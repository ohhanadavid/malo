"""Integration tests: end-to-end sanity checks on the real data (Phase 5,
Task 5.2).

Unlike the rest of the suite (hand-built synthetic DataFrames, see
docs/testing.md), this module deliberately runs the full pipeline against
the actual ``Data/*.xlsx`` files via the real loaders -- these are small
files (a few seconds to load), which is acceptable for one integration
module. It checks:

1. Row-count reconciliation on ``TblAllTest``.
2. A regression check of ``reporting.compute_national_norm``'s exact
   already-verified real-data result (see ``docs/project-plan.md`` Task
   3.3).
3. A regression check of the school special-needs report's exact
   already-verified real-data result (see ``docs/project-plan.md`` Task
   4.2).
4. An independent spot-check: cntvalid and pop_id/delcodeb for a handful of
   real students at one real school, re-derived by hand in this file
   straight from the task-brief rules in CLAUDE.md -- not by calling
   ``transforms.compute_cntvalid`` or ``pop_id.classify_pop_id`` -- then
   compared against the pipeline's actual output for those same students.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.delcodeb import add_delcodeb
from src.loaders import load_all_data, load_schools, load_sppop, load_translation_tables
from src.pop_id import classify_pop_id
from src.reporting import (
    aggregate_school_special_needs,
    compute_national_norm,
    school_special_needs_report,
)
from src.tbl_all_test import build_tbl_all_test
from src.transforms import compute_cntvalid

# The 98/99 non-response sentinels, per CLAUDE.md step 1 -- duplicated here
# (not imported from src.transforms) since section 4 below must re-derive
# cntvalid independently of transforms.compute_cntvalid.
_NON_RESPONSE = (98, 99)


@pytest.fixture(scope="module")
def pipeline() -> dict:
    """Run the full pipeline once against the real Data/*.xlsx files."""
    all_data = load_all_data()
    schools = load_schools()
    sppop = load_sppop()
    translation_tables = load_translation_tables()

    all_data_cv = compute_cntvalid(all_data)
    sppop_classified = classify_pop_id(sppop, all_data_cv)
    tbl_all_test = build_tbl_all_test(all_data_cv, schools)
    tbl_all_test = add_delcodeb(tbl_all_test, sppop_classified)

    return {
        "all_data": all_data,
        "sppop": sppop,
        "translation_tables": translation_tables,
        "tbl_all_test": tbl_all_test,
    }


# ---------------------------------------------------------------------------
# 1. Row-count reconciliation
# ---------------------------------------------------------------------------


def test_tbl_all_test_row_count_matches_sum_of_form_sheets(pipeline: dict) -> None:
    all_data = pipeline["all_data"]
    sum_of_form_sheets = sum(
        len(df) for name, df in all_data.items() if name != "varname"
    )
    assert sum_of_form_sheets == 42890
    assert len(pipeline["tbl_all_test"]) == 42890


def test_taz_new_is_fully_unique(pipeline: dict) -> None:
    assert pipeline["tbl_all_test"]["taz_new"].is_unique


def test_no_nulls_in_joined_school_attributes(pipeline: dict) -> None:
    tbl_all_test = pipeline["tbl_all_test"]
    for col in ("migzar_id", "pikuach_id", "machoz_divuach"):
        assert tbl_all_test[col].isna().sum() == 0, f"unexpected nulls in {col}"


# ---------------------------------------------------------------------------
# 2. National-norm count regression check
# ---------------------------------------------------------------------------


def test_national_norm_matches_verified_real_data_result(pipeline: dict) -> None:
    result = compute_national_norm(
        pipeline["tbl_all_test"], pipeline["translation_tables"]
    )
    assert result == {
        "national_norm_count": 33800,
        "excluded_haredi": 4671,
        "excluded_mizrach_yerushalayim": 2305,
        "excluded_new_immigrant": 205,
        "excluded_blank_booklet": 303,
        "excluded_form_mismatch": 1894,
        "total_rows": 42890,
    }


# ---------------------------------------------------------------------------
# 3. School-report regression check
# ---------------------------------------------------------------------------


def test_school_special_needs_report_matches_verified_real_data_result(
    pipeline: dict,
) -> None:
    school_stats = aggregate_school_special_needs(pipeline["tbl_all_test"])
    assert len(school_stats) == 1089

    report = school_special_needs_report(school_stats)
    assert len(report) == 72

    top_school = report[report["semel_new"] == 1474]
    assert len(top_school) == 1
    row = top_school.iloc[0]
    assert row["regular_count"] == 18
    assert row["special_needs_proportion"] == pytest.approx(0.454545, abs=1e-6)


# ---------------------------------------------------------------------------
# 4. Independent spot-check on a real slice -- school 3867
# ---------------------------------------------------------------------------
#
# Found by exploring the real data for a school small enough to check by
# hand in full while still covering both a blank-booklet student and a
# classified-special-needs student:
#
#   - sheet "472": taz_new 10258-10262 (5 students)
#   - sheet "506": taz_new 24893-24894 (2 students)
#
# Of these 7, only taz_new 24893 has a row in the real sppop.xlsx
# (Kvutza_musheret=6, status_meushar=400); the other 6 are entirely absent
# from sppop.xlsx. taz_new 10258 answered every Ind1==1 question with 98/99
# -- a genuine blank booklet in the real data.
#
# Everything below is computed fresh from the raw Data/all_data.xlsx /
# Data/sppop.xlsx rows and the task-brief rules in CLAUDE.md, without
# calling transforms.compute_cntvalid or pop_id.classify_pop_id, so this is
# an independent check rather than the pipeline being compared to itself.

_TAZ_472 = [10258, 10259, 10260, 10261, 10262]
_TAZ_506 = [24893, 24894]


def _hand_compute_cntvalid(
    form_df: pd.DataFrame, varname: pd.DataFrame, code: int, taz_list: list[int]
) -> dict[int, int]:
    """Independently recompute cntvalid for specific students on one form.

    Re-derives CLAUDE.md step 1 ("cntvalid = count of answered questions,
    counting only questions whose varname entry has Ind1==1; 98/99 don't
    count") from scratch -- this is intentionally a separate piece of code
    from transforms.compute_cntvalid, not a call to it.
    """
    ind1_columns = varname.loc[
        (varname["code_shelon_omer"] == code) & (varname["Ind1"] == 1), "VarName"
    ].tolist()
    ind1_columns = [c for c in ind1_columns if c in form_df.columns]

    cntvalid_by_taz = {}
    for taz in taz_list:
        row = form_df.loc[form_df["taz_new"] == taz, ind1_columns].iloc[0]
        cntvalid_by_taz[taz] = sum(1 for value in row if value not in _NON_RESPONSE)
    return cntvalid_by_taz


def test_spot_check_cntvalid_matches_hand_recomputation(pipeline: dict) -> None:
    varname = pipeline["all_data"]["varname"]

    expected = _hand_compute_cntvalid(pipeline["all_data"]["472"], varname, 472, _TAZ_472)
    expected.update(
        _hand_compute_cntvalid(pipeline["all_data"]["506"], varname, 506, _TAZ_506)
    )

    tbl_all_test = pipeline["tbl_all_test"]
    for taz, expected_cntvalid in expected.items():
        actual = tbl_all_test.loc[tbl_all_test["taz_new"] == taz, "cntvalid"].iloc[0]
        assert actual == expected_cntvalid, f"taz_new={taz}"

    # This slice must actually cover a blank booklet (all Ind1==1 answers
    # are 98/99 -> cntvalid == 0) and a real test-taker, per the task.
    assert expected[10258] == 0
    assert expected[24893] > 0


def test_spot_check_blank_booklet_forces_delcodeb_5(pipeline: dict) -> None:
    sppop = pipeline["sppop"]
    tbl_all_test = pipeline["tbl_all_test"]

    # taz_new 10258 has no row at all in the raw special-needs file -- a
    # naive implementation might default an sppop-absent student straight
    # to "regular" (0) without checking cntvalid first.
    assert sppop.loc[sppop["taz_new"] == 10258].empty

    row = tbl_all_test.loc[tbl_all_test["taz_new"] == 10258].iloc[0]
    assert row["cntvalid"] == 0
    # CLAUDE.md step 4: delcodeb mirrors pop_id, "except blank booklets
    # always get 5" -- overriding the sppop-absent default.
    assert row["delcodeb"] == 5
    assert row["delcodeb_n"] == 5


def test_spot_check_group6_status400_classified_as_combined(pipeline: dict) -> None:
    sppop = pipeline["sppop"]
    tbl_all_test = pipeline["tbl_all_test"]

    raw = sppop.loc[sppop["taz_new"] == 24893].iloc[0]
    assert raw["semel_new"] == 3867
    assert raw["Kvutza_musheret"] == 6
    assert raw["status_meushar"] == 400

    # CLAUDE.md step 2: "groups 5/6 + status 400 (default) -> combined/
    # integrated (משולב)", coded as pop_id = pop_id_n = 6. Applied by hand
    # here for this one real row, independently of pop_id.classify_pop_id.
    expected_pop_id = 6

    row = tbl_all_test.loc[tbl_all_test["taz_new"] == 24893].iloc[0]
    assert row["cntvalid"] > 0  # actually tested
    assert row["delcodeb"] == expected_pop_id
    assert row["delcodeb_n"] == expected_pop_id


def test_spot_check_students_absent_from_sppop_are_regular(pipeline: dict) -> None:
    sppop = pipeline["sppop"]
    tbl_all_test = pipeline["tbl_all_test"]

    # The other 6 students at this school: non-blank, no row in sppop.xlsx
    # at all -- CLAUDE.md step 4: "students absent from the special-needs
    # file are treated as regular".
    for taz in (10259, 10260, 10261, 10262, 24894):
        assert sppop.loc[sppop["taz_new"] == taz].empty, f"taz_new={taz}"
        row = tbl_all_test.loc[tbl_all_test["taz_new"] == taz].iloc[0]
        assert row["cntvalid"] > 0
        assert row["delcodeb"] == 0
        assert row["delcodeb_n"] == 0

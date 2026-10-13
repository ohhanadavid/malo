"""Unit tests for ``src.pop_id.classify_pop_id`` (Phase 5, Task 5.1).

Covers every branch of the group/status decision table documented in
``CLAUDE.md`` ("The task", step 2) and ``src/pop_id.py``'s docstring /
``GROUP_DEFAULT_POP_ID``.
"""

from __future__ import annotations

import math

import pandas as pd

from src.pop_id import classify_pop_id

SEMEL = 100  # single shared school code for every synthetic row -- the
# decision table doesn't depend on school identity, only on
# (taz_new, semel_new) matching between sppop and the tested lookup.


def _make_sppop() -> pd.DataFrame:
    # (taz_new, Kvutza_musheret, status_meushar) for every branch of the
    # decision table. pop_id/pop_id_n/del start as NaN, matching the real
    # (currently-unclassified) sppop.xlsx.
    rows = [
        # taz, group, status
        (1, 1, 200),   # group1+status200 -> new immigrant
        (2, 1, 400),   # group1+status400 -> veteran immigrant
        (3, 2, 200),   # group2+status200 -> new immigrant
        (4, 2, 400),   # group2+status400 -> veteran immigrant
        (5, 5, 400),   # group5+status400 -> combined
        (6, 6, 400),   # group6+status400 -> combined
        (7, 5, 200),   # group5+status200, tested -> reclassified combined
        (8, 5, 200),   # group5+status200, untested -> del=2
        (9, 6, 300),   # group6+status300, tested -> reclassified combined
        (10, 1, 100),  # status100+group1 -> school 0, national group-default (4)
        (11, 5, 100),  # status100+group5 -> school 0, national group-default (6)
        (12, 2, 600),  # status600, tested, group2 -> group default (7)
        (13, 1, 600),  # status600, untested -> del=1
        (14, 2, 700),  # status700 -> regular (0/0) regardless of group
        (15, 0, 300),  # group0+status300 -> known-unhandled gap
    ]
    return pd.DataFrame(
        {
            "semel_new": [SEMEL] * len(rows),
            "taz_new": [r[0] for r in rows],
            "Kvutza_musheret": [r[1] for r in rows],
            "status_meushar": [r[2] for r in rows],
            "pop_id": [float("nan")] * len(rows),
            "pop_id_n": [float("nan")] * len(rows),
            "del": [float("nan")] * len(rows),
        }
    )


def _make_all_data_with_cntvalid() -> dict[str, pd.DataFrame]:
    """Tested lookup for the rows whose branch depends on cntvalid > 0.

    taz=7 and taz=9 are "tested" (cntvalid > 0). taz=12 is "tested" too
    (status 600 branch). taz=13 is present but cntvalid == 0, i.e.
    explicitly untested (not merely absent). taz=8 is deliberately absent
    from both sheets entirely -- also untested, via the no-match path.
    """
    form_a = pd.DataFrame(
        {
            "taz_new": [7, 9],
            "semel_new": [SEMEL, SEMEL],
            "cntvalid": [3, 5],
        }
    )
    form_b = pd.DataFrame(
        {
            "taz_new": [12, 13],
            "semel_new": [SEMEL, SEMEL],
            "cntvalid": [2, 0],
        }
    )
    varname = pd.DataFrame(
        {"code_shelon_omer": [], "VarName": [], "Ind1": []}
    )
    return {"472": form_a, "506": form_b, "varname": varname}


def _row(result: pd.DataFrame, taz: int) -> pd.Series:
    matches = result.loc[result["taz_new"] == taz]
    assert len(matches) == 1
    return matches.iloc[0]


def _assert_tuple(row: pd.Series, pop_id, pop_id_n, del_, needs_review: bool):
    def _check(actual, expected):
        if expected is None:
            assert math.isnan(actual)
        else:
            assert actual == expected

    _check(row["pop_id"], pop_id)
    _check(row["pop_id_n"], pop_id_n)
    _check(row["del"], del_)
    assert bool(row["needs_review"]) is needs_review


def test_group1_status200_new_immigrant():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 1), 4, 4, None, False)


def test_group1_status400_veteran_immigrant():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 2), 7, 7, None, False)


def test_group2_status200_new_immigrant():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 3), 4, 4, None, False)


def test_group2_status400_veteran_immigrant():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 4), 7, 7, None, False)


def test_group5_status400_combined():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 5), 6, 6, None, False)


def test_group6_status400_combined():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 6), 6, 6, None, False)


def test_group5_status200_tested_reclassified_combined():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 7), 6, 6, None, False)


def test_group5_status200_untested_del2():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 8), None, None, 2, False)


def test_group6_status300_tested_reclassified_combined():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 9), 6, 6, None, False)


def test_status100_group1_school_regular_national_group_default():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 10), 0, 4, None, False)


def test_status100_group5_school_regular_national_group_default():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 11), 0, 6, None, False)


def test_status600_tested_group2_group_default():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 12), 7, 7, None, False)


def test_status600_untested_del1():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 13), None, None, 1, False)


def test_status700_regular_regardless_of_group():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 14), 0, 0, None, False)


def test_group0_status300_unhandled_gap_flagged_needs_review():
    result = classify_pop_id(_make_sppop(), _make_all_data_with_cntvalid())
    _assert_tuple(_row(result, 15), None, None, None, True)


def test_sppop_input_not_mutated():
    sppop = _make_sppop()
    sppop_before = sppop.copy()

    classify_pop_id(sppop, _make_all_data_with_cntvalid())

    pd.testing.assert_frame_equal(sppop, sppop_before)
    assert "needs_review" not in sppop.columns

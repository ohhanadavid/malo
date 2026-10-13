"""Unit tests for ``src.delcodeb.add_delcodeb`` (Phase 5, Task 5.1)."""

from __future__ import annotations

import math

import pandas as pd

from src.delcodeb import add_delcodeb

SEMEL = 100


def _make_tbl_all_test() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "taz_new": [1, 2, 3, 4],
            "semel_new": [SEMEL] * 4,
            # taz=1: blank booklet, despite also having a defined pop_id
            #        in sppop_classified below -- the override must win.
            # taz=2: non-blank, entirely absent from sppop_classified.
            # taz=3: non-blank, matched with a defined pop_id/pop_id_n.
            # taz=4: non-blank, matched but pop_id/pop_id_n are NaN
            #        (simulated needs_review row) -- must stay NaN, not
            #        default to 0.
            "cntvalid": [0, 5, 7, 3],
        }
    )


def _make_sppop_classified() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "taz_new": [1, 3, 4],
            "semel_new": [SEMEL, SEMEL, SEMEL],
            "pop_id": [6, 4, float("nan")],
            "pop_id_n": [6, 4, float("nan")],
            "needs_review": [False, False, True],
        }
    )


def _row(result: pd.DataFrame, taz: int) -> pd.Series:
    matches = result.loc[result["taz_new"] == taz]
    assert len(matches) == 1
    return matches.iloc[0]


def test_blank_booklet_forces_5_even_with_defined_pop_id():
    result = add_delcodeb(_make_tbl_all_test(), _make_sppop_classified())
    row = _row(result, 1)
    assert row["delcodeb"] == 5
    assert row["delcodeb_n"] == 5


def test_nonblank_absent_from_sppop_defaults_to_regular_0():
    result = add_delcodeb(_make_tbl_all_test(), _make_sppop_classified())
    row = _row(result, 2)
    assert row["delcodeb"] == 0
    assert row["delcodeb_n"] == 0


def test_nonblank_matched_carries_over_defined_pop_id():
    result = add_delcodeb(_make_tbl_all_test(), _make_sppop_classified())
    row = _row(result, 3)
    assert row["delcodeb"] == 4
    assert row["delcodeb_n"] == 4


def test_nonblank_matched_needs_review_nan_stays_nan_not_zero():
    """Regression test for the exact bug add_delcodeb was built to avoid:
    a student *present* in sppop_classified with an undefined (NaN)
    pop_id must not be confused with being *absent* from it -- the
    absent case defaults to 0, but this case must stay NaN.
    """
    result = add_delcodeb(_make_tbl_all_test(), _make_sppop_classified())
    row = _row(result, 4)
    assert math.isnan(row["delcodeb"])
    assert math.isnan(row["delcodeb_n"])


def test_inputs_not_mutated():
    tbl_all_test = _make_tbl_all_test()
    sppop_classified = _make_sppop_classified()
    tbl_before = tbl_all_test.copy()
    sppop_before = sppop_classified.copy()

    add_delcodeb(tbl_all_test, sppop_classified)

    pd.testing.assert_frame_equal(tbl_all_test, tbl_before)
    pd.testing.assert_frame_equal(sppop_classified, sppop_before)
    assert "delcodeb" not in tbl_all_test.columns
    assert "delcodeb_n" not in tbl_all_test.columns


def test_existing_columns_preserved_and_new_columns_appended():
    tbl_all_test = _make_tbl_all_test()
    result = add_delcodeb(tbl_all_test, _make_sppop_classified())

    for col in tbl_all_test.columns:
        assert col in result.columns
    assert list(result.columns)[: len(tbl_all_test.columns)] == list(
        tbl_all_test.columns
    )
    assert "delcodeb" in result.columns
    assert "delcodeb_n" in result.columns

"""Unit tests for ``src.transforms.compute_cntvalid`` (Phase 5, Task 5.1)."""

from __future__ import annotations

import pandas as pd

from src.transforms import compute_cntvalid


def _make_all_data() -> dict[str, pd.DataFrame]:
    """Small synthetic all_data dict: one fake form sheet + varname.

    Form "999" has four answer columns: Q1 (Ind1=1), Q2 (Ind1=1), Q3
    (Ind1=0 -- must be ignored even though it has countable-looking
    values), and Q0_demo (Ind1=0, background question).
    """
    form = pd.DataFrame(
        {
            "taz_new": [1, 2, 3],
            "semel_new": [10, 10, 20],
            # Q1: all valid answers.
            "Q1": [1, 2, 3],
            # Q2: row0 answered, row1 is 98 (non-response), row2 is 99.
            "Q2": [5, 98, 99],
            # Q3: Ind1=0 -- must never count, even though these look valid.
            "Q3": [1, 1, 1],
            # Q0_demo: Ind1=0 background question.
            "Q0_demo": [98, 99, 1],
        }
    )

    varname = pd.DataFrame(
        {
            "code_shelon_omer": [999, 999, 999, 999],
            "VarName": ["Q1", "Q2", "Q3", "Q0_demo"],
            "Ind1": [1, 1, 0, 0],
        }
    )

    return {"999": form, "varname": varname}


def test_cntvalid_counts_only_ind1_columns_excluding_98_99():
    all_data = _make_all_data()

    result = compute_cntvalid(all_data)

    # Row 0: Q1=1 (valid), Q2=5 (valid) -> 2. Q3/Q0_demo ignored (Ind1=0).
    # Row 1: Q1=2 (valid), Q2=98 (non-response, excluded) -> 1.
    # Row 2: Q1=3 (valid), Q2=99 (non-response, excluded) -> 1.
    expected = [2, 1, 1]

    assert result["999"]["cntvalid"].tolist() == expected


def test_ind1_zero_columns_ignored_even_if_otherwise_countable():
    all_data = _make_all_data()
    result = compute_cntvalid(all_data)

    # Q3 is all valid-looking (1,1,1) with Ind1=0 -- if it leaked in,
    # every row's cntvalid would be 1 higher than expected.
    assert result["999"]["cntvalid"].tolist() == [2, 1, 1]


def test_varname_passed_through_unchanged():
    all_data = _make_all_data()
    result = compute_cntvalid(all_data)

    assert result["varname"] is all_data["varname"]
    pd.testing.assert_frame_equal(result["varname"], all_data["varname"])


def test_input_not_mutated():
    all_data = _make_all_data()

    form_before = all_data["999"].copy()
    varname_before = all_data["varname"].copy()

    compute_cntvalid(all_data)

    # The input dict's DataFrames are unchanged (no cntvalid column added,
    # no value changed).
    pd.testing.assert_frame_equal(all_data["999"], form_before)
    pd.testing.assert_frame_equal(all_data["varname"], varname_before)
    assert "cntvalid" not in all_data["999"].columns


def test_returned_form_sheet_is_a_different_object_with_cntvalid_added():
    all_data = _make_all_data()
    result = compute_cntvalid(all_data)

    assert result["999"] is not all_data["999"]
    assert "cntvalid" in result["999"].columns
    # All original columns preserved.
    for col in all_data["999"].columns:
        assert col in result["999"].columns


def test_multiple_form_sheets_each_get_their_own_varname_matched_columns():
    # A second form sheet ("888") with its own distinct Ind1=1 columns,
    # to confirm the loop doesn't cross-apply one sheet's valid columns to
    # another.
    form_999 = pd.DataFrame({"taz_new": [1], "semel_new": [10], "Q1": [1], "Q2": [98]})
    form_888 = pd.DataFrame({"taz_new": [2], "semel_new": [11], "QA": [5], "QB": [99]})

    varname = pd.DataFrame(
        {
            "code_shelon_omer": [999, 999, 888, 888],
            "VarName": ["Q1", "Q2", "QA", "QB"],
            "Ind1": [1, 1, 1, 1],
        }
    )

    all_data = {"999": form_999, "888": form_888, "varname": varname}
    result = compute_cntvalid(all_data)

    # 999: Q1=1 valid, Q2=98 excluded -> 1
    assert result["999"]["cntvalid"].tolist() == [1]
    # 888: QA=5 valid, QB=99 excluded -> 1
    assert result["888"]["cntvalid"].tolist() == [1]

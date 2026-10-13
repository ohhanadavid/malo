"""Core record-level transformations (Phase 2) applied on top of ``loaders.py``'s output."""

from __future__ import annotations

import pandas as pd

_NON_RESPONSE_CODES = (98, 99)


def compute_cntvalid(all_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Add a ``cntvalid`` column to every form sheet in ``all_data``.

    ``all_data`` is the dict returned by ``loaders.load_all_data()``: one
    entry per form sheet (``472``, ``506``, ``541``, ``542``, ``653``,
    ``654``, or any future form sheet) plus a ``varname`` sheet with columns
    ``code_shelon_omer``, ``VarName``, ``Ind1``.

    For every key except ``"varname"``, ``cntvalid`` is computed as the
    per-row count of that form's ``Ind1 == 1`` columns (looked up from
    ``varname`` by matching ``code_shelon_omer == int(sheet_name)``) whose
    value is neither ``98`` nor ``99``. Those sentinel values are only
    excluded from this count -- they are left untouched everywhere else
    (recoding them is out of scope here; see ``docs/project-plan.md``
    Phase 7).

    Returns a new dict with the same keys as ``all_data``: every form sheet
    is a copy of the input DataFrame with ``cntvalid`` added, and
    ``"varname"`` is passed through unchanged (same object, not mutated).
    Pure function -- no printing, no file I/O, no mutation of ``all_data``
    or its DataFrames.
    """
    varname = all_data["varname"]
    result: dict[str, pd.DataFrame] = {"varname": varname}

    for sheet_name, df in all_data.items():
        if sheet_name == "varname":
            continue

        valid_columns = varname.loc[
            (varname["code_shelon_omer"] == int(sheet_name)) & (varname["Ind1"] == 1),
            "VarName",
        ].tolist()

        df = df.copy()
        present_columns = [col for col in valid_columns if col in df.columns]
        is_answered = ~df[present_columns].isin(_NON_RESPONSE_CODES)
        df["cntvalid"] = is_answered.sum(axis=1).astype(int)

        result[sheet_name] = df

    return result

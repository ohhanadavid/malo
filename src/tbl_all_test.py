"""Build ``TblAllTest`` (Phase 2, Task 2.3), combining every student from
every form sheet with school attributes joined in from ``schools.xlsx``.
"""

from __future__ import annotations

import pandas as pd

_COMBINED_COLUMNS = [
    "taz_new",
    "semel_new",
    "MAKBILA_tiyuv",
    "code_shelon_rama",
    "SIDURY_SHELON",
    "cntvalid",
]

_OUTPUT_COLUMNS = [
    "taz_new",
    "semel_new",
    "MAKBILA_tiyuv",
    "code_shelon_rama",
    "SIDURY_SHELON",
    "cntvalid",
    "migzar_id",
    "pikuach_id",
    "machoz_divuach",
]


def build_tbl_all_test(
    all_data_with_cntvalid: dict[str, pd.DataFrame], schools: pd.DataFrame
) -> pd.DataFrame:
    """Build ``TblAllTest``: one row per student across all form sheets.

    ``all_data_with_cntvalid`` is ``transforms.compute_cntvalid()``'s output
    (the six form sheets plus ``varname``, each form sheet carrying
    ``cntvalid``). ``schools`` is ``loaders.load_schools()``'s output.

    Combines ``taz_new``, ``semel_new``, ``MAKBILA_tiyuv``,
    ``code_shelon_rama``, ``SIDURY_SHELON`` and ``cntvalid`` from every form
    sheet (every key except ``"varname"``) into one DataFrame, then groups
    by ``taz_new`` so there is exactly one row per student: ``cntvalid`` is
    summed across the group and the other columns take the first value in
    the group. In the current data every ``taz_new`` already appears in
    exactly one row total across all six sheets, so this groupby+sum is a
    no-op today -- it is implemented anyway as a deliberate defensive
    choice in case duplicate/retake data appears later (see
    ``docs/project-plan.md``'s Task 2.3 note).

    Finally left-joins ``migzar_id``, ``pikuach_id`` and ``machoz_divuach``
    in from ``schools`` via ``semel_new``.

    Returns a new DataFrame with exactly these columns: ``taz_new``,
    ``semel_new``, ``MAKBILA_tiyuv``, ``code_shelon_rama``,
    ``SIDURY_SHELON``, ``cntvalid``, ``migzar_id``, ``pikuach_id``,
    ``machoz_divuach``. Pure function -- no printing, no file I/O, no
    mutation of ``all_data_with_cntvalid``, ``schools``, or any of their
    DataFrames.
    """
    form_sheets = [
        df[_COMBINED_COLUMNS]
        for sheet_name, df in all_data_with_cntvalid.items()
        if sheet_name != "varname"
    ]
    combined = pd.concat(form_sheets, ignore_index=True)

    grouped = combined.groupby("taz_new", as_index=False).agg(
        semel_new=("semel_new", "first"),
        MAKBILA_tiyuv=("MAKBILA_tiyuv", "first"),
        code_shelon_rama=("code_shelon_rama", "first"),
        SIDURY_SHELON=("SIDURY_SHELON", "first"),
        cntvalid=("cntvalid", "sum"),
    )

    tbl_all_test = grouped.merge(
        schools[["semel_new", "migzar_id", "pikuach_id", "machoz_divuach"]],
        on="semel_new",
        how="left",
    )

    return tbl_all_test[_OUTPUT_COLUMNS]

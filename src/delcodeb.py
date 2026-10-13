"""Add ``delcodeb``/``delcodeb_n`` to ``TblAllTest`` (Phase 2, Task 2.4).

Mirrors ``pop_id``/``pop_id_n`` from ``pop_id.classify_pop_id()``'s output
onto ``tbl_all_test.build_tbl_all_test()``'s output, except blank booklets
(``cntvalid == 0``) always get ``5`` regardless of ``pop_id``, and students
absent from ``sppop_classified`` entirely are treated as regular (``0``).
Pure function: no printing, no file I/O, no mutation of its inputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_delcodeb(
    tbl_all_test: pd.DataFrame, sppop_classified: pd.DataFrame
) -> pd.DataFrame:
    """Add ``delcodeb``/``delcodeb_n`` columns to ``tbl_all_test``.

    ``tbl_all_test`` is ``tbl_all_test.build_tbl_all_test()``'s output (one
    row per student, has a ``cntvalid`` column). ``sppop_classified`` is
    ``pop_id.classify_pop_id()``'s output (has ``pop_id``, ``pop_id_n`` and
    ``needs_review`` columns; confirmed no duplicate ``(taz_new,
    semel_new)`` pairs in it).

    ``delcodeb`` takes the same value as ``pop_id``, and ``delcodeb_n`` the
    same value as ``pop_id_n``, matched on ``(taz_new, semel_new)``, with
    two exceptions evaluated in priority order:

    1. A blank booklet (``cntvalid == 0``) always gets ``delcodeb =
       delcodeb_n = 5``, overriding everything else -- even a student who
       also has a defined ``pop_id``.
    2. A student with no ``(taz_new, semel_new)`` match at all in
       ``sppop_classified`` (i.e. entirely absent from the special-needs
       file) is treated as regular: ``delcodeb = delcodeb_n = 0``.

    Otherwise ``delcodeb``/``delcodeb_n`` carry over ``pop_id``/``pop_id_n``
    as-is, including staying ``NaN`` for the documented ``needs_review`` gap
    (a student *present* in ``sppop_classified`` with an undefined
    ``pop_id`` is not the same as being *absent* from it, and must not
    default to ``0``). The merge's ``indicator`` flag (``"both"`` vs.
    ``"left_only"``) is what distinguishes these two cases correctly --
    checking ``pop_id.isna()`` alone would not.

    Returns a copy of ``tbl_all_test`` with ``delcodeb`` and ``delcodeb_n``
    appended (existing columns are kept, untouched, in their original
    order). Does not mutate ``tbl_all_test`` or ``sppop_classified``.
    """
    merged = tbl_all_test.merge(
        sppop_classified[["taz_new", "semel_new", "pop_id", "pop_id_n"]],
        on=["taz_new", "semel_new"],
        how="left",
        indicator=True,
    )

    is_blank_booklet = merged["cntvalid"] == 0
    is_absent = merged["_merge"] == "left_only"
    is_matched = ~is_blank_booklet & ~is_absent
    condlist = [is_blank_booklet, is_absent, is_matched]

    delcodeb = np.select(condlist, [5, 0, merged["pop_id"]], default=np.nan)
    delcodeb_n = np.select(condlist, [5, 0, merged["pop_id_n"]], default=np.nan)

    result = tbl_all_test.copy()
    result["delcodeb"] = delcodeb
    result["delcodeb_n"] = delcodeb_n

    return result

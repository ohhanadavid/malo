"""``sppop`` special-needs classification (Phase 2, Task 2.2).

Implements the ``pop_id``/``pop_id_n``/``del`` decision table from the task
brief on top of ``loaders.load_sppop()``'s output and
``transforms.compute_cntvalid()``'s output. Pure function: no printing, no
file I/O, no mutation of its inputs.
"""

from __future__ import annotations

import pandas as pd

# pop_id a group gets when classified by its "default" status (see task
# brief's coding table: regular=0, new immigrant=4, combined=6, veteran
# immigrant=7).
GROUP_DEFAULT_POP_ID: dict[int, int] = {1: 4, 2: 7, 5: 6, 6: 6}


def _build_tested_lookup(all_data_with_cntvalid: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Concatenate ``cntvalid``/``taz_new``/``semel_new`` from every form sheet.

    Excludes the ``varname`` entry. ``taz_new`` is confirmed globally unique
    across all 6 form sheets combined (zero duplicates, zero cross-sheet
    overlap), so this lookup has at most one row per ``(taz_new,
    semel_new)`` pair.
    """
    frames = [
        df[["cntvalid", "taz_new", "semel_new"]]
        for name, df in all_data_with_cntvalid.items()
        if name != "varname"
    ]
    return pd.concat(frames, ignore_index=True)


def _classify_row(row: pd.Series) -> tuple[float, float, float, bool]:
    """Classify one ``sppop`` row per the task brief's decision table.

    Returns ``(pop_id, pop_id_n, del, needs_review)``. Status 100/600/700
    checks are evaluated before the group-based checks, since they apply
    regardless of group.
    """
    group = row["Kvutza_musheret"]
    status = row["status_meushar"]
    tested = row["_tested"]

    pop_id: float = float("nan")
    pop_id_n: float = float("nan")
    del_flag: float = float("nan")
    needs_review = False

    if status == 700:
        pop_id = 0
        pop_id_n = 0
    elif status == 100:
        pop_id = 0  # regular at the school level
        if group in GROUP_DEFAULT_POP_ID:
            pop_id_n = GROUP_DEFAULT_POP_ID[group]  # national level: group default
        else:
            needs_review = True
    elif status == 600:
        if tested:
            if group in GROUP_DEFAULT_POP_ID:
                pop_id = pop_id_n = GROUP_DEFAULT_POP_ID[group]
            else:
                needs_review = True
        else:
            del_flag = 1  # removed from the special-needs file; never tested
    elif group == 1:
        if status == 200:
            pop_id = pop_id_n = 4
        elif status == 400:
            pop_id = pop_id_n = 7
        else:
            needs_review = True
    elif group == 2:
        if status == 400:
            pop_id = pop_id_n = 7
        elif status == 200:
            pop_id = pop_id_n = 4
        else:
            needs_review = True
    elif group in (5, 6):
        if status == 400:
            pop_id = pop_id_n = 6
        elif status in (200, 300):
            if tested:
                pop_id = pop_id_n = 6  # reclassified as status 400
            else:
                del_flag = 2
        else:
            needs_review = True
    else:
        # e.g. group 0 with status 300 -- a known, documented gap (CLAUDE.md
        # "Data quirks"). Do not guess a classification; flag for review.
        needs_review = True

    return pop_id, pop_id_n, del_flag, needs_review


def classify_pop_id(
    sppop: pd.DataFrame, all_data_with_cntvalid: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Classify every ``sppop`` row into ``pop_id``/``pop_id_n``/``del``.

    ``sppop`` is ``loaders.load_sppop()``'s output (columns include
    ``semel_new``, ``taz_new``, ``Kvutza_musheret`` [group],
    ``status_meushar`` [status], and currently-all-``NaN`` ``pop_id``,
    ``pop_id_n``, ``del``). ``all_data_with_cntvalid`` is
    ``transforms.compute_cntvalid()``'s output (dict of the 6 form sheets +
    ``varname``, each form sheet carrying ``cntvalid``).

    A student is "tested" iff a ``(taz_new, semel_new)`` match is found in
    ``all_data_with_cntvalid`` (across all form sheets) *and* that match's
    ``cntvalid > 0``; no match at all (e.g. special-needs-registered
    students absent from ``all_data.xlsx``) counts as not tested.

    Returns a copy of ``sppop`` with ``pop_id``, ``pop_id_n``, ``del``
    filled in per the task brief's decision table (left as ``NaN`` wherever
    the table doesn't define a value -- no invented fallback), plus a new
    boolean ``needs_review`` column, ``True`` only for genuinely-unhandled
    combos (not for the ``del=1``/``del=2`` rows, which already carry their
    own explicit marker). Does not mutate ``sppop`` or
    ``all_data_with_cntvalid``.
    """
    tested_lookup = _build_tested_lookup(all_data_with_cntvalid)

    merged = sppop.merge(
        tested_lookup,
        on=["taz_new", "semel_new"],
        how="left",
    )
    merged["_tested"] = merged["cntvalid"].fillna(0) > 0

    classified = merged.apply(_classify_row, axis=1, result_type="expand")
    classified.columns = ["pop_id", "pop_id_n", "del", "needs_review"]

    result = sppop.copy()
    result["pop_id"] = classified["pop_id"]
    result["pop_id_n"] = classified["pop_id_n"]
    result["del"] = classified["del"]
    result["needs_review"] = classified["needs_review"].astype(bool)

    return result

"""National-norm test-taker count (Phase 3, Tasks 3.1/3.2/3.3).

Computes the national-norm test-taker count from
``tbl_all_test.build_tbl_all_test()``'s output (with ``delcodeb``/
``delcodeb_n`` already added by ``delcodeb.add_delcodeb()``), per the task
brief's step 5 exclusion rules. Pure function: no printing, no file I/O, no
mutation of its inputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_national_norm(
    tbl_all_test: pd.DataFrame, translation_tables: dict[str, pd.DataFrame]
) -> dict:
    """Compute the national-norm test-taker count and its exclusion breakdown.

    ``tbl_all_test`` is ``tbl_all_test.build_tbl_all_test()``'s output, with
    ``delcodeb``/``delcodeb_n`` already added by ``delcodeb.add_delcodeb()``
    (so it has ``migzar_id``, ``pikuach_id``, ``machoz_divuach``,
    ``cntvalid``, ``code_shelon_rama``, ``delcodeb_n``). ``translation_tables``
    is ``loaders.load_translation_tables()``'s output (dict with a
    ``"migzar"`` key -- a DataFrame with ``migzar``/``desc``/``language``
    columns, confirmed to hold plain Python ``int``s despite the
    object-looking column dtype).

    A row is excluded from the national norm if any of these 5 conditions
    holds:

    1. Haredi: ``pikuach_id == 3``.
    2. מז"י (East Jerusalem, Arab sector): ``machoz_divuach == 13 AND
       migzar_id == 2`` -- specifically the Arab sector (``migzar_id==2``),
       not the broader Arabic-language group (which also includes Druze,
       ``migzar_id==4``, and Bedouin, ``migzar_id==5``).
    3. New immigrant at the **national** level: ``delcodeb_n == 4``
       (deliberately ``delcodeb_n``, not ``delcodeb``, since this is a
       national-norm calculation).
    4. Blank booklet: ``cntvalid == 0``.
    5. Form/population mismatch: a student's own population bucket is ``3``
       if Haredi (condition 1), else their ``migzar_id``'s ``language``
       value (``1``=Hebrew, ``2``=Arabic) looked up from
       ``translation_tables["migzar"]``. The form's target-population
       bucket is the 3rd digit (counting from the left) of
       ``code_shelon_rama`` (a 5-digit int, e.g. ``26112`` -> digit ``1``).
       Mismatch is ``student_bucket != form_bucket``.

    Returns a dict:

    - ``national_norm_count``: count of rows where **none** of the 5
      conditions hold -- the actual deliverable.
    - ``excluded_haredi``, ``excluded_mizrach_yerushalayim``,
      ``excluded_new_immigrant``, ``excluded_blank_booklet``,
      ``excluded_form_mismatch``: diagnostic counts of each condition
      evaluated **alone**. These 5 are **not** mutually exclusive -- a row
      can match more than one condition -- so they do not partition
      ``total_rows``; don't assume they sum to
      ``total_rows - national_norm_count``.
    - ``total_rows``: ``len(tbl_all_test)``, for sanity-checking.
    """
    is_haredi = tbl_all_test["pikuach_id"] == 3
    is_mizrach_yerushalayim = (tbl_all_test["machoz_divuach"] == 13) & (
        tbl_all_test["migzar_id"] == 2
    )
    is_new_immigrant = tbl_all_test["delcodeb_n"] == 4
    is_blank_booklet = tbl_all_test["cntvalid"] == 0

    migzar_to_language = dict(
        zip(translation_tables["migzar"]["migzar"], translation_tables["migzar"]["language"])
    )
    student_bucket = np.where(
        is_haredi, 3, tbl_all_test["migzar_id"].map(migzar_to_language)
    )
    form_bucket = tbl_all_test["code_shelon_rama"].astype(str).str[2].astype(int)
    is_form_mismatch = student_bucket != form_bucket

    excluded_any = (
        is_haredi
        | is_mizrach_yerushalayim
        | is_new_immigrant
        | is_blank_booklet
        | is_form_mismatch
    )

    return {
        "national_norm_count": int((~excluded_any).sum()),
        "excluded_haredi": int(is_haredi.sum()),
        "excluded_mizrach_yerushalayim": int(is_mizrach_yerushalayim.sum()),
        "excluded_new_immigrant": int(is_new_immigrant.sum()),
        "excluded_blank_booklet": int(is_blank_booklet.sum()),
        "excluded_form_mismatch": int(is_form_mismatch.sum()),
        "total_rows": len(tbl_all_test),
    }


def aggregate_school_special_needs(tbl_all_test: pd.DataFrame) -> pd.DataFrame:
    """Per-school special-needs proportion and regular-student count (Task 4.1).

    ``tbl_all_test`` is ``delcodeb.add_delcodeb()``'s output (has
    ``semel_new`` and ``delcodeb``, among others).

    Deliberately uses ``delcodeb`` -- the **school-level** classification --
    rather than ``delcodeb_n`` (the national-level one used by
    ``compute_national_norm`` above). The task brief frames this report
    explicitly per-school ("proportion of special-needs test-takers... for
    each school"), unlike step 5's national-norm count, so the school-level
    column is the correct one here even though both functions live in this
    module.

    Per the brief, new immigrants (``delcodeb == 4``) and blank booklets
    (``delcodeb == 5``) are ignored entirely -- excluded from both the
    numerator and the denominator, not just the special-needs count. Rows
    with ``delcodeb`` left ``NaN`` (the documented ``needs_review`` gap --
    18 such rows in the real data, students present in ``sppop`` with no
    rule covering their group/status combination) are also excluded here.
    This is a deliberate "flag, don't guess" choice consistent with Phases
    2-3: those students are unclassified, not confirmed regular or confirmed
    special-needs, so forcing them into either bucket would silently
    misrepresent the proportion rather than leaving the gap visible.

    Among the remaining rows (``delcodeb`` in ``{0, 6, 7}``), groups by
    ``semel_new`` and computes:

    - ``regular_count``: rows where ``delcodeb == 0``.
    - ``special_needs_count``: rows where ``delcodeb != 0`` (i.e. ``6`` or
      ``7``, within this already-filtered set).
    - ``total_considered``: ``regular_count + special_needs_count``.
    - ``special_needs_proportion``: ``special_needs_count /
      total_considered``. Left as ``NaN`` for a school where
      ``total_considered == 0`` rather than raising a divide-by-zero error
      -- such a school fails ``school_special_needs_report()``'s
      ``regular_count > 15`` threshold anyway, so the ``NaN`` is harmless
      and never surfaces in the final report.

    Returns one row per ``semel_new`` with columns: ``semel_new``,
    ``regular_count``, ``special_needs_count``, ``total_considered``,
    ``special_needs_proportion``. Pure function: no printing, no file I/O,
    no mutation of ``tbl_all_test``.
    """
    considered = tbl_all_test[~tbl_all_test["delcodeb"].isin([4, 5])]
    considered = considered[considered["delcodeb"].notna()]

    is_regular = considered["delcodeb"] == 0

    grouped = (
        considered.assign(is_regular=is_regular)
        .groupby("semel_new")["is_regular"]
        .agg(regular_count="sum", total_considered="count")
        .reset_index()
    )
    grouped["special_needs_count"] = (
        grouped["total_considered"] - grouped["regular_count"]
    )
    grouped["special_needs_proportion"] = grouped["special_needs_count"] / grouped[
        "total_considered"
    ].replace(0, np.nan)

    return grouped[
        [
            "semel_new",
            "regular_count",
            "special_needs_count",
            "total_considered",
            "special_needs_proportion",
        ]
    ]


def school_special_needs_report(school_stats: pd.DataFrame) -> pd.DataFrame:
    """Filter per-school stats to schools exceeding both report thresholds (Task 4.2).

    ``school_stats`` is ``aggregate_school_special_needs()``'s output.

    Per the task brief's step 6, keeps only schools where the special-needs
    proportion exceeds 20% **and** the regular test-taker count exceeds 15
    (both strict ``>``, not ``>=``). Schools with ``total_considered == 0``
    (and therefore a ``NaN`` ``special_needs_proportion``) naturally fail
    the ``regular_count > 15`` condition and are excluded without any extra
    handling.

    Returns the filtered rows with the same columns as ``school_stats``, in
    whatever order ``filter``/boolean indexing naturally produces (no
    re-sort applied). Pure function: no printing, no file I/O, no mutation
    of ``school_stats``.
    """
    mask = (school_stats["special_needs_proportion"] > 0.20) & (
        school_stats["regular_count"] > 15
    )
    return school_stats[mask]

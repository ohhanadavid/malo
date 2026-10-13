"""Data-loading layer (Phase 1, Task 1.1).

One function per source file under ``Data/``. Every loader is a pure
function: it takes a path (or uses the project's ``Data/`` dir by default),
reads the file with pandas, and returns plain ``pandas.DataFrame``(s) with no
side effects (no printing, no global state, no mutation of the source
files).

Deliberately out of scope here (see docs/project-plan.md Phase 7): recoding
the 98/99 non-response sentinel values in the ``Q*`` answer columns of
``load_all_data``'s output. Those are left exactly as read.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Project root is the parent of this file's parent (src/.. == project root).
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

# Column names for each of the three stacked tables in the translation-tables
# file, keyed by that table's header value (first cell of its header row).
_TRANSLATION_TABLE_SPECS: dict[str, list[str]] = {
    "pikuach_id": ["pikuach_id", "desc"],
    "migzar": ["migzar", "desc", "language"],
    "language": ["language", "desc"],
}


def load_all_data(path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load every sheet of ``all_data.xlsx`` in one call.

    Returns a ``dict[str, pd.DataFrame]`` keyed by sheet name, so it
    naturally includes the form sheets (``472``, ``506``, ``541``, ``542``,
    ``653``, ``654``) plus the ``varname`` sheet, without hardcoding sheet
    names -- a future form sheet just shows up as another dict entry.
    """
    if path is None:
        path = DATA_DIR / "all_data.xlsx"
    return pd.read_excel(path, sheet_name=None, engine="openpyxl")


def load_schools(path: str | Path | None = None) -> pd.DataFrame:
    """Load ``schools.xlsx``'s single sheet.

    ``schools.xlsx`` stores missing numeric values (e.g. in ``asiron_h``,
    ``asiron_e``) as the literal string ``"NULL"`` instead of a blank cell
    (see CLAUDE.md's "Data quirks" section) -- ``na_values=["NULL"]`` turns
    those into real ``NaN``.
    """
    if path is None:
        path = DATA_DIR / "schools.xlsx"
    return pd.read_excel(path, sheet_name=0, na_values=["NULL"], engine="openpyxl")


def load_sppop(path: str | Path | None = None) -> pd.DataFrame:
    """Load ``sppop.xlsx``'s single sheet, plain (no special NA handling)."""
    if path is None:
        path = DATA_DIR / "sppop.xlsx"
    return pd.read_excel(path, sheet_name=0, engine="openpyxl")


def load_translation_tables(path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load ``טבלאות תרגום.xlsx`` and split it into its three stacked tables.

    The sheet holds three stacked code->label tables (``pikuach_id,desc``;
    ``migzar,desc,language``; ``language,desc``) separated by blank rows.
    Those blank rows have no explicit XML row element in the sheet (so a
    raw cell-count scan of the file misses them), but pandas/openpyxl still
    materializes them because they fall inside the sheet's used range --
    read with ``header=None``, then split by detecting each table's header
    row (first cell equal to one of ``"pikuach_id"``, ``"migzar"``,
    ``"language"``), slicing out that table's rows up to the next header and
    dropping any all-NaN blank rows, then assigning its own column names.

    Returns a ``dict[str, pd.DataFrame]`` with keys ``"pikuach_id"``,
    ``"migzar"``, ``"language"``.
    """
    if path is None:
        path = DATA_DIR / "טבלאות תרגום.xlsx"
    raw = pd.read_excel(path, sheet_name=0, header=None, engine="openpyxl")

    header_positions = [
        i
        for i in range(len(raw))
        if raw.iat[i, 0] in _TRANSLATION_TABLE_SPECS
    ]

    tables: dict[str, pd.DataFrame] = {}
    for position, start in enumerate(header_positions):
        key = raw.iat[start, 0]
        columns = _TRANSLATION_TABLE_SPECS[key]
        end = (
            header_positions[position + 1]
            if position + 1 < len(header_positions)
            else len(raw)
        )
        data = raw.iloc[start + 1 : end, : len(columns)].dropna(how="all").copy()
        data.columns = columns
        tables[key] = data.reset_index(drop=True)

    return tables


if __name__ == "__main__":
    all_data = load_all_data()
    for sheet_name, df in all_data.items():
        print(f"all_data[{sheet_name!r}]: shape={df.shape}")
        print(df.dtypes)
        print()

    schools = load_schools()
    print(f"schools: shape={schools.shape}")
    print(schools.dtypes)
    print()

    sppop = load_sppop()
    print(f"sppop: shape={sppop.shape}")
    print(sppop.dtypes)
    print()

    translation_tables = load_translation_tables()
    for table_name, df in translation_tables.items():
        print(f"translation_tables[{table_name!r}]: shape={df.shape}")
        print(df.dtypes)
        print()

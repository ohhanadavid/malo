"""Entry point for the Malo response-rate pipeline (Phase 6, Task 6.1).

Run from the project root with:

    .venv\\Scripts\\python.exe main.py

This script is pure wiring: it loads the raw data, runs it through the
already-built/already-tested transforms in ``src/``, computes the two final
reports, writes everything to ``output/``, and prints a short summary to the
console. No logic from ``src/`` is reimplemented or altered here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

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

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def build_summary_lines(norm_result: dict, num_schools: int) -> list[str]:
    """Build the human-readable summary as a list of lines.

    Shared between the console printout and ``output/summary.txt`` so the
    two never drift apart.
    """
    return [
        "Malo Pipeline - Summary Report",
        "===============================",
        "",
        f"Total students (rows in TblAllTest): {norm_result['total_rows']}",
        "",
        "National norm count (students counted toward the national "
        f"response-rate norm): {norm_result['national_norm_count']}",
        "",
        "Breakdown of the 5 exclusion conditions (each counted independently;",
        "these conditions are NOT mutually exclusive -- a student can match more",
        "than one -- so they do NOT sum to the total number of excluded students):",
        f"  - Excluded as Haredi (pikuach_id == 3): {norm_result['excluded_haredi']}",
        "  - Excluded as Mizrach Yerushalayim (East Jerusalem, Arab sector, "
        f"district 13): {norm_result['excluded_mizrach_yerushalayim']}",
        "  - Excluded as new immigrant (national level): "
        f"{norm_result['excluded_new_immigrant']}",
        "  - Excluded as blank booklet (cntvalid == 0): "
        f"{norm_result['excluded_blank_booklet']}",
        "  - Excluded due to form/population mismatch: "
        f"{norm_result['excluded_form_mismatch']}",
        "",
        "Schools in final special-needs report (special-needs proportion > 20% "
        f"AND regular test-taker count > 15): {num_schools}",
    ]


def main() -> None:
    print("Malo response-rate pipeline")
    print("============================")

    print("[1/7] Loading data (all_data, schools, sppop, translation tables)...")
    all_data = load_all_data()
    schools = load_schools()
    sppop = load_sppop()
    translation_tables = load_translation_tables()

    print("[2/7] Computing cntvalid for every form sheet...")
    all_data_cv = compute_cntvalid(all_data)

    print("[3/7] Classifying special-needs students (pop_id/pop_id_n)...")
    sppop_classified = classify_pop_id(sppop, all_data_cv)

    print("[4/7] Building TblAllTest...")
    tbl_all_test = build_tbl_all_test(all_data_cv, schools)

    print("[5/7] Adding delcodeb/delcodeb_n...")
    tbl_all_test = add_delcodeb(tbl_all_test, sppop_classified)

    print("[6/7] Computing national norm and school special-needs report...")
    norm_result = compute_national_norm(tbl_all_test, translation_tables)
    school_stats = aggregate_school_special_needs(tbl_all_test)
    report = school_special_needs_report(school_stats)

    print("[7/7] Writing results to output/...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tbl_all_test.to_excel(OUTPUT_DIR / "TblAllTest.xlsx", index=False)
    sppop_classified.to_excel(OUTPUT_DIR / "sppop_classified.xlsx", index=False)

    with pd.ExcelWriter(OUTPUT_DIR / "all_data_with_cntvalid.xlsx") as writer:
        for sheet_name, df in all_data_cv.items():
            if sheet_name == "varname":
                continue
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    report.to_excel(OUTPUT_DIR / "school_special_needs_report.xlsx", index=False)

    summary_lines = build_summary_lines(norm_result, len(report))
    (OUTPUT_DIR / "summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    print()
    print("Done. Results written to:", OUTPUT_DIR)
    print()
    for line in summary_lines:
        print(line)


if __name__ == "__main__":
    main()

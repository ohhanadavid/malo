# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session log (required)

For every turn in this chat (each user message and the response to it), append an entry to `session-log.md` in the project root containing: the user's instruction (verbatim or lightly trimmed), and a short summary of what was actually done in response. Append — never overwrite or delete prior entries. Do this for every turn in this project, not just coding turns.

## Project state

There is no git repository or README. The task brief (`task/תרגיל.docx`, Hebrew) originally left R-or-Python open; the implementation language was decided as **Python**. The pipeline is fully built and verified against the real data: Phases 0-6 are complete (data loading, `cntvalid`, `pop_id`/`pop_id_n` classification, `TblAllTest`, `delcodeb`/`delcodeb_n`, the national-norm count, the school special-needs report, a 37-test pytest suite, and the `main.py` entry point). **Phase 7 (98/99 non-response recoding) is the one remaining outstanding item** — see `docs/project-plan.md`'s Phase 7 for the full spec; it's deliberately sequenced last in that document but its actual implementation point is alongside Phase 2's `cntvalid`.

## Commands

- **Run the full pipeline**: `.venv\Scripts\python.exe main.py` from the project root — the one file a user runs themselves, no AI needed. Loads the data, runs the full transform chain, and writes `TblAllTest.xlsx`, `sppop_classified.xlsx`, `all_data_with_cntvalid.xlsx`, `school_special_needs_report.xlsx`, and `summary.txt` to `output/` (gitignored), printing progress and the key numbers to the console.
- **Run the test suite**: `.venv\Scripts\python.exe -m pytest tests/ -v` from the project root (37 tests — see `docs/testing.md` for conventions and coverage).
- **Environment setup** (venv creation, installing `requirements.txt`): see `docs/environment.md`.

## Pipeline structure (`src/`)

One function per module, each pure (no I/O/printing/mutation) and already verified against the real data (see `docs/project-plan.md` for the exact verified numbers per phase):

| Module | Function | Task |
|---|---|---|
| `loaders.py` | `load_all_data`, `load_schools`, `load_sppop`, `load_translation_tables` | Phase 1 |
| `transforms.py` | `compute_cntvalid` | Task 2.1 |
| `pop_id.py` | `classify_pop_id` | Task 2.2 |
| `tbl_all_test.py` | `build_tbl_all_test` | Task 2.3 |
| `delcodeb.py` | `add_delcodeb` | Task 2.4 |
| `reporting.py` | `compute_national_norm` | Phase 3 |
| `reporting.py` | `aggregate_school_special_needs`, `school_special_needs_report` | Phase 4 |

`main.py` (project root, not inside `src/`) wires these together in order and exports the results — see "Commands" above.

The phased build plan / to-do list lives in `docs/project-plan.md` — check it off and keep it current as phases complete; it also records which phases/tasks are sequential vs. can run in parallel, and the exact already-verified real-data numbers for each phase.

The task brief also has a full literal bilingual (Hebrew/English) translation at `task/task_translation.md`, in addition to the condensed/structured version in this file. Testing conventions are in `docs/testing.md`.

## The task (translated from `task/תרגיל.docx`)

Goal: compute **response/completion rates** (שיעורי השבה) at the school and national level for a set of exam "forms" (נוסחים).

Steps, in order (read all of them before starting, since later steps depend on earlier ones):

1. **Flag blank booklets.** For every form sheet in `all_data.xlsx`, add a column `cntvalid` = count of answered questions, counting only questions whose `varname` sheet entry has `Ind1 == 1`. Values `98`/`99` are not valid answers and don't count. Build this as a loop over all form sheets (don't hardcode one sheet's logic).

2. **Classify special-needs students** (`sppop.xlsx`) into `pop_id` based on `Kvutza_musheret` (group) and `status_meushar` (status):
   - group 1 + status 200 (default) → new immigrant (עולה חדש)
   - group 1 + status 400 → veteran immigrant (עולה ותיק)
   - group 2 + status 400 (default) → veteran immigrant
   - group 2 + status 200 → new immigrant
   - groups 5/6 + status 400 (default) → combined/integrated (משולב)
   - groups 5/6 + status 200/300 → if the student actually tested (`cntvalid > 0`) reclassify as status 400 and handle per that rule; if they did not test, mark `del = 2`
   - status 100 → regular student at the **school** level, but at the **national** level classify per the student's group/default status
   - status 700 → regular student
   - status 600 → if tested (`cntvalid > 0`), classify per group/default status; if not tested, delete from the special-needs file (mark `del = 1`)

   Coding table for `pop_id`: regular=0, new immigrant=4, combined=6, veteran immigrant=7.
   `pop_id_n` (national-level) mirrors `pop_id` except for the status-100 case above.

3. **Build `TblAllTest`**: one combined dataset with every student from every form, containing: ID (taz_new), school code (semel_new), MAKBILA_tiyuv (form/parallel code), code_shelon_rama (questionnaire code), SIDURY_SHELON (questionnaire serial), and `cntvalid`. Join in `migzar_id` (sector), `pikuach_id` (supervision), `machoz_divuach` (district) from `schools.xlsx` (via `semel_new`).

4. Add `delcodeb`: same as `pop_id`, except blank booklets always get `5`. Students absent from the special-needs file are treated as regular. Mirror this as `delcodeb_n` from `pop_id_n`.

5. Compute the national-norm test-taker count, **excluding**: Haredi students, מז"י (East Jerusalem, Arab sector in district 13), new immigrants, and blank booklets. Also exclude students who tested with a form that doesn't match their population (e.g. Arabic-speaking students tested in the Hebrew form or vice versa; Haredi students tested in a non-Haredi form or vice versa) — the **3rd digit of the questionnaire code** (`code_shelon_rama`, counting from the left) indicates the form's target population: `1`=Hebrew-speaking/non-Haredi (forms `472`/`506`), `2`=Arabic-speaking (forms `541`/`542`), `3`=Haredi (forms `653`/`654`) — resolved against the real data, see "Data quirks" below.

6. Produce a list of schools where the proportion of special-needs test-takers exceeds 20% **and** the number of regular test-takers exceeds 15 (for this calculation, ignore new immigrants and blank booklets).

## Data files (`Data/`)

- **`all_data.xlsx`** — one sheet per exam form code, plus a `varname` sheet.
  - Form sheets: `472`, `506`, `541`, `542`, `653`, `654`. Common columns: `taz_new` (student ID), `semel_new` (school code), `code_shelon_rama` (questionnaire/form code — 3rd digit = target population), `SIDURY_SHELON` (questionnaire serial), `MAKBILA_tiyuv` (parallel form id; `542`/`653` also have `MAKBILA_hibachanut`), `gender_tiyuv`, then per-question answer columns (`Q1_a`, `Q2_1`, `Q3_0_voc`, etc. — naming varies by form).
  - `varname` sheet: `code_shelon_omer`, `VarName`, `Ind1` — maps each question column to a description and flags (`Ind1`) whether it counts toward `cntvalid`.
- **`schools.xlsx`** (`Sheet1`) — one row per school: `semel_new`, `tert`, `mivne_mosad`, `migzar_id` (sector), `pikuach_id` (supervision), `gorem_medaveach`, `machoz_divuach` (district), `rashut_chinuch`, `semel_yishuv`, `asiron_y`/`asiron_h`/`asiron_e` (socioeconomic deciles).
- **`sppop.xlsx`** (`Sheet1`) — special-needs population: `semel_new`, `taz_new`, `makbila_tiyuv`, `oleh_y1`, `oleh_y2_y3`, `meshulav`, `Kvutza_musheret` (group), `status_meushar` (status), `pop_id`, `pop_id_n`, `del`. This is the file step 2 above updates.
- **`טבלאות תרגום.xlsx`** (translation tables, `Sheet1`) — **not one table**: three code→label tables are stacked vertically in the same sheet, each starting with its own header row. Parse by splitting on the header rows (`pikuach_id,desc`, `migzar,desc,language`, `language,desc`), don't treat it as a single rectangular table.
  - `pikuach_id`: 1=ממלכתי (state/secular), 2=ממ"ד (state-religious), 3=חרדי (Haredi) — this is what step 5's Haredi exclusion filters on (`pikuach_id == 3`).
  - `migzar` (sector): 1=יהודי (Jewish, `language`=1), 2=ערבי (Arab, `language`=2), 4=דרוזי (Druze, `language`=2), 5=בדואי (Bedouin, `language`=2), 6=צ'רקסי (Circassian, `language`=1).
  - `language`: 1=דוברי עברית (Hebrew speakers), 2=דוברי ערבית (Arabic speakers) — this is what step 5's form/population-mismatch check needs (comparing a student's sector-derived language against the form's target-population digit in `code_shelon_rama`).
  - **Correction from Task 1.1 implementation**: the three stacked tables *are* separated by blank rows in the real file — those rows just have no explicit XML `<row>` element (so a raw cell-count scan of the file misses them entirely), but pandas/openpyxl still materializes them because they fall inside the sheet's used range (17 rows total, not 13). `src/loaders.py`'s `load_translation_tables()` handles this with `.dropna(how="all")` after slicing each table out — don't assume a naive header-to-next-header slice is safe without that.

Join key across files is `semel_new` (school code); `taz_new` is the student id used to join form sheets with `sppop.xlsx`.

## Data quirks observed from actual rows (not just headers)

Read full/sampled row data from every sheet (varname sheet and translation tables in full; `all_data`/`schools`/`sppop` form sheets sampled, since they run 1k–14k rows each). Things to account for when writing the pipeline:

- **`varname` sheet structure**: for each form code, rows list every question column name (`VarName`) with `Ind1` (1 = counts toward `cntvalid`, 0 = doesn't). The pattern is consistent across forms: all `Q0_*` columns (background/demographic questions) are `Ind1=0`; every other `Q*` column is `Ind1=1`. Still, drive `cntvalid` off this table programmatically (join `code_shelon_rama`/sheet name → `VarName` → `Ind1`), not off the naming pattern, since it's the authoritative source.
- **Orphan code in `varname`**: the sheet includes a full question block (56 rows) for form code `477`, but `all_data.xlsx` has no `477` sheet (only `472, 506, 541, 542, 653, 654`) — **confirmed genuinely unused** (Phase 1, Task 1.2): `load_all_data()` returns a dict keyed by the sheets that actually exist, so looping over its keys naturally skips `477` without any special-casing. Code that loops "for each form" should drive off the sheets actually present, and not assume every `code_shelon_omer` in `varname` has a matching sheet (or vice versa).
- **`sppop.xlsx`**: `pop_id`, `pop_id_n`, and `del` are blank/`NULL` for all 10,647 rows — they are the *output* columns step 2 computes, not pre-filled input. **Correction** (Phase 2 design, full data — an earlier note here said group values were `1,2,3,5,6`, based on only a 15-row sample; that was wrong): the real `Kvutza_musheret` (group) values are `{0, 1, 2, 5, 6, 10}` — there is no group `3`. The full `(Kvutza_musheret, status_meushar)` matrix matches the brief's rules cleanly except one gap: **group `0` with status `300` (117 rows) has no defined rule anywhere in the brief** (status 300 only has meaning for groups 5/6). Group `10` always pairs with status `700`, which is unambiguous ("regular student" regardless of group) — not actually a gap. Decision (confirmed with the user): the 117 group-0/status-300 rows are left unclassified (`pop_id`/`pop_id_n` stay `NaN`) and flagged via a `needs_review` column in `classify_pop_id`'s output, rather than guessed at.
- **`schools.xlsx`**: missing numeric values (e.g. in `asiron_h`, `asiron_e`) are stored as the literal string `"NULL"`, not an empty cell — **confirmed handled** (Phase 1, Task 1.2): `load_schools()` passes `na_values=["NULL"]`, verified against the real file to leave zero object-dtype columns and the expected NaN counts (`asiron_h`: 3035 NaN, `asiron_e`: 2620 NaN out of 3843 rows).
- **`code_shelon_rama`** (questionnaire code) — **resolved** (Phase 1, Task 1.2). It's constant per form sheet, 5 digits (`472`→`26112`, `506`→`26122`, `541`→`26212`, `542`→`26222`, `653`→`26312`, `654`→`26322`). Counting from the **left**, digit 3 is the target-population flag the footnote refers to, and it groups the 6 forms into exactly 3 pairs. Confirmed by cross-tabulating against the real `schools.xlsx` join (`migzar_id`/`pikuach_id` via `semel_new`): digit3=`1` → Hebrew-speaking/non-Haredi (forms `472`/`506`; `migzar_id=1`, `pikuach_id` 1 or 2), digit3=`2` → Arabic-speaking (forms `541`/`542`; `migzar_id` 2/4/5), digit3=`3` → Haredi (forms `653`/`654`; mostly `pikuach_id=3`). The handful of students crossing these boundaries in the real data (e.g. a few Haredi students under a digit3=1 form) are exactly the form/population mismatches step 5 is supposed to detect and exclude — not noise to explain away.
- **98/99 non-response codes are not interchangeable** — resolved from real data (Phase 7, Task 7.1). They're strongly column-specific: on sheet `472`, `Q6_0`/`Q7_0`/`Q13_0`/`Q18_0` have hundreds of `98`s and almost no `99`s, while `Q19_0`/`Q20_a/b/c`/`Q23_0`/`Q24_0` have zero `98`s and thousands of `99`s. `99` is far more common overall (16-33% of `Ind1==1` cells per form) than `98` (0.3-1%) — each question's response format likely has its own fixed invalid-answer convention. The exact semantic difference (e.g. "not administered" vs. "left blank") isn't resolvable from the data alone and remains an open question for the task-giver. Practically this doesn't affect anything already built: `cntvalid` already excludes both regardless of meaning, and no other pipeline function reads an individual `Q*` value — the only place raw `98`/`99` is visible at all is `output/all_data_with_cntvalid.xlsx`'s `Q*` columns, which are deliberately left unrecoded for now (user decision, see `docs/project-plan.md` Phase 7 Task 7.2).

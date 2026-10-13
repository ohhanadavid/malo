# Environment & Tooling

Decided as Phase 0, Task 0.2 of `docs/project-plan.md`.

## Python version

- **Minimum: Python 3.11+.** Confirmed available on this machine: Python 3.12.6 at
  `C:\Users\sustu\AppData\Local\Programs\Python\Python312\python.exe`. Use this
  interpreter for the venv.

## Virtual environment

Stdlib `venv` — no need for conda/poetry on a project this size (one pipeline,
a handful of dependencies).

**Create (PowerShell, from the project root):**

```powershell
C:\Users\sustu\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
```

**Activate (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script with an execution-policy error, run
once per machine (current user, not system-wide):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Install requirements (after activating):**

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`.venv/` is project-local and listed in `.gitignore` — never commit it.

## Libraries (`requirements.txt`)

Version floors, not exact pins — small, fixed dependency set, no need to lock
further:

- **`pandas>=2.1`** — loading the `.xlsx` sheets, joins (`semel_new`,
  `taz_new`), and the row-level/aggregate transforms in Phases 1-4.
- **`openpyxl>=3.1`** — the engine `pandas` needs to read/write `.xlsx`
  (`all_data.xlsx`, `schools.xlsx`, `sppop.xlsx`, the translation-tables
  file, and the Phase 6 output workbooks).
- **`pytest>=7.4`** — the Phase 5 unit/sanity-check test suite.

No other libraries are provisioned at this stage; add one later only if a
concrete need shows up during implementation (e.g. a specific Excel quirk
`openpyxl` can't handle).

## Repo layout

```
Malo/
├── Data/                  # source Excel files (unchanged)
├── docs/                  # project documentation (this file, project-plan.md, ...)
├── output/                # generated result files, written by main.py — gitignored:
│                          #   TblAllTest.xlsx, sppop_classified.xlsx,
│                          #   all_data_with_cntvalid.xlsx,
│                          #   school_special_needs_report.xlsx, summary.txt
├── src/                   # pipeline package, one module per transform:
│   ├── loaders.py         #   Phase 1: read all_data/schools/sppop/translation sheets
│   ├── transforms.py      #   Phase 2 Task 2.1: compute_cntvalid
│   ├── pop_id.py          #   Phase 2 Task 2.2: classify_pop_id (pop_id/pop_id_n/del)
│   ├── tbl_all_test.py    #   Phase 2 Task 2.3: build_tbl_all_test
│   ├── delcodeb.py        #   Phase 2 Task 2.4: add_delcodeb
│   └── reporting.py       #   Phase 3-4: national-norm count, school special-needs list
├── main.py                # entry point (Phase 6) -- run with
│                          #   .venv\Scripts\python.exe main.py
│                          # the one file a user runs themselves, no AI needed
├── tests/                 # pytest suite (Phase 5), mirrors src/ module names
├── task/                  # original brief + translation
├── requirements.txt
├── .gitignore
└── CLAUDE.md
```

Rationale: the brief is one ETL/analysis pipeline, not a service — a small
`src/` package with a `tests/` sibling is enough structure to keep loaders,
transforms, and reporting separable and testable, without over-scaffolding a
framework-style project. Phase 2 ended up as **one file per transform**
(`transforms.py`/`pop_id.py`/`tbl_all_test.py`/`delcodeb.py`) rather than one
shared `transforms.py`, specifically so Tasks 2.2 and 2.3 — independent of
each other, both only depending on 2.1 — could be implemented by two parallel
subagents without both editing the same file. `reporting.py`/`main.py` and
`tests/` are still unwritten; those come in Phases 3-5.

## Status

Decided, scaffolded, and **set up**: `.venv/` has been created with the
Python 3.12.6 interpreter above, and `requirements.txt` installed cleanly
into it (`pandas 3.0.6`, `numpy 2.5.3`, `openpyxl 3.1.5`, `pytest 9.1.1`, plus
their transitive dependencies). Ready to start Phase 1.

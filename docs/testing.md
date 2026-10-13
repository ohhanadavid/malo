# Testing

> *Maintained by: test-runner agent*

## Framework

`pytest` (installed in the project's `.venv`, see `docs/environment.md`).
No other test framework is in use.

## Commands

Run from the project root (`C:\Users\sustu\Documents\my projects\Malo`):

```powershell
# Full suite
.\.venv\Scripts\python.exe -m pytest tests/ -v

# A single file
.\.venv\Scripts\python.exe -m pytest tests/test_transforms.py -v

# With coverage (requires pytest-cov; not currently installed/required)
.\.venv\Scripts\python.exe -m pytest tests/ --cov=src
```

(Bash/POSIX equivalent: `./.venv/Scripts/python.exe -m pytest tests/ -v`.)

## Directory / naming conventions

- `tests/` mirrors `src/` module names: `tests/test_<module>.py` tests
  `src/<module>.py` (e.g. `tests/test_transforms.py` tests
  `src/transforms.py`).
- Tests import directly from the `src` package (`from src.transforms import
  compute_cntvalid`), relying on `src/__init__.py` and pytest's rootdir-based
  `sys.path` insertion — no editable install or `conftest.py` path hacks
  needed.
- All unit tests (`test_transforms.py`, `test_pop_id.py`, `test_delcodeb.py`)
  run against small, hand-built synthetic DataFrames — fast and
  self-contained. Every test also asserts the function under test does not
  mutate its input DataFrame(s)/dict, since all three Phase 2 transform
  functions are documented as pure.
- `test_integration.py` is the one exception: it runs the full pipeline
  against the real `Data/*.xlsx` files via the real loaders (a few seconds
  to load — acceptable for one module), module-scoped via a `pytest.fixture`
  so the pipeline runs once and is reused across its tests.

## Current coverage (Phase 5, Task 5.1)

Covers the three Phase 2 pure transform functions, one test file each:

- **`tests/test_transforms.py`** — `compute_cntvalid` (`src/transforms.py`):
  correct per-row counting of `Ind1==1` columns, 98/99 exclusion, `Ind1==0`
  columns ignored, `varname` passed through unchanged, no input mutation,
  multiple form sheets don't cross-contaminate each other's valid-column
  sets.
- **`tests/test_pop_id.py`** — `classify_pop_id` (`src/pop_id.py`): every
  branch of the group/status decision table (groups 1/2/5/6, statuses
  100/200/300/400/600/700, both tested and untested group-5/6 reclassify
  cases, `del=1`/`del=2`, the group-0/status-300 unhandled-gap
  `needs_review` case), no input mutation.
- **`tests/test_delcodeb.py`** — `add_delcodeb` (`src/delcodeb.py`): blank
  booklet override to `5` (even over a defined `pop_id`), absent-from-sppop
  default to `0`, matched defined `pop_id`/`pop_id_n` carried over, and the
  matched-but-`NaN` (`needs_review`) case staying `NaN` rather than
  defaulting to `0` — a regression test for the specific bug
  `add_delcodeb`'s `indicator`-based merge was built to avoid.

28 tests total, all passing as of this writing.

## Current coverage (Phase 5, Task 5.2)

**`tests/test_integration.py`** — end-to-end sanity checks on the real
data, building the full pipeline once per test session (`compute_cntvalid`
-> `classify_pop_id` -> `build_tbl_all_test` -> `add_delcodeb`) against the
actual `Data/*.xlsx` files:

- **Row-count reconciliation**: `TblAllTest` has exactly 42,890 rows (sum of
  the 6 form sheets), `taz_new` is fully unique, and the school attributes
  joined in from `schools.xlsx` (`migzar_id`, `pikuach_id`,
  `machoz_divuach`) have zero nulls.
- **National-norm regression check**: `reporting.compute_national_norm`'s
  exact already-verified real-data result (`national_norm_count=33800`,
  `total_rows=42890`, with the 5 exclusion counts from
  `docs/project-plan.md` Task 3.3).
- **School-report regression check**: `aggregate_school_special_needs`
  (1,089 schools considered) + `school_special_needs_report` (72 schools
  meet both thresholds), including school `1474`'s exact proportion
  (`≈0.454545`, `regular_count=18`).
- **Independent spot-check** (not circular — doesn't call
  `transforms.compute_cntvalid`/`pop_id.classify_pop_id`): 7 real students
  at school `3867` (`taz_new` 10258-10262 on form `472`, 24893-24894 on
  form `506`), with `cntvalid` re-derived by hand straight from the raw
  `Ind1`/98-99 rule and `pop_id`/`delcodeb` re-derived by hand from the
  group/status table, covering one genuine blank booklet (`10258`,
  all-98/99 answers) and one classified special-needs student (`24893`,
  group 6/status 400 -> combined, `delcodeb=6`); the other 5 students are
  absent from `sppop.xlsx` and confirmed to default to regular (`delcodeb=0`).

9 tests, all passing as of this writing — 37 tests total across the full
suite.

## Known flaky tests

None currently.

## Coverage baseline

No numeric coverage threshold is enforced or tracked yet; `pytest-cov` is
not installed (not in `requirements.txt`). Coverage here is treated as a
correctness signal (every decision-table branch has an explicit test) per
`docs/environment.md`'s decided library set, not a percentage target.

## Test-only infrastructure

None. No external services, Docker test containers, or seeded databases are
needed. Most functions under test are pure, in-memory pandas
transformations exercised with hand-built synthetic DataFrames.
`tests/test_integration.py` is the exception: it reads the real
`Data/*.xlsx` files already checked into the project (no credentials, no
network, no separate test fixture data) directly off disk via the real
loaders.

## Scope note

Phase 5 is complete: Task 5.1 (unit tests for the Phase 2 transforms) and
Task 5.2 (end-to-end sanity checks on the real data, `test_integration.py`)
are both written and passing.

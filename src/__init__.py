"""Pipeline package for the Malo data-analysis exercise.

Sub-modules (built out across the project's phases, see docs/project-plan.md):
    loaders       -- Phase 1: read all_data/schools/sppop/translation-table sheets.
    transforms    -- Phase 2 Task 2.1: compute_cntvalid.
    pop_id        -- Phase 2 Task 2.2: classify_pop_id (pop_id/pop_id_n/del).
    tbl_all_test  -- Phase 2 Task 2.3: build_tbl_all_test.
    delcodeb      -- Phase 2 Task 2.4: add_delcodeb.
    reporting     -- Phase 3-4: national-norm count, school special-needs list.

The runnable entry point is ../main.py at the project root (not a sub-module
here) -- run it with ``.venv\\Scripts\\python.exe main.py`` from the project
root.
"""

# FraudDet (consolidated)

This repository contains two packages merged into a single workspace. The fraud detection crew lives under `src/fraud_det` and a reusable library under `src/crew_ai`.

Running tests

- Use the project's virtualenv: `/.venv/bin/python` is present at the repo root.
- To run tests from the repo root:

```bash
PYTHONPATH=./src /.venv/bin/python -m pytest -q
```

Editable install

If you prefer not to set PYTHONPATH, install the package(s) in editable mode:

```bash
/.venv/bin/python -m pip install -e ./src
```

Smoke run of the fraud workflow (safe, local checks)

The repo includes `tests/test_fraud_smoke.py`, which validates the crew wiring and task configs without calling external services or LLMs.

Integration and local runs (LLMs)

- To run the crew locally using real LLM credentials (this will call external APIs):

```bash
export OPENAI_API_KEY="<your key>"
PYTHONPATH=./src /.venv/bin/python scripts/run_local.py
```

- To run the guarded integration test (CI-safe), set RUN_INTEGRATION=1 and ensure credentials are set. This test is skipped by default.

```bash
export RUN_INTEGRATION=1
export OPENAI_API_KEY="<your key>"
PYTHONPATH=./src /.venv/bin/python -m pytest tests/test_integration.py -q
```

FAISS benchmark

```bash
PYTHONPATH=./src /.venv/bin/python scripts/bench_faiss.py
```

Notes

- The FAISS backend is the preferred RAG adapter; an in-memory fallback exists for local development.
- If you plan to run the Crew engine end-to-end with LLMs, ensure credentials and network access are configured in the venv.

Notes

- The FAISS backend is the preferred RAG adapter; an in-memory fallback exists for local development.
- If you plan to run the Crew engine end-to-end with LLMs, ensure credentials and network access are configured in the venv.

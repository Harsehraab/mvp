#!/usr/bin/env python3
"""Local runner for FraudDet crew using real LLMs.

Validates inputs with Pydantic schemas and runs the crew kickoff. Requires
OPENAI_API_KEY (or other provider env vars) to be set in the environment.

Usage: PYTHONPATH=./src /.venv/bin/python scripts/run_local.py
"""
import os
import json
import sys
from pathlib import Path
from typing import List

from fraud_det.schemas import InvestigateArgs, ReportArgs
from fraud_det.crew import FraudDet


def load_sample_transactions() -> List[dict]:
    # Minimal synthetic example; you can replace with real data
    now = "2025-01-01T00:00:00Z"
    return [
        {"id": "tx1", "amount": 1000.0, "currency": "USD", "timestamp": now, "metadata": {"method": "card"}},
        {"id": "tx2", "amount": 5.0, "currency": "USD", "timestamp": now, "metadata": {"method": "card"}},
        {"id": "tx3", "amount": 7500.0, "currency": "USD", "timestamp": now, "metadata": {"method": "bank_transfer"}},
    ]


def main():
    # Ensure an LLM API key exists; we don't mock — runner uses real LLMs
    if os.getenv("OPENAI_API_KEY") is None and os.getenv("CREWAI_LLM_API_KEY") is None:
        print("ERROR: No LLM credentials found. Set OPENAI_API_KEY or CREWAI_LLM_API_KEY in environment.")
        sys.exit(2)

    base = Path(__file__).resolve().parents[1] / "src" / "fraud_det" / "config"

    # Build and validate inputs for the investigation task
    tx = load_sample_transactions()
    investigate_args = {"transactions_batch": tx}
    validated = InvestigateArgs(**investigate_args)
    print("Validated investigate args:", validated)

    # Prepare kickoff inputs - depending on your crew wiring, map task inputs appropriately
    inputs = {
        "investigate_transactions": investigate_args,
    }

    # Instantiate and run the crew
    fd = FraudDet()
    fd.agents_config = json.loads((base / "agents.yaml").read_text())
    fd.tasks_config = json.loads((base / "tasks.yaml").read_text()) if (base / "tasks.yaml").exists() else {}

    print("Starting crew kickoff (this will call your configured LLMs)...")
    try:
        result = fd.crew().kickoff(inputs=inputs)
        print("Crew kickoff finished. Result:")
        print(result)
    except Exception as e:
        print("Crew run failed:", e)
        raise


if __name__ == "__main__":
    main()

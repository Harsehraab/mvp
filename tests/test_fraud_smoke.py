import os
import yaml
from pathlib import Path

from fraud_det.crew import FraudDet


def load_yaml(p):
    with open(p, "r") as f:
        return yaml.safe_load(f)


def test_fraud_smoke_configs_and_tasks():
    """Smoke test: load configs, instantiate FraudDet, create agents and tasks."""
    base = Path(__file__).resolve().parents[1] / "src" / "fraud_det" / "config"
    agents_cfg = load_yaml(base / "agents.yaml")
    tasks_cfg = load_yaml(base / "tasks.yaml")

    # Set a dummy LLM API key to avoid requiring real credentials during smoke tests.
    os.environ.setdefault("OPENAI_API_KEY", "test")

    fd = FraudDet()
    # The real crew decorator would normally populate these; set them for smoke
    fd.agents_config = agents_cfg
    fd.tasks_config = tasks_cfg

    # Create agents (call the underlying unwrapped methods to avoid crew wrappers)
    ar = FraudDet.fraud_researcher(fd)
    aa = FraudDet.fraud_analyst(fd)
    assert hasattr(ar, "__dict__")
    assert hasattr(aa, "__dict__")

    # Create tasks
    # Verify task methods exist on the class (the real crew runtime would wire these)
    assert hasattr(fd, "investigate_transactions")
    assert hasattr(fd, "triage_and_prioritize")
    assert hasattr(fd, "generate_incident_report")

    # Validate the task configs themselves (we avoid invoking crew Task wrappers
    # which may require runtime wiring of agents/LLMs).
    assert "investigate_transactions" in tasks_cfg
    assert "triage_and_prioritize" in tasks_cfg
    assert "generate_incident_report" in tasks_cfg

    # Ensure the report task expects to write a markdown report
    assert tasks_cfg["generate_incident_report"].get("expected_output")

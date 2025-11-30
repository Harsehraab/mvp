import os
import subprocess
import sys
import pytest


@pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="Integration tests disabled")
def test_integration_run_local():
    """Guarded integration test: runs the local runner which uses real LLMs.

    Requires environment variables (e.g., OPENAI_API_KEY) and RUN_INTEGRATION=1.
    """
    runner = os.path.abspath("scripts/run_local.py")
    cmd = [sys.executable, runner]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    assert proc.returncode == 0, f"Runner failed: stdout={proc.stdout}\nstderr={proc.stderr}"

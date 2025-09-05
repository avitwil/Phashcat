# tests/conftest.py
import os
import subprocess
import shutil
import pytest
from hypothesis import settings

# Hypothesis: disable per-test deadlines (hashcat strings can be long)
settings.register_profile("dev", deadline=None, max_examples=100)
settings.load_profile("dev")


@pytest.fixture(autouse=True)
def _set_hashcat_binary_env(monkeypatch):
    """
    Make binary resolution deterministic.
    Unit tests mock subprocess.run; integration tests may use a real binary.
    """
    # Prefer 'hashcat' (no .exe) so cmdline comparisons are consistent cross-OS.
    monkeypatch.setenv("HASHCAT_BINARY", "hashcat")
    yield


class DummyCompletedProcess:
    def __init__(self, args, returncode=0, stdout="", stderr=""):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def fake_run(monkeypatch):
    """
    Monkeypatch subprocess.run to avoid real execution in unit tests.
    Usage:
        def test_x(fake_run):
            fake_run["returncode"] = 0
            fake_run["stdout"] = "OK"
    """
    state = {"returncode": 0, "stdout": "OK", "stderr": ""}

    def fake_subprocess_run(args, check=True, capture_output=False, text=True):
        cp = DummyCompletedProcess(
            args=args,
            returncode=state["returncode"],
            stdout=state["stdout"] if capture_output else "",
            stderr=state["stderr"] if capture_output else "",
        )
        if check and cp.returncode != 0:
            raise subprocess.CalledProcessError(cp.returncode, args, cp.stdout, cp.stderr)
        return cp

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)
    return state


def has_real_hashcat() -> bool:
    """
    Returns True if a real 'hashcat' is discoverable on PATH or via HASHCAT_BINARY.
    """
    env = os.getenv("HASHCAT_BINARY")
    if env and os.path.exists(env):
        return True
    return shutil.which(env or "hashcat") is not None

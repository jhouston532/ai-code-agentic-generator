"""
test_runner.py — Standalone test execution module for ollama_codegen.

Provides a single public entry point:

    from test_runner import run_tests
    success, stdout, stderr = run_tests(code, task, timeout, sandbox)

The task dict must contain these keys (all produced by ollama_codegen's
parse_task_file, but the module has no dependency on ollama_codegen itself):

    expected_output : str         — exact stdout to match (empty = skip)
    input_data      : str         — stdin piped to the script (empty = none)
    test_args       : list[str]   — argv passed to the script
    inline_tests    : list[str]   — assert-style test blocks
    test_script     : str | None  — path to an external test file

Test strategies run in this order:
    1. Sandbox check      — blocks dangerous imports / calls before execution
    2. Expected output    — exact stdout match after strip()
    3. Inline assert tests — assert lines appended to the script and executed
    4. External test script — external .py run with GENERATED_MODULE env var

Strategies 2+3 can be combined: a script must pass both to be considered
successful.  If only inline tests are present (no expected_output), only
those are evaluated.  TEST_SCRIPT is evaluated last and independently.

──────────────────────────────────────────────────────────────────────────────
Extending the runner
──────────────────────────────────────────────────────────────────────────────
To add a new test strategy, implement a function with this signature:

    def _run_<name>(code, task, timeout) -> TestResult:
        ...

Then register it in STRATEGIES at the bottom of this file.  The dispatcher
in run_tests() will call it automatically when the relevant task key is set.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    success: bool
    stdout:  str = ""
    stderr:  str = ""
    # Which strategy produced this result
    strategy: str = ""
    # Detailed per-check breakdown (populated by inline-test runner)
    details: list[str] = field(default_factory=list)

    def as_tuple(self) -> tuple[bool, str, str]:
        """Backwards-compatible (success, stdout, stderr) tuple."""
        return self.success, self.stdout, self.stderr


# ── Sandbox ───────────────────────────────────────────────────────────────────

# Modules that must never appear in an import statement.
# 'sys' is intentionally absent — sys.argv is required for CLI tasks.
# Dangerous sys usages are caught by _DANGEROUS_CALLS below.
BLOCKED_IMPORTS: set[str] = {
    "os", "shutil", "subprocess", "socket",
    "glob", "fnmatch", "signal", "ctypes",
    "importlib", "multiprocessing", "threading",
}

# Call-level patterns blocked even when the parent module is allowed.
_DANGEROUS_CALLS = re.compile(
    r"\b("
    r"sys\.(exit|path\b|modules)"
    r"|shutil\.(rmtree|move|copy)"
    r"|subprocess\.(run|call|Popen|check_output|check_call)"
    r"|os\.(remove|unlink|rmdir|makedirs|system|popen|exec)"
    r")\s*\("
)


def check_sandbox(code: str) -> list[str]:
    """
    Return a list of violations found in *code*.

    Each entry is a short human-readable string describing the blocked
    import or call, e.g. ``"import os"`` or ``"sys.exit()"``.
    Empty list means the code is clean.
    """
    violations: list[str] = []

    # Pass 1 — blocked imports
    for line in code.splitlines():
        stripped = line.strip()
        m = re.match(r"^(?:import|from)\s+([\w.]+)", stripped)
        if m:
            top = m.group(1).split(".")[0]
            if top in BLOCKED_IMPORTS:
                violations.append(f"import {top}")

    # Pass 2 — dangerous calls
    for match in _DANGEROUS_CALLS.finditer(code):
        violations.append(f"{match.group(1)}()")

    return violations


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_temp(code: str) -> str:
    """Write *code* to a secure cross-platform temp file; return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(code)
        return fh.name


def _run_file(
    path: str,
    args: list[str],
    stdin_data: bytes | None,
    timeout: int,
) -> tuple[int, str, str]:
    """
    Execute *path* as a Python script.
    Returns (returncode, stdout_stripped, stderr_stripped).
    """
    try:
        result = subprocess.run(
            [sys.executable, path] + args,
            input=stdin_data,
            capture_output=True,
            timeout=timeout,
        )
        stdout = result.stdout.decode(errors="replace").strip()
        stderr = result.stderr.decode(errors="replace").strip()
        return result.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timed out after {timeout}s"


# ── Strategy implementations ──────────────────────────────────────────────────

def _strategy_expected_output(
    code: str, task: dict, timeout: int
) -> TestResult | None:
    """
    Run the script and compare stdout to task['expected_output'].
    Returns None if no expected_output is defined (strategy is skipped).
    """
    expected = task.get("expected_output", "").strip()
    if not expected:
        return None

    tmp = _write_temp(code)
    try:
        args       = task.get("test_args", [])
        stdin_data = task["input_data"].encode() if task.get("input_data") else None
        rc, stdout, stderr = _run_file(tmp, args, stdin_data, timeout)

        if rc == -1:                        # timeout
            return TestResult(False, stdout, stderr, strategy="expected_output")

        passed = stdout == expected
        detail = (
            f"expected : {repr(expected[:80])}\n"
            f"got      : {repr(stdout[:80])}"
        )
        return TestResult(
            passed, stdout, stderr,
            strategy="expected_output",
            details=[detail],
        )
    finally:
        Path(tmp).unlink(missing_ok=True)


def _strategy_inline_tests(
    code: str, task: dict, timeout: int
) -> TestResult | None:
    """
    Append each TEST: block to the generated code as assert statements
    and execute the combined script.
    Returns None if no inline tests are defined.
    """
    test_blocks: list[str] = task.get("inline_tests", [])
    if not test_blocks:
        return None

    all_asserts = "\n".join(test_blocks)
    combined    = f"{code}\n\n# ── inline tests ──\n{all_asserts}\n"
    tmp         = _write_temp(combined)

    try:
        rc, stdout, stderr = _run_file(tmp, [], None, timeout)

        if rc == -1:
            return TestResult(False, stdout, stderr, strategy="inline_tests")

        # Parse individual assertion failures out of stderr for detail
        details: list[str] = []
        if not rc == 0 and stderr:
            for line in stderr.splitlines():
                if "AssertionError" in line or "assert " in line:
                    details.append(line)

        return TestResult(
            rc == 0, stdout, stderr,
            strategy="inline_tests",
            details=details or ([stderr.splitlines()[-1]] if stderr else []),
        )
    finally:
        Path(tmp).unlink(missing_ok=True)


def _strategy_test_script(
    code: str, task: dict, timeout: int
) -> TestResult | None:
    """
    Run an external test file (task['test_script']) as a subprocess.
    The path to the generated module is injected as the GENERATED_MODULE
    environment variable so the test file can import or exec it.
    Returns None if no test_script is defined.
    """
    test_script_path = task.get("test_script")
    if not test_script_path:
        return None

    generated_tmp = _write_temp(code)
    env = {**os.environ, "GENERATED_MODULE": generated_tmp}

    try:
        result = subprocess.run(
            [sys.executable, test_script_path],
            capture_output=True,
            timeout=timeout,
            env=env,
        )
        stdout = result.stdout.decode(errors="replace").strip()
        stderr = result.stderr.decode(errors="replace").strip()

        return TestResult(
            result.returncode == 0, stdout, stderr,
            strategy="test_script",
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            False, "", f"Test script timed out after {timeout}s",
            strategy="test_script",
        )
    finally:
        Path(generated_tmp).unlink(missing_ok=True)


# ── Strategy registry ─────────────────────────────────────────────────────────
#
# Each entry is a callable with signature:
#   (code: str, task: dict, timeout: int) -> TestResult | None
#
# Returning None means "this strategy does not apply to this task".
# Strategies are evaluated in list order.  For strategies 1+2 (expected output
# and inline tests), BOTH must pass when both are present.

StrategyFn = Callable[[str, dict, int], "TestResult | None"]

STRATEGIES: list[tuple[str, StrategyFn]] = [
    ("expected_output", _strategy_expected_output),
    ("inline_tests",    _strategy_inline_tests),
    ("test_script",     _strategy_test_script),
]


# ── Public entry point ────────────────────────────────────────────────────────

def run_tests(
    code: str,
    task: dict,
    timeout: int = 15,
    sandbox: bool = True,
) -> tuple[bool, str, str]:
    """
    Run all applicable test strategies against *code*.

    Parameters
    ----------
    code    : The Python source to test.
    task    : Task dict (from parse_task_file or equivalent).
    timeout : Per-strategy execution timeout in seconds.
    sandbox : When True, block dangerous imports/calls before running anything.

    Returns
    -------
    (success, stdout, stderr)
        success — True only if every applicable strategy passed.
        stdout  — stdout from the primary execution (expected_output run).
        stderr  — combined stderr / error messages.
    """

    # ── Sandbox gate ──────────────────────────────────────────────────────────
    if sandbox:
        violations = check_sandbox(code)
        if violations:
            msg = "[SANDBOX] Blocked: " + ", ".join(dict.fromkeys(violations))
            return False, "", msg

    # ── Run strategies ────────────────────────────────────────────────────────
    results: list[TestResult] = []
    primary_stdout = ""

    for name, strategy_fn in STRATEGIES:
        result = strategy_fn(code, task, timeout)
        if result is None:
            continue                        # strategy not applicable

        results.append(result)

        if name == "expected_output":
            primary_stdout = result.stdout  # capture for reporting

        if not result.success:
            # Fail fast — no point running further strategies
            stderr_out = result.stderr or "\n".join(result.details)
            return False, result.stdout, stderr_out

    if not results:
        return False, "", "No test strategy was applicable for this task."

    # All applicable strategies passed
    return True, primary_stdout, ""


# ── CLI — run the module directly for quick ad-hoc testing ───────────────────

if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(
        description="Run test_runner directly against a code file and task file."
    )
    parser.add_argument("code_file", help="Python file to test")
    parser.add_argument("task_file", help="Task definition file (same format as ollama_codegen)")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--no-sandbox", action="store_true")
    args = parser.parse_args()

    # Minimal task parser (mirrors ollama_codegen.parse_task_file)
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ollama_codegen import parse_task_file
        task = parse_task_file(args.task_file)
    except ImportError:
        print("[WARN] ollama_codegen not found; using empty task dict.")
        task = {
            "expected_output": "", "input_data": "",
            "test_args": [], "inline_tests": [], "test_script": None,
        }

    code = Path(args.code_file).read_text()
    success, stdout, stderr = run_tests(
        code, task, timeout=args.timeout, sandbox=not args.no_sandbox
    )

    print(f"Result  : {'PASS' if success else 'FAIL'}")
    if stdout:
        print(f"stdout  : {stdout}")
    if stderr:
        print(f"stderr  : {stderr}")
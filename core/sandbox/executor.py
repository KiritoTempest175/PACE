"""
executor.py — Sandbox Verification Engine (Stream B / Mastery 1: Coding)

Provides a secure, isolated Python subprocess executor that runs
LLM-generated code snippets against unit tests with strict timeouts.

The Coding Critic uses this to emit a binary reward signal:
  PASS  → the generated code is functionally correct  (reward = +1)
  FAIL  → the code has runtime errors or test failures (reward = -1)

Security model:
  - Code runs in a *child* subprocess — never eval()/exec() in the parent.
  - stdout/stderr are captured; the parent process is never blocked beyond
    ``timeout`` seconds.
  - A minimal ``__builtins__`` restriction note is included in the harness
    (full sandboxing requires OS-level isolation such as Docker; see
    ``infra/docker/Dockerfile.sandbox``).
"""

import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT: int = 10        # seconds before the subprocess is killed
MAX_OUTPUT_CHARS: int = 8_000    # truncate stdout/stderr beyond this


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_code(
    code: str,
    test_code: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    python_executable: str = sys.executable,
) -> dict:
    """
    Execute *code* in an isolated subprocess, optionally appending *test_code*.

    The combined script is written to a temporary file, executed by the
    *python_executable* interpreter, and the results are returned as a dict.

    Args:
        code:               The LLM-generated Python source to execute.
        test_code:          Optional unit-test source appended after *code*.
                            Should use ``assert`` statements or ``unittest``/
                            ``pytest`` style. If provided, any ``AssertionError``
                            is treated as a FAIL.
        timeout:            Maximum wall-clock seconds allowed for execution.
        python_executable:  Path to the Python interpreter (defaults to the
                            running interpreter so the same environment is used).

    Returns:
        A dict with keys:
          - ``"status"``       : ``"pass"`` | ``"fail"`` | ``"timeout"`` | ``"error"``
          - ``"stdout"``       : captured standard output (str, truncated)
          - ``"stderr"``       : captured standard error  (str, truncated)
          - ``"return_code"``  : process exit code (int), or ``None`` on timeout
          - ``"elapsed_ms"``   : wall-clock milliseconds spent
          - ``"label"``        : 1 = pass, 0 = fail  (for Critic reward)
    """
    # Build the harness script
    harness_parts = [textwrap.dedent(code)]
    if test_code:
        harness_parts.append("\n\n# --- TEST HARNESS ---\n")
        harness_parts.append(textwrap.dedent(test_code))
    full_script = "\n".join(harness_parts)

    # Write to a temp file (auto-deleted after execution)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="pace_sandbox_",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(full_script)
        tmp_path = Path(tmp.name)

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [python_executable, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        stdout = proc.stdout[:MAX_OUTPUT_CHARS]
        stderr = proc.stderr[:MAX_OUTPUT_CHARS]
        return_code = proc.returncode

        if return_code == 0:
            status = "pass"
            label = 1
        else:
            status = "fail"
            label = 0

    except subprocess.TimeoutExpired:
        elapsed_ms = timeout * 1000
        stdout = ""
        stderr = f"Execution timed out after {timeout}s."
        return_code = None
        status = "timeout"
        label = 0

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        stdout = ""
        stderr = str(exc)
        return_code = -1
        status = "error"
        label = 0

    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
        "elapsed_ms": elapsed_ms,
        "label": label,
    }


def batch_run(
    code_test_pairs: list[tuple[str, Optional[str]]],
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """
    Run multiple (code, test_code) pairs sequentially and return a list of
    result dicts. Useful for batch evaluation during Critic training.

    Args:
        code_test_pairs: List of (code, test_code) tuples.
        timeout:         Per-execution timeout in seconds.

    Returns:
        List of result dicts as returned by :func:`run_code`.
    """
    return [run_code(code, test, timeout=timeout) for code, test in code_test_pairs]


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Sandbox Executor — Smoke Test ===\n")

    # Test 1: correct code
    result = run_code(
        code="def add(a, b): return a + b",
        test_code="assert add(2, 3) == 5\nassert add(-1, 1) == 0\nprint('Tests passed.')",
    )
    print(f"[PASS expected]  status={result['status']}  label={result['label']}")
    print(f"  stdout: {result['stdout'].strip()}")

    # Test 2: buggy code (assertion will fail)
    result = run_code(
        code="def add(a, b): return a - b",   # bug: subtraction instead of addition
        test_code="assert add(2, 3) == 5",
    )
    print(f"\n[FAIL expected]  status={result['status']}  label={result['label']}")
    print(f"  stderr: {result['stderr'].strip()[:200]}")

    # Test 3: infinite loop → timeout
    result = run_code(
        code="while True: pass",
        timeout=2,
    )
    print(f"\n[TIMEOUT expected]  status={result['status']}  label={result['label']}")

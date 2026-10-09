"""Optional isolated Docker runner. Disabled by default and on hosted deployments.

The AST filter is defense in depth, NOT the sandbox. Docker's resource,
filesystem, network and privilege restrictions form the actual isolation.
For exposure to anonymous public users, prefer a dedicated sandbox service.
"""
from __future__ import annotations

import ast
import logging
import os
import re
import subprocess
from uuid import uuid4

from core.config import get_settings

logger = logging.getLogger(__name__)


class SandboxUnavailable(RuntimeError):
    pass


class UnsafeCode(ValueError):
    pass


# Restrict imports to simple deterministic exercises. Bypasses are possible;
# the isolated container remains the security boundary.
ALLOWED_MODULES = frozenset({"math", "statistics", "itertools", "functools", "collections", "decimal", "fractions", "re", "json", "string", "heapq", "bisect"})
DISALLOWED_NAMES = frozenset({"__import__", "open", "exec", "eval", "compile", "input", "breakpoint", "globals", "locals", "vars"})


def validate_source(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise UnsafeCode("Source code is not valid Python") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".", 1)[0] not in ALLOWED_MODULES for alias in node.names):
                raise UnsafeCode("Import not permitted in restricted exercises")
        elif isinstance(node, ast.ImportFrom):
            if not node.module or node.level or node.module.split(".", 1)[0] not in ALLOWED_MODULES:
                raise UnsafeCode("Import not permitted in restricted exercises")
        elif isinstance(node, ast.Name) and node.id in DISALLOWED_NAMES:
            raise UnsafeCode("Restricted built-in in exercise")
        elif isinstance(node, ast.Attribute) and node.attr in {"__subclasses__", "__globals__", "__builtins__", "__dict__"}:
            raise UnsafeCode("Reflection not allowed")


def run_code(code: str, test_code: str | None = None, timeout: int = 8, python_executable: str | None = None) -> dict:
    settings = get_settings()
    if settings.environment != "development" or not settings.sandbox_enabled:
        raise SandboxUnavailable("Code execution is disabled in this environment")
    if python_executable is not None:
        raise SandboxUnavailable("Custom executable selection is prohibited")
    if len(code) > 20_000 or len(test_code or "") > 10_000:
        raise ValueError("Source exceeds code length limit")
    if not isinstance(timeout, int) or not 1 <= timeout <= 20:
        raise ValueError("Timeout must be 1 to 20 seconds")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.:/-]{0,100}", settings.sandbox_image):
        raise SandboxUnavailable("Invalid sandbox image name")
    source = code + "\n" + (test_code or "")
    validate_source(source)
    name = "pace-exec-" + uuid4().hex
    cmd = [
        "docker", "run", "--rm", "--interactive", "--name", name,
        "--network", "none", "--read-only", "--memory", "256m",
        "--memory-swap", "256m", "--cpus", "0.5", "--pids-limit", "32",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--user", "65534:65534", "--tmpfs", "/tmp:rw,nosuid,noexec,size=16m",
        "--ulimit", "nofile=64:64", "--ulimit", "fsize=1048576:1048576",
        settings.sandbox_image, "python", "-I", "-S", "-",
    ]
    try:
        completed = subprocess.run(
            cmd, input=source, capture_output=True, text=True, timeout=timeout + 3,
            check=False, env={"PATH": os.getenv("PATH", "/usr/bin:/bin")},
        )
    except subprocess.TimeoutExpired:
        # Killing only the docker CLI can leave a running container. Remove by
        # our generated container name; never interpolate untrusted shell text.
        try:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=5, check=False)
        except (OSError, subprocess.SubprocessError):
            logger.warning("Could not remove expired sandbox container %s", name)
        return {"status": "timeout", "stdout": "", "stderr": "Time limit exceeded", "return_code": None, "label": 0}
    except (OSError, subprocess.SubprocessError) as exc:
        raise SandboxUnavailable("Docker sandbox is not available") from exc
    return {
        "status": "pass" if completed.returncode == 0 else "fail",
        "stdout": completed.stdout[:8000], "stderr": completed.stderr[:8000],
        "return_code": completed.returncode,
        "label": int(completed.returncode == 0),
    }


def batch_run(code_test_pairs: list[tuple[str, str | None]], timeout: int = 8) -> list[dict]:
    if len(code_test_pairs) > 10:
        raise ValueError("Batch limit exceeded")
    return [run_code(code, tests, timeout) for code, tests in code_test_pairs]

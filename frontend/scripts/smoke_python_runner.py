"""Production-built Vite runner in a real headless Chromium browser.

This tests the self-hosted WASM runtime (no CDN at runtime), actual Python
execution, exception handling, and timeout / worker cancellation.
"""
from __future__ import annotations
import os
import sys
from playwright.sync_api import sync_playwright

BASE = os.getenv("PACE_WEB_URL", "http://127.0.0.1:4173")
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page()
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until="domcontentloaded",timeout=30000)
    details=page.locator(".coding-tools details")
    details.locator("summary").click()
    editor=page.locator("#sandbox-code")
    editor.fill('print("PACE-PYTHON-RUNNER-OK")\nprint(6 * 7)')
    page.get_by_role("button",name="Run Python").click()
    page.get_by_text("Result: success").wait_for(timeout=150000)
    content=page.locator(".runner-output pre").inner_text()
    assert "PACE-PYTHON-RUNNER-OK" in content, content
    assert "42" in content,content
    print("PASS: bundled Pyodide executes Python in production React build",flush=True)

    editor.fill("raise ValueError('EXCEPTION-OK')")
    page.get_by_role("button",name="Run Python").click()
    page.get_by_text("Result: error").wait_for(timeout=30000)
    assert "EXCEPTION-OK" in page.locator(".runner-output pre").inner_text()
    print("PASS: Python exceptions rendered, not treated as success",flush=True)

    editor.fill("while True: pass")
    page.get_by_role("button",name="Run Python").click()
    page.get_by_text("Result: timeout").wait_for(timeout=25000)
    print("PASS: runaway Python worker terminates after timeout",flush=True)

    editor.fill('print("RECOVERED")')
    page.get_by_role("button",name="Run Python").click()
    page.get_by_text("Result: success").wait_for(timeout=30000)
    assert "RECOVERED" in page.locator(".runner-output pre").inner_text()
    print("PASS: worker recreated after timeout; subsequent runs work",flush=True)
    assert not errors,errors
    browser.close()

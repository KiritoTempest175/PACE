"""Smoke test actual installed Tauri WebView2 UI through the CDP debugging port."""
import json,time,urllib.request
from playwright.sync_api import sync_playwright
CDP="http://127.0.0.1:9222"
for attempt in range(50):
    try:
        with urllib.request.urlopen(CDP+"/json/version",timeout=2) as res:
            if "webSocketDebuggerUrl" in res.read().decode():break
    except Exception as exc:
        if attempt%10==0: print("Waiting for WebView2:",repr(exc),flush=True)
    time.sleep(2)
else:raise RuntimeError("WebView2 CDP debugger unavailable after 100 seconds")
with sync_playwright() as p:
    browser=p.chromium.connect_over_cdp(CDP,timeout=20000)
    print("CDP pages:",[x.url for c in browser.contexts for x in c.pages],flush=True)
    matches=[x for c in browser.contexts for x in c.pages if "tauri.localhost" in x.url.lower()]
    if not matches:raise RuntimeError("Installed Tauri WebView2 page is missing")
    page=matches[0]
    page.on("pageerror",lambda e:print("JS error:",e,flush=True))
    page.locator("h1").wait_for(timeout=30000)
    page.get_by_text("API online").wait_for(timeout=45000)
    assert page.locator("h1").inner_text()=="Coding"
    print("PASS: Tauri React interface and bundled backend health",flush=True)
    page.locator("#prompt").fill("Say hi")
    page.get_by_role("button",name="Send message").click()
    page.get_by_text("PACE desktop local integration test passed").wait_for(timeout=45000)
    print("PASS: React -> packaged Python API -> test-only Ollama protocol -> React",flush=True)
    for label in ("Research","Literacy","Coding"):
        page.get_by_role("button",name=label,exact=True).click()
        assert page.locator("h1").inner_text()==label
    print("PASS: all three workspaces preserved",flush=True)
    page.get_by_role("button",name="Settings",exact=True).click()
    page.get_by_text("Desktop backend").wait_for(timeout=10000)
    print("PASS: desktop preferences available",flush=True)
    browser.close()

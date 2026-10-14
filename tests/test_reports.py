"""Real browser and HTTP fixtures; no Semrush credentials or external requests."""

import asyncio
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from patchright.async_api import async_playwright

from semrush_web_mcp.server import REPORTS, BrowserSession, SemrushError


@contextmanager
def website():
    calls = []
    state = {"fail_method": None}

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            if self.path == "/home/" and "session=fixture-session" not in self.headers.get(
                "Cookie", ""
            ):
                self.send_response(302)
                self.send_header("Location", "/")
            else:
                self.send_response(200)
            self.end_headers()

        def do_GET(self):
            if self.path.startswith("/analytics/overview/"):
                body = b"""<div role="menuitem">My profile</div><script>
                fetch('/dpa/rpc', {method:'POST',headers:{'Content-Type':'application/json'},
                body:JSON.stringify({id:1,jsonrpc:'2.0',method:'user.Databases',
                params:{apiKey:'fixture-only-key',userId:7}})});
                </script>"""
            else:
                body = b"<html>fixture</html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, payload, self.headers.get("Cookie", "")))
            method = payload["method"]
            if method == state["fail_method"]:
                response = {"error": {"code": 403, "message": "Limit for fixture-only-key reached"}}
            elif method == "keywords.GetInfo":
                response = {
                    "result": {
                        "keywords": [
                            {"database": "gb", "volume": 100},
                            {"database": "us", "volume": 33100, "identifier": 14456231459620808652},
                        ]
                    }
                }
            elif method == "organic.Summary":
                response = {
                    "result": [
                        {"database": "gb", "organicTraffic": 1},
                        {"database": "us", "organicTraffic": 500},
                    ]
                }
            elif method == "backlinks.Summary":
                response = {"result": {"authorityScore": 96, "backlinks": 70000000}}
            elif method in ("user.GetInfo", "backlinks.Overview", "organic.AiSeoSummary"):
                response = {"result": {"available": True}}
            else:
                response = {"result": [{"position": i} for i in range(1, 21)]}
            response.update(id=payload["id"], jsonrpc="2.0")
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls, state
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


async def run_in_browser(origin, scenario):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies([{"name": "session", "value": "fixture-session", "url": origin}])
        session = BrowserSession(context=context, origin=origin)
        try:
            await scenario(session, context)
        finally:
            await session.close()
            assert context.pages == []
            await browser.close()


def test_all_reports_use_authenticated_browser_endpoints():
    with website() as (origin, calls, _state):

        async def scenario(session, context):
            for name in REPORTS:
                arguments = (
                    {"domain": "openai.com"}
                    if name.startswith("domain_")
                    else {}
                    if name == "account_status"
                    else {"keyword": "email marketing"}
                )
                if "limit" in REPORTS[name].query.model_fields:
                    arguments["limit"] = 3
                response = await session.report(name, arguments)
                assert response["authenticated"] and response["report"] == name
                assert "fixture-only-key" not in json.dumps(response)
                if name == "keyword_overview":
                    assert response["data"]["volume"] == 33100
                    assert response["data"]["identifier"] == 14456231459620808652
                elif name == "domain_overview":
                    assert response["data"]["search"]["organicTraffic"] == 500
                    assert response["data"]["backlinks"]["authorityScore"] == 96
                elif "limit" in arguments:
                    assert len(response["data"]) == 3

        asyncio.run(run_in_browser(origin, scenario))
        for path, payload, cookies in calls:
            assert "session=fixture-session" in cookies
            if path == "/dpa/rpc":
                assert payload["params"]["apiKey"] == "fixture-only-key"
                assert payload["params"]["userId"] == 7
                if payload["method"] != "user.Databases":
                    assert payload["params"]["request_id"]
        assert {payload["method"] for _, payload, _ in calls} >= {
            r.method for r in REPORTS.values()
        }


def test_expired_session_stops_before_a_report_request():
    with website() as (origin, calls, _state):

        async def scenario(session, context):
            await session.report("account_status", {})
            before = len(calls)
            await context.clear_cookies()
            with pytest.raises(SemrushError, match="session expired"):
                await session.report("keyword_overview", {"keyword": "email marketing"})
            assert len(calls) == before

        asyncio.run(run_in_browser(origin, scenario))


def test_provider_errors_redact_authentication_fields():
    with website() as (origin, _calls, state):
        state["fail_method"] = "backlinks.Overview"

        async def scenario(session, context):
            with pytest.raises(SemrushError, match="403 Limit for \\[redacted\\] reached"):
                await session.report("domain_backlinks", {"domain": "openai.com"})

        asyncio.run(run_in_browser(origin, scenario))

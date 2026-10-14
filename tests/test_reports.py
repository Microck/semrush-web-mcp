"""Real browser and HTTP fixtures; no Semrush credentials or external requests."""

import asyncio
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest
from patchright.async_api import async_playwright

from semrush_web_mcp.server import REPORTS, BrowserSession, SemrushError


@contextmanager
def website():
    calls = []
    state = {"fail_method": None, "backlink_initializations": set()}

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
            if self.path.startswith("/analytics/keywordgap/"):
                body = b"""<script>fetch('/spectrum/v1/Meta/UserPermissions', {method:'POST',
                headers:{'Authorization':'Bearer fixture-gap-token','x-report':'gap.keywords',
                'Content-Type':'application/json'},body:JSON.stringify({database:'us'})});</script>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path.startswith(
                ("/analytics/backlinks/", "/siteaudit/api/", "/apis/", "/ai-seo/api/")
            ):
                calls.append((self.path, None, self.headers.get("Cookie", "")))
                if "/overview/" in self.path:
                    request_id = self.headers.get("x-request-id")
                    if urlsplit(self.path).path.endswith("/init"):
                        assert request_id
                        state["backlink_initializations"].add(request_id)
                    else:
                        assert request_id in state["backlink_initializations"]

                body = json.dumps(
                    {
                        "status": "SUCCESS",
                        "total": 1000,
                        "data": [
                            {"url": "https://example.com/7", "identifier": 14456231459620808652}
                        ],
                        "key": "fixture-only-key",
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
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
            if "method" not in payload:
                if self.path.startswith("/spectrum/"):
                    assert self.headers.get("Authorization") == "Bearer fixture-gap-token"
                    assert self.headers.get("x-report") == "gap.keywords"

                body = b'{"lists": []}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
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
                fields = REPORTS[name].query.model_fields
                arguments = {}
                if "domain" in fields:
                    arguments["domain"] = "openai.com"
                if "keyword" in fields:
                    arguments["keyword"] = "email marketing"
                if "domains" in fields:
                    arguments["domains"] = ["openai.com", "anthropic.com"]
                if "limit" in REPORTS[name].query.model_fields:
                    arguments["limit"] = 3
                response = await session.report(name, arguments)
                assert response["authenticated"] and response["report"] == name
                assert "fixture-only-key" not in json.dumps(response)
                assert "fixture-gap-token" not in json.dumps(response)
                if name == "keyword_overview":
                    assert response["data"]["volume"] == 33100
                    assert response["data"]["identifier"] == 14456231459620808652
                elif name == "domain_overview":
                    assert response["data"]["search"]["organicTraffic"] == 500
                    assert response["data"]["backlinks"]["authorityScore"] == 96
                elif "limit" in arguments and isinstance(response["data"], list):
                    assert len(response["data"]) == 3

        asyncio.run(run_in_browser(origin, scenario))
        for path, payload, cookies in calls:
            assert "session=fixture-session" in cookies
            if path == "/dpa/rpc":
                assert payload["params"]["apiKey"] == "fixture-only-key"
                assert payload["params"]["userId"] == 7
                if payload["method"] not in ("user.Databases", "organic.SnapshotDates"):
                    assert payload["params"]["request_id"]
        assert {
            payload["method"] for _, payload, _ in calls if payload and "method" in payload
        } >= {
            r.method
            for r in REPORTS.values()
            if r.transport in ("keyword", "magic", "domain", "direct")
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


def test_full_reports_preserve_pagination_filters_totals_and_auth_privacy():
    with website() as (origin, calls, _state):

        async def scenario(session, context):
            rankings = await session.report(
                "domain_keywords",
                {
                    "domain": "openai.com",
                    "page": 2,
                    "page_size": 20,
                    "database": "mobile-us",
                    "date": 1789430400,
                    "date_type": "monthly",
                    "filters": {"phrase": [{"value": "chat"}]},
                },
            )
            assert rankings["data"]["page"] == 2
            assert "rows" in rankings["data"] and "total" in rankings["data"]
            await session.report(
                "keyword_magic",
                {
                    "keyword": "seo",
                    "page": 3,
                    "page_size": 25,
                    "questions_only": True,
                    "filters": {"volume": [{"from": 100}]},
                },
            )
            links = await session.report("backlink_links", {"domain": "openai.com", "page": 2})
            assert links["data"]["total"] == 1000
            assert links["data"]["data"][0]["url"] == "https://example.com/7"
            assert links["data"]["data"][0]["identifier"] == 14456231459620808652
            assert "key" not in links["data"]
            await session.report(
                "backlink_gap", {"domains": ["openai.com", "anthropic.com"], "page": 1, "limit": 20}
            )

        asyncio.run(run_in_browser(origin, scenario))
        positions = next(
            payload
            for _, payload, _ in calls
            if payload and payload.get("method") == "organic.Positions"
        )
        assert positions["params"]["report"] == "organic.positions"
        assert positions["params"]["args"]["database"] == "mobile-us"
        assert positions["params"]["args"]["date"] == 1789430400
        assert positions["params"]["args"]["dateType"] == "monthly"
        assert positions["params"]["args"]["display"] == {
            "page": 2,
            "pageSize": 20,
            "order": {"field": "trafficPercent", "direction": "desc"},
        }
        assert positions["params"]["args"]["filter"] == {"phrase": [{"value": "chat"}]}
        magic = next(payload for path, payload, _ in calls if path == "/kmtgw/v2/webapi")
        assert magic["params"]["page"] == {"number": 3, "size": 25}
        assert magic["params"]["questions_only"] is True
        assert magic["params"]["filter"]["volume"] == [{"from": 100}]
        link_path = next(path for path, _, _ in calls if path.startswith("/analytics/backlinks/"))
        params = parse_qs(urlsplit(link_path).query)
        assert params["display_page"] == ["2"]
        assert params["key"] == ["fixture-only-key"]
        matrix_path = next(path for path, _, _ in calls if "type=backlinks_matrix" in path)
        matrix_params = parse_qs(urlsplit(matrix_path).query)
        assert matrix_params["targets[]"] == ["openai.com", "anthropic.com"]
        assert matrix_params["target_types[]"] == ["root_domain", "root_domain"]
        assert matrix_params["display_page"] == ["1"]

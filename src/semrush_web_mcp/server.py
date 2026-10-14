"""Read Semrush reports through a signed-in Chromium context."""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from patchright.async_api import Error as BrowserError
from patchright.async_api import async_playwright
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SemrushError(Exception):
    """A report cannot be read without changing account or authentication state."""


class EmptyQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class KeywordQuery(EmptyQuery):
    keyword: str = Field(min_length=1, max_length=200)
    database: str = Field(default="us", pattern="^[a-z]{2}$")


class KeywordListQuery(KeywordQuery):
    limit: int = Field(default=10, ge=1, le=100)


class IdeasQuery(KeywordListQuery):
    questions_only: bool = False


class DomainQuery(EmptyQuery):
    domain: str = Field(min_length=1, max_length=253, description="Bare domain, e.g. openai.com")
    database: str = Field(default="us", pattern="^[a-z]{2}$")


class DomainListQuery(DomainQuery):
    limit: int = Field(default=5, ge=1, le=10)


@dataclass(frozen=True)
class Report:
    method: str
    query: type[BaseModel]
    description: str


REPORTS = {
    "account_status": Report("user.GetInfo", EmptyQuery, "Signed-in account and report limits."),
    "keyword_overview": Report(
        "keywords.GetInfo", KeywordQuery, "Volume, difficulty, CPC, intent and trends."
    ),
    "keyword_ideas": Report(
        "ideas.GetKeywords", IdeasQuery, "Related keywords or questions, with metrics."
    ),
    "keyword_serp": Report("serp.GetURLs", KeywordListQuery, "Ranked URLs and SERP features."),
    "keyword_ads": Report("adwords.GetCopies", KeywordListQuery, "Search ad copies for a keyword."),
    "keyword_clusters": Report("clusters.Get", KeywordQuery, "Keyword topics and search intents."),
    "domain_overview": Report(
        "organic.Summary", DomainQuery, "Search metrics and backlink summary."
    ),
    "domain_keywords": Report(
        "organic.PositionsOverview", DomainListQuery, "Top-ten organic keyword sample."
    ),
    "domain_competitors": Report(
        "organic.CompetitorsOverview", DomainListQuery, "Organic search competitors."
    ),
    "domain_backlinks": Report(
        "backlinks.Overview", DomainQuery, "Backlink summary, sample links and anchors."
    ),
    "domain_ai_visibility": Report(
        "organic.AiSeoSummary", DomainQuery, "AI visibility, mentions and citations."
    ),
}

# Only fixed report methods above are exposed. Callers cannot supply a URL,
# JavaScript, RPC method, auth fields or account-changing operation.
FETCH_RPC = """async ({path, payload}) => {
    const response = await fetch(path, {
        method: 'POST', credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload), signal: AbortSignal.timeout(45000)
    });
    if (!response.ok) return {status: response.status};
    return {status: response.status, text: await response.text()};
}"""
CHECK_AUTH = """async () => {
    const response = await fetch('/home/', {
        method: 'HEAD', credentials: 'include', cache: 'no-store',
        signal: AbortSignal.timeout(15000)
    });
    return response.ok && new URL(response.url).pathname === '/home/';
}"""


class BrowserSession:
    def __init__(
        self, cdp_url="http://127.0.0.1:9234", *, context=None, origin="https://www.semrush.com"
    ):
        self.cdp_url = cdp_url
        self.origin = origin
        self.context = context
        self.page = None
        self.playwright = None
        self.auth = {}
        self.lock = asyncio.Lock()

    async def connect(self):
        if self.page is not None and not self.page.is_closed():
            return
        if self.context is None:
            self.playwright = await async_playwright().start()
            try:
                browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            except BrowserError:
                await self.close()
                raise SemrushError(
                    "Semrush browser unavailable. Run semrush-web-mcp setup."
                ) from None
            self.context = browser.contexts[0]
        self.page = await self.context.new_page()
        ready = asyncio.Event()

        def observe(request):
            if request.url.split("?")[0] != self.origin + "/dpa/rpc":
                return
            try:
                payload = request.post_data_json
            except (ValueError, BrowserError):
                return
            for item in payload if isinstance(payload, list) else [payload]:
                params = item.get("params", {})
                if params.get("apiKey") and params.get("userId"):
                    # Page-owned auth stays in memory and never enters tool results.
                    self.auth = {key: params[key] for key in ("apiKey", "userId")}
                    ready.set()

        self.page.on("request", observe)
        try:
            await self.page.goto(
                self.origin + "/analytics/overview/?db=us",
                wait_until="domcontentloaded",
                timeout=45000,
            )
            await self.page.get_by_role("menuitem", name="My profile", exact=True).wait_for(
                timeout=15000
            )
            await asyncio.wait_for(ready.wait(), timeout=15)
        except (BrowserError, TimeoutError):
            await self.close()
            raise SemrushError("Semrush sign-in required. Run semrush-web-mcp login.") from None
        # Keep the authenticated origin without running the dashboard's charts,
        # telemetry and polling in every MCP process.
        await self.page.goto(self.origin + "/robots.txt", wait_until="domcontentloaded")

    async def check_auth(self):
        if not await self.page.evaluate(CHECK_AUTH, isolated_context=False):
            await self.close()
            raise SemrushError(
                "Semrush session expired. Run semrush-web-mcp login, then reconnect MCP."
            )

    async def rpc(self, method, params, *, domain=False):
        path = "/dpa/rpc" if domain else "/kwogw/v2/webapi"
        if domain:
            params = {
                "request_id": str(uuid.uuid4()),
                "report": "domain.overview",
                "args": params,
                **self.auth,
            }
        response = await self.page.evaluate(
            FETCH_RPC,
            {
                "path": path,
                "payload": {"id": 1, "jsonrpc": "2.0", "method": method, "params": params},
            },
            isolated_context=False,
        )
        if response["status"] != 200:
            raise SemrushError(f"Semrush {method}: HTTP {response['status']}")
        try:
            # Parse outside JavaScript so 64-bit report identifiers stay exact.
            body = json.loads(response["text"])
        except ValueError:
            raise SemrushError(
                f"Semrush {method}: expected JSON, received a page or challenge"
            ) from None
        if "error" in body:
            error = body["error"]
            message = str(error.get("message", "Report failed"))
            for secret in self.auth.values():
                message = message.replace(str(secret), "[redacted]")
            raise SemrushError(f"Semrush {method}: {error.get('code')} {message[:500]}")
        if "result" not in body:
            raise SemrushError(f"Semrush {method}: missing report result")
        return body["result"]

    async def report(self, name, arguments):
        if name not in REPORTS:
            raise SemrushError(f"Unknown report: {name}")
        definition = REPORTS[name]
        query = definition.query.model_validate(arguments).model_dump()
        async with self.lock:
            await self.connect()
            await self.check_auth()
            domain = name.startswith("domain_")
            if domain:
                params = {
                    "searchItem": query["domain"],
                    "searchType": "domain",
                    "database": query["database"],
                    "dateFormat": "date",
                    "dateType": "daily",
                }
                if name in ("domain_backlinks", "domain_ai_visibility"):
                    params.pop("database")
                if name == "domain_keywords":
                    params["positionsType"] = "all"
                if name == "domain_competitors":
                    params.update(display={"page": 1, "pageSize": query["limit"]}, youDomain=True)
            elif name == "account_status":
                params = {}
            else:
                params = {
                    "phrase": query["keyword"],
                    "database": query["database"],
                    "device": 0,
                    "currency": "USD",
                    "location": 0,
                    "date": "",
                }
                if name == "keyword_ideas":
                    params.update(mode=0, questions_only=query["questions_only"])
            result = await self.rpc(definition.method, params, domain=domain)
            if name == "keyword_overview":
                matches = [
                    item for item in result["keywords"] if item["database"] == query["database"]
                ]
                if not matches:
                    raise SemrushError("No keyword data for the selected database")
                result = matches[0]
            elif name == "domain_overview":
                metrics = [item for item in result if item["database"] == query["database"]]
                if not metrics:
                    raise SemrushError("No domain data for the selected database")
                backlinks = await self.rpc(
                    "backlinks.Summary",
                    {
                        "searchItem": query["domain"],
                        "searchType": "domain",
                    },
                    domain=True,
                )
                result = {"search": metrics[0], "backlinks": backlinks}
            if "limit" in query and isinstance(result, list):
                result = result[: query["limit"]]
            return {"authenticated": True, "report": name, "data": result}

    async def close(self):
        if self.page is not None and not self.page.is_closed():
            await self.page.close()
        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None
            self.context = None
        self.page = None
        self.auth.clear()


def create_server(session):
    tools = [
        types.Tool(
            name=name,
            description=f"Authenticated Semrush web report. {report.description}",
            inputSchema=report.query.model_json_schema(),
            annotations=types.ToolAnnotations(readOnlyHint=True, openWorldHint=True),
        )
        for name, report in REPORTS.items()
    ]

    async def list_tools(ctx, params):
        return types.ListToolsResult(tools=tools)

    async def call_tool(ctx, params):
        try:
            result = await session.report(params.name, params.arguments or {})
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(result))]
            )
        except (SemrushError, ValidationError) as error:
            message = str(error)
        except Exception:  # noqa: BLE001 - the MCP boundary must not leak browser details
            # Browser exceptions can include request details. Do not print them.
            message = "Semrush browser request failed. Check the browser service and reconnect MCP."
        return types.CallToolResult(
            isError=True, content=[types.TextContent(type="text", text=message)]
        )

    @asynccontextmanager
    async def lifespan(server):
        try:
            yield {}
        finally:
            await session.close()

    return Server(
        "semrush-web-mcp",
        version="0.1.0",
        lifespan=lifespan,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def serve(cdp_url):
    server = create_server(BrowserSession(cdp_url))
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())

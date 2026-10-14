"""Exercise the installed stdio entry point and its trust boundary."""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from semrush_web_mcp.server import REPORTS


def test_stdio_discovery_validation_and_missing_browser():
    async def scenario():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[
                "-m",
                "semrush_web_mcp.cli",
                "serve",
                "--cdp-url",
                "http://127.0.0.1:1",
            ],
        )
        async with (
            stdio_client(parameters) as (reader, writer),
            ClientSession(reader, writer, read_timeout_seconds=30) as session,
        ):
            initialized = await session.initialize()
            assert initialized.server_info.name == "semrush-web-mcp"
            catalog = await session.list_tools()
            assert {tool.name for tool in catalog.tools} == set(REPORTS)
            assert all("Authenticated" in tool.description for tool in catalog.tools)
            for name, arguments in [
                ("keyword_overview", {}),
                ("keyword_overview", {"keyword": ""}),
                ("keyword_overview", {"keyword": "seo", "url": "https://example.com"}),
                ("keyword_ideas", {"keyword": "seo", "limit": 1000}),
                ("unknown", {}),
            ]:
                response = await session.call_tool(name, arguments)
                assert response.is_error
                assert "browser unavailable" not in json.dumps(response.model_dump())
            response = await session.call_tool("account_status", {})
            assert response.is_error
            assert "browser unavailable" in response.content[0].text

    asyncio.run(scenario())

# semrush-web-mcp

An MCP server that reads Semrush through your signed-in browser session.

11 tools for keyword metrics, ideas, SERP results, ads, clusters, domain
overview, organic keywords, competitors, backlinks and AI visibility.
Requests run inside Chromium with your existing account session.
No Semrush developer API key or CAPTCHA service is required.

## Install

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and Chromium.
The managed browser setup below requires Linux with a systemd user session.

```sh
git clone https://github.com/Microck/semrush-web-mcp
cd semrush-web-mcp
uv sync --no-dev
uv run --no-dev python -m patchright install chromium
uv run --no-dev semrush-web-mcp setup
uv run --no-dev semrush-web-mcp login
```

Sign into Semrush in the visible browser, then close that window. The
background browser resumes using the same private profile. `login` requires
a graphical desktop. On a headless machine, use a browser automation client
connected to the service's localhost CDP port to complete the login.

To use an existing dedicated Chromium profile:

```sh
uv run --no-dev semrush-web-mcp setup --profile /absolute/path/to/private-profile
```

Close any browser already using that profile before setup. The service
uses port 9234 by default. `setup --port PORT` selects another port.

## Connect an MCP client

Use the installed executable's absolute path:

```json
{
  "mcpServers": {
    "semrush-web": {
      "command": "/absolute/path/to/semrush-web-mcp/.venv/bin/semrush-web-mcp",
      "args": ["serve"],
      "timeout": 120000
    }
  }
}
```

This also works in OMP's `~/.omp/agent/mcp.json`. Restart or reconnect the
client after replacing an existing Semrush server.

For an existing browser managed elsewhere, including on other operating
systems, use `serve --cdp-url http://127.0.0.1:9234`. It must contain a
signed-in Semrush session. Keep CDP on localhost or behind SSH forwarding.

## Tools

| Tool | Inputs | Returns |
| --- | --- | --- |
| `account_status` | None | Session confirmation and account report limits |
| `keyword_overview` | `keyword`, `database` | Volume, difficulty, CPC, intent and trends |
| `keyword_ideas` | `keyword`, `database`, `questions_only`, `limit` | Related keywords or questions |
| `keyword_serp` | `keyword`, `database`, `limit` | Ranked URLs and SERP features |
| `keyword_ads` | `keyword`, `database`, `limit` | Search ad copies |
| `keyword_clusters` | `keyword`, `database` | Related topics and intents |
| `domain_overview` | `domain`, `database` | Organic/paid search metrics and backlink summary |
| `domain_keywords` | `domain`, `database`, `limit` | Top-ten organic keyword sample |
| `domain_competitors` | `domain`, `database`, `limit` | Organic competitors |
| `domain_backlinks` | `domain`, `database` | Backlink overview, sample links and anchors |
| `domain_ai_visibility` | `domain`, `database` | AI visibility, mentions and citations |

`database` defaults to `us`. Keyword list limits default to 10, with a
maximum of 100. Domain list limits default to 5, with a maximum of 10.
Some domain reports are worldwide even when the common query schema
includes a database. The server preserves the web endpoint's result.

Example prompt:

> Use keyword_overview for "email marketing" in the US database, then show
> five related keyword ideas and the leading search results.

Every successful result includes `authenticated: true`, `report` and `data`.
Unknown inputs, expired sessions and Semrush errors return MCP errors.

## How it works

One private Chromium service owns the persistent login profile. Each MCP
process connects through CDP and opens its own page. It observes the
domain app's authentication parameters, then calls the same read endpoints
as the signed-in website using browser `fetch` and session cookies.

The report page moves to a lightweight same-origin document after startup,
so it does not leave dashboard charts and background polling running.
The MCP closes its page on disconnect and leaves the shared browser service
available for other clients.

The server checks authentication before every report. It does not fall
back to anonymous scraping, export cookies, automatically log in, create
projects, refresh paid data, or submit CAPTCHA tasks. It can still consume
normal account report allowances. Semrush account limits and permissions
apply. The endpoints are internal web APIs and may change.

See [the report contract](docs/contracts.md) for the observed endpoints.

## Local state and recovery

Configuration and the default browser profile live under
`~/.config/semrush-web-mcp/`, outside the checkout. The directory is private
to its owner. Treat the browser profile as a credential.

```sh
systemctl --user status semrush-web-browser.service
systemctl --user restart semrush-web-browser.service
systemctl --user stop semrush-web-browser.service
```

If the session expires, run `semrush-web-mcp login` again and reconnect your
MCP client. On headless hosts, sign in through your CDP client instead.
Account limits require waiting for a reset or changing your Semrush plan.

## Development and verification

```sh
uv sync
uv run python -m patchright install --with-deps chromium
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Tests use a real Chromium browser, a local HTTP fixture and the real MCP
stdio subprocess. They cover all report mappings, session expiry, input
validation, credential redaction, exact 64-bit identifiers and page cleanup.
They require no Semrush account and make no external report requests.

All 11 tools also passed live authenticated MCP calls on October 14, 2026.
For example, `keyword_overview` returned US volume 33,100, difficulty 79 and
CPC $29.59 for "email marketing". Live checks are separate from fixture tests.

## License

MIT. This is an independent project, not an official Semrush integration.

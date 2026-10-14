# semrush-web-mcp

An MCP server that reads Semrush through your signed-in browser session.

48 read operations for keyword research, organic rankings, competitors,
keyword and backlink gaps, backlinks, historical/mobile research and AI
visibility. Every MCP operation also has a native CLI command.
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

To put the CLI command on your PATH, run `uv tool install .` from the checkout.

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

## MCP and CLI operations

Both interfaces use the same [operation catalog](docs/tool-catalog.md) and
input schemas. List commands and schemas locally:

```sh
semrush-web-mcp reports
semrush-web-mcp reports --json
semrush-web-mcp domain-keywords --help
```

| Research area | Operations |
| --- | --- |
| Keywords | Metrics, ideas/questions, SERPs, ads, clusters, paginated Keyword Magic and groups |
| Organic search | Full rankings, top pages, subdomains, changes, competitors, topics and trends |
| Gaps | Organic keyword overlaps and gaps, backlink prospects and profile comparisons |
| Links | Full backlinks, referring domains, anchors, indexed pages, outbound domains, history and authority |
| GEO | Domain AI visibility, mentions, citation sources and country distribution |
| Account data | Permissions, databases, snapshot dates, projects, folders, saved lists and audit campaigns |

MCP names use underscores. CLI commands and flags use hyphens.
For array and object flags, supply JSON. For example:

```sh
semrush-web-mcp keyword-overview --keyword 'email marketing' --json
semrush-web-mcp keyword-magic --keyword 'email marketing' --questions-only --page 2 --page-size 20 --json
semrush-web-mcp domain-keywords --domain openai.com --page 2 --page-size 20 --json
semrush-web-mcp domain-keywords --domain openai.com --database mobile-us --date 1789430400 --date-type monthly --json
semrush-web-mcp keyword-gap --domains '["openai.com","anthropic.com"]' --json
semrush-web-mcp backlink-gap --domains '["openai.com","anthropic.com"]' --json
semrush-web-mcp backlink-links --domain openai.com --filters '+|type||nofollow' --json
```

`database` defaults to `us`. Domain research also accepts mobile databases
such as `mobile-us`. Obtain historical timestamps from `snapshot-dates`.
Keyword Magic and organic report pages start at 1. Backlink pages start at 0.
Gap queries use `offset` or a zero-based backlink page, as shown in their help.
Provider caps and totals remain visible. There is no unlimited-export claim.
Redirect JSON output to a local file with the shell when needed.

Every successful result includes `authenticated: true`, `report` and `data`.
Unknown inputs, expired sessions and Semrush errors return MCP errors or a
nonzero CLI exit. See [coverage and account restrictions](docs/feature-parity.md).

## How it works

One private Chromium service owns the persistent login profile. Each MCP
process connects through CDP and opens its own page. It reads the signed-in
page's bootstrap JSON without rendering the dashboard and, when needed,
observes the keyword gap app's authorization token. It calls the same read endpoints
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

See [verification evidence](docs/verification.md) for live authenticated
checks, pagination, native CLI calls and the automated test boundary.

## License

MIT. This is an independent project, not an official Semrush integration.

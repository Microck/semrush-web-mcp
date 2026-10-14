# Verification

Verified on October 14, 2026 on Linux ARM64 with Python 3.14.

## Local checks

- `uv run pytest -q`: four tests passed. The browser fixture exercises all
  11 report mappings, cookies, per-call authentication, expiry rejection,
  credential redaction, large integer preservation and page cleanup.
- The stdio test starts the installed CLI and checks discovery, invalid
  inputs, unknown reports and a missing browser without contacting Semrush.
- Ruff lint and formatting checks passed.
- Wheel and source distribution builds passed.
- No separate static type checker is configured.

## Live evidence

All 11 tools returned authenticated data through a real stdio MCP client.
Queries used `email marketing` and `openai.com`. The account's authenticated
browser context supplied the session; no developer API key or CAPTCHA
service was used. This does not establish access beyond that account's plan.

OMP then independently called `account_status` and `keyword_overview` through
its configured replacement server. It returned authenticated status and
US keyword volume 33,100, difficulty 79 and CPC $29.59.

The private Linux browser service remained signed in after a restart.
The setup command was rerun successfully after the service reconfiguration
fix. Live tests do not run in CI and no account credentials are in this repo.

## Review

The simplification pass applied two efficiency changes: build the fixed
tool catalog once and read the config without a separate existence check.
It found no reuse changes. One correctness fix makes repeated setup restart
the browser service so new settings take effect.

Publishable source, wheel and source archives were checked for credentials.
Private browser state, login credentials and provider keys are outside the
checkout and excluded from the artifacts.

# Verification

Verified on October 14, 2026 on Linux ARM64 with Python 3.14.

## Automated checks

- Eleven tests pass. They use real Chromium, a local HTTP fixture, CLI processes
  and a real MCP stdio subprocess. No test mocks modules or makes external
  Semrush requests.
- The browser fixture exercises all 48 operation mappings, cookies, per-call
  authentication, session expiry, credential redaction, exact 64-bit IDs and
  owned-page cleanup.
- It checks full report pagination, totals, historical/mobile arguments,
  filters, repeated target query parameters, Spectrum authorization and
  backlink initialization with the same request ID.
- CLI discovery matches the MCP catalog and schemas. CLI help, JSON-array
  validation, invalid inputs and missing-browser errors are covered.
- Ruff lint and formatting pass. Wheel and source distribution builds pass.
  No separate static type checker is configured.

A concurrent local run hit host memory pressure and timed out in two checks.
The serial rerun passed all ten tests in that build without changing their timeouts or
weakening assertions.

## Live authenticated checks

All 48 operations passed calls through a real stdio MCP client using
`email marketing`, `openai.com` and `anthropic.com`. Every result confirmed
`authenticated: true`. Domain topics returned provider status `ready`.
An empty campaign/list response confirms access, not populated project data.
No developer API key, anonymous free-tools API or CAPTCHA service was used.

Representative full report totals for `openai.com` in the US database:

| Report | Provider total |
| --- | ---: |
| Organic rankings | 1,329,896 |
| Organic top pages | 46,332 |
| Position changes | 81,571 |

Two distinct pages returned different nonempty records for organic rankings,
Keyword Magic, backlinks and Keyword Gap. Backlink pages returned 100 rows;
the other pagination probes used three rows per page.

Native CLI calls also passed for Keyword Gap, Backlink Gap, AI capabilities,
and September 2026 mobile-US rankings. The historical/mobile call returned
62,393 total rankings and three requested rows.

The 0.2.1 startup change reads the signed-in page's serialized user JSON
instead of rendering the Domain Overview dashboard. Live inspection confirmed
that its API key and user ID exactly match the web RPC authentication values.
The additional fixture test rejects missing authenticated bootstrap metadata.

After recovering the private browser service from host resource exhaustion,
a fresh OMP run using the installed 0.2.1 command completed both requests:

| OMP operation | Authenticated | Rows returned |
| --- | --- | ---: |
| Organic rankings, page 2 | Yes | 2 |
| Backlink Gap | Yes | 2 |

Earlier OMP runs timed out during host memory pressure. Their failures are
not counted as successes. The browser restart retained the authenticated
profile. Other MCP configuration entries were unchanged.

These checks establish access only for the tested account and queries.
They do not establish all databases, filter combinations or paid products.
Live account checks do not run in CI. Account restrictions and remaining
web parity gaps are listed in [coverage](feature-parity.md).

## Review and privacy

Three independent read-only simplification reviews found two changes worth
applying: reuse the shared keyword/question schema and select RPC transport
with the catalog family instead of three mutually exclusive booleans.
The efficiency review found no changes needed. The required backlink init
and sequential rows/total ordering remain intact.

Browser state, login credentials and provider keys remain outside the repo.
Only fixed report operations are exposed. Publishable source and build
archives are checked separately from private configuration and captures.

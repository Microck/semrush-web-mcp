# Browser report contract

All operations require a signed-in Semrush browser session. They read fixed
report endpoints inside Chromium. Callers cannot supply URLs, JavaScript,
RPC methods, authentication parameters or account-changing operations.
No operation purchases a subscription, starts a crawl, refreshes paid data,
creates projects, imports cookies into an HTTP client or submits CAPTCHA tasks.
Normal Semrush account report limits apply.

## Authentication and transports

Credentials remain in a private persistent browser profile outside the repo.
Domain authentication parameters come from the signed-in page's serialized
`window.sm2.user` bootstrap JSON. The browser fetches that HTML without rendering
the dashboard or executing its scripts. No JavaScript from the HTML is evaluated.
Keyword Gap observes the web app's authorization header on first use and uses
its `gap.keywords` report header. Both remain in memory and are redacted from
results and errors. Backlink overview requests initialize a logical report
using the same generated `x-request-id` as its subsequent read.

| Family | Endpoint | Shape |
| --- | --- | --- |
| Keyword overview | `/kwogw/v2/webapi` | JSON-RPC with phrase, database and keyword parameters |
| Keyword Magic | `/kmtgw/v2/webapi` | JSON-RPC with matching mode, filters, grouping and page |
| Domain research | `/dpa/rpc` | JSON-RPC with page-owned auth, report name and args |
| Keyword Gap | `/spectrum/v1/Gap/*` | JSON with targets, filters and range; page-owned bearer auth |
| Backlinks and Backlink Gap | `/analytics/backlinks/webapi2/` | GET with fixed report type, targets, paging and filters |
| Backlink overview metrics | `/analytics/backlinks/webapi2/overview/*` | GET after report initialization |
| Projects and saved lists | Fixed `/apis/v4-raw/` routes | Existing records only |
| Audit campaigns | `/siteaudit/api/campaigns/seolist` | Existing campaigns only |
| AI entitlement | `/ai-seo/api/v2/user/user_capabilities` | Account capability read |

The [catalog](tool-catalog.md) identifies each operation's method and inputs.
These internal requests were observed in the signed-in app on October 14,
2026. Semrush can change them independently of this package.

## Query and result behavior

Pydantic validates each input at the boundary and rejects unknown fields.
MCP discovery and CLI discovery expose the same model schema. Filters use
the corresponding web API's filter structure or expression, never executable
code. Array query parameters preserve repeated keys for multi-domain reports.

Organic rankings, pages, subdomains, competitors and changes return `rows`,
`total`, `page` and `page_size`. Their totals come from a separate provider
request. Pages start at 1 and contain at most 100 rows. `date` selects a Unix
snapshot timestamp from `snapshot_dates`; `date_type` selects daily or monthly.
Mobile databases use names such as `mobile-us`.

Keyword Magic returns the provider's keyword or group object. Its separate
summary operation provides matching totals. The overview `keyword_ideas`
operation remains a sample; use Keyword Magic for paginated research.
Backlink tables preserve the provider's caps, limits, offsets and totals;
their pages start at 0. Keyword Gap uses a bounded limit and offset.
Paid keyword/competitor overview operations remain explicitly labeled samples.

Successful results contain `authenticated: true`, `report` and `data`.
The server parses JSON in Python to preserve 64-bit identifiers exactly.
It checks the session with a browser HEAD request to `/home/` before each
operation. An anonymous redirect produces a sign-in error. HTTP, RPC and
provider-status failures produce MCP `isError` results. No automatic retries
or alternate sources hide failures or account limits.

Each MCP process owns one page and closes it on stdio disconnect. It leaves
the shared browser service running. Temporary auth listeners are removed.

## CLI operation contract

`reports --json` lists the MCP operation names and their input schemas.
Every operation has a direct command, with underscores replaced by hyphens.
Query fields become named flags. Boolean flags support `--no-FLAG`; array and
object flags accept JSON. Nullable timestamps accept integer values.
Both interfaces call the same browser operation and return the same result.

`--json` emits one compact JSON object; default output is indented JSON.
`--cdp-url` selects an existing browser instead of the configured service.
Errors go to stderr, with exit 2 for invalid arguments, exit 1 for failed
browser/report operations, and exit 130 for interruption. Report errors
print no traceback or browser authentication fields.

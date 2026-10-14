# Browser report contract

All tools require a signed-in Semrush browser session. No tool imports
cookies into an HTTP client, calls the anonymous free-tools API, creates
projects, refreshes paid data, changes the account, or submits CAPTCHA tasks.
Normal Semrush account report limits still apply.

Browser credentials remain in a private profile outside this repository.
Domain API authentication parameters are observed from the page's own
requests and held in memory. They never appear in results or logs.

| Tool | Browser endpoint and method | Result |
| --- | --- | --- |
| `account_status` | `/kwogw/v2/webapi`, `user.GetInfo` | Authentication, trial and keyword-update limits |
| `keyword_overview` | `/kwogw/v2/webapi`, `keywords.GetInfo` | Metrics for the selected database |
| `keyword_ideas` | `/kwogw/v2/webapi`, `ideas.GetKeywords` | Related keywords or questions |
| `keyword_serp` | `/kwogw/v2/webapi`, `serp.GetURLs` | Ranked URLs and SERP features |
| `keyword_ads` | `/kwogw/v2/webapi`, `adwords.GetCopies` | Search ad copies |
| `keyword_clusters` | `/kwogw/v2/webapi`, `clusters.Get` | Related topics and intents |
| `domain_overview` | `/dpa/rpc`, `organic.Summary` + `backlinks.Summary` | Selected database search metrics and backlink summary |
| `domain_keywords` | `/dpa/rpc`, `organic.PositionsOverview` | Top organic keyword positions |
| `domain_competitors` | `/dpa/rpc`, `organic.CompetitorsOverview` | Organic competitors |
| `domain_backlinks` | `/dpa/rpc`, `backlinks.Overview` | Backlink overview, sample links and anchors |
| `domain_ai_visibility` | `/dpa/rpc`, `organic.AiSeoSummary` | AI visibility, mentions and citations |

These methods and request shapes were observed in the signed-in web app
on October 14, 2026. They are internal web APIs, so Semrush may change them.

Keyword tools accept `keyword` and `database` (default `us`). Domain tools
accept a bare `domain` and `database` (default `us`). Ideas optionally
accept `questions_only`. List tools accept a bounded `limit` and return a
prefix of the browser endpoint's result, not an unlimited export.
Domain keyword positions use the overview report's top-ten sample.

Results contain `authenticated: true`, the report name and `data`.
Authentication is checked with a browser HEAD request to `/home/` before
each report. An anonymous session redirects elsewhere and produces an
explicit sign-in error. HTTP failures, JSON-RPC errors, unavailable browser,
missing report data and account limits produce MCP `isError` results.
There are no automatic request retries or alternate data sources.

The local browser service owns the persistent profile. Each MCP process
owns one page and closes that page when its stdio connection ends.
Independent OMP sessions share the browser, not their report pages.

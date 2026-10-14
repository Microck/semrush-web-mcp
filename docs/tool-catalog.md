# Operation catalog

MCP names use underscores. Native CLI commands replace underscores with hyphens.
`reports --json` exposes the full schema, including defaults, types and limits.

| Operation | Inputs | Browser method or route |
| --- | --- | --- |
| `account_status` | None | `user.GetInfo` |
| `keyword_overview` | `keyword`, `database` | `keywords.GetInfo` |
| `keyword_ideas` | `keyword`, `database`, `questions_only`, `limit` | `ideas.GetKeywords` |
| `keyword_ideas_summary` | `keyword`, `database`, `questions_only` | `ideas.GetKeywordsSummary` |
| `keyword_serp` | `keyword`, `database`, `limit` | `serp.GetURLs` |
| `keyword_ads` | `keyword`, `database`, `limit` | `adwords.GetCopies` |
| `keyword_clusters` | `keyword`, `database` | `clusters.Get` |
| `keyword_magic` | `keyword`, `database`, `questions_only`, `mode`, `currency`, `sort_field`, `descending`, `filters`, `groups`, `page`, `page_size` | `ideas.GetKeywords` |
| `keyword_magic_summary` | `keyword`, `database`, `questions_only`, `mode`, `currency`, `sort_field`, `descending`, `filters`, `groups` | `ideas.GetKeywordsSummary` |
| `keyword_magic_groups` | `keyword`, `database`, `questions_only`, `mode`, `currency`, `sort_field`, `descending`, `filters`, `groups`, `page`, `page_size` | `ideas.GetGroups` |
| `domain_overview` | `domain`, `database` | `organic.Summary` |
| `domain_keywords` | `domain`, `database`, `date`, `search_type`, `date_type`, `page`, `page_size`, `sort_field`, `descending`, `filters` | `organic.Positions` |
| `domain_pages` | `domain`, `database`, `date`, `search_type`, `date_type`, `page`, `page_size`, `sort_field`, `descending`, `filters` | `organic.PagesV3` |
| `domain_subdomains` | `domain`, `database`, `date`, `search_type`, `date_type`, `page`, `page_size`, `sort_field`, `descending`, `filters` | `organic.Subdomains` |
| `domain_position_changes` | `domain`, `database`, `date`, `search_type`, `date_type`, `page`, `page_size`, `sort_field`, `descending`, `filters` | `organic.PositionChangesV2` |
| `domain_competitors` | `domain`, `database`, `date`, `search_type`, `date_type`, `page`, `page_size`, `sort_field`, `descending` | `organic.Competitors` |
| `domain_backlinks` | `domain` | `backlinks.Overview` |
| `domain_ai_visibility` | `domain` | `organic.AiSeoSummary` |
| `domain_ai_countries` | `domain` | `organic.AiDistributionByCountry` |
| `domain_ai_sources` | `domain`, `database`, `limit`, `offset` | `organic.AiTopSources` |
| `domain_trends` | `domain`, `database`, `date_type`, `global_data` | `organic.OverviewTrend` |
| `domain_paid_keywords` | `domain`, `database`, `limit` | `adwords.PositionsOverview` |
| `domain_paid_competitors` | `domain`, `database`, `limit` | `adwords.CompetitorsOverview` |
| `domain_topics` | `domain`, `database` | `organic.TopicsResult` |
| `domain_topics_status` | `domain`, `database` | `organic.TopicsStatus` |
| `databases` | None | `user.Databases` |
| `snapshot_dates` | `database`, `global_data` | `organic.SnapshotDates` |
| `report_permissions` | `database` | `dpa.UserPermissions` |
| `backlink_links` | `domain`, `target_type`, `filters`, `page`, `sort_field`, `descending` | `backlinks` |
| `backlink_referring_domains` | `domain`, `target_type`, `filters`, `page`, `sort_field`, `descending` | `backlinks_refdomains` |
| `backlink_history` | `domain`, `target_type` | `historical` |
| `backlink_competitors` | `domain`, `target_type` | `competitors` |
| `backlink_top_pages` | `domain`, `target_type`, `filters`, `page`, `sort_field`, `descending` | `backlinks_pages` |
| `backlink_anchors` | `domain`, `target_type`, `filters`, `page`, `sort_field`, `descending` | `backlinks_anchors` |
| `backlink_outgoing_domains` | `domain`, `target_type`, `filters`, `page`, `sort_field`, `descending` | `backlinks_outgoing_domains` |
| `backlink_countries` | `domain`, `target_type` | `geodomains` |
| `backlink_authority` | `domain`, `target_type` | `ascore` |
| `backlink_categories` | `domain`, `target_type` | `category-profile` |
| `keyword_gap` | `database`, `domains`, `filters`, `gap_type`, `limit`, `offset` | `/spectrum/v1/Gap/KeywordsList` |
| `keyword_gap_totals` | `database`, `domains`, `filters` | `/spectrum/v1/Gap/KeywordsTotals` |
| `keyword_gap_overlap` | `database`, `domains`, `filters` | `/spectrum/v1/Gap/Overlaps` |
| `backlink_gap` | `domains`, `page`, `limit`, `filters`, `sort_field`, `descending`, `sort_target` | `backlinks_matrix` |
| `backlink_comparison` | `domains` | `backlinks_comparison` |
| `projects` | `limit`, `offset`, `filters` | `/apis/v4-raw/crossroad/api/v0/crossroad/list` |
| `ai_capabilities` | None | `/ai-seo/api/v2/user/user_capabilities` |
| `audit_campaigns` | None | `/siteaudit/api/campaigns/seolist` |
| `folders` | None | `/apis/v4-raw/folders/api/v0/folders/selector-list` |
| `saved_keyword_lists` | None | `/apis/v4-raw/saved-keywords/api/v0/list/all` |

See [the contract](contracts.md) for transports, authentication and pagination.
See [coverage](feature-parity.md) for account restrictions and remaining gaps.

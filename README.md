# Google MCP Server

A unified [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that gives AI assistants direct access to **Google Analytics 4**, **Google Search Console**, **Google Ads** and **Google Merchant Center** data.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and Google REST APIs. Uses OAuth2 user credentials -- no service account needed. You authenticate once, and the server sees every property your Google account has access to.

## Tools (21)

### Google Analytics 4

| Tool | Description |
|---|---|
| `ga4_list_properties` | List all accessible GA4 properties |
| `ga4_run_report` | Run standard reports (dimensions, metrics, filters, sorting, date ranges, up to 10k rows) |
| `ga4_realtime_report` | Realtime active users report |
| `ga4_get_metadata` | List available dimensions and metrics for a property |

### Google Search Console

| Tool | Description |
|---|---|
| `gsc_list_sites` | List all verified sites |
| `gsc_search_analytics` | Search performance data (queries, pages, countries, devices, dates) with filters and pagination (up to 25k rows) |
| `gsc_inspect_url` | Inspect URL indexing status (verdict, coverage, crawl state, robots.txt) |
| `gsc_list_sitemaps` | List submitted sitemaps |
| `gsc_submit_url` | Submit a URL for indexing |

### Google Ads

| Tool | Description |
|---|---|
| `ads_list_customers` | List all accessible Google Ads accounts |
| `ads_campaign_report` | Campaign performance (impressions, clicks, cost, conversions, CPC, CTR) |
| `ads_adgroup_report` | Ad group performance |
| `ads_keyword_report` | Keyword performance (with quality score) |
| `ads_keyword_ideas` | Keyword Planner: search volume, CPC, competition |

### Google Merchant Center

| Tool | Description |
|---|---|
| `merchant_list_accounts` | List all accessible Merchant Center accounts |
| `merchant_list_products` | List products from catalog (title, offer ID, language, feed) |
| `merchant_product_status` | Product approval statuses (approved, disapproved, pending, issues) |
| `merchant_account_status` | Account information (name, language, timezone) |
| `merchant_list_product_issues` | Product issues aggregated by type (with examples) |

### Batch

| Tool | Description |
|---|---|
| `ga4_batch_report` | Run the same GA4 report across multiple properties at once |
| `gsc_batch_analytics` | Run the same Search Analytics query across multiple sites at once |

## Setup

### 1. Prerequisites

- Python 3.10+
- A Google Cloud project with these APIs enabled:
  - Google Analytics Data API
  - Google Analytics Admin API
  - Google Search Console API
  - Google Ads API *(for Ads tools)*
  - Merchant API *(for Merchant Center tools)*

### 2. Create OAuth credentials

1. Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials** > **OAuth client ID** > **Desktop application**
3. Download the JSON file
4. Save it as `~/.config/google-mcp/credentials.json`

### 3. Configure OAuth consent screen scopes

In Google Cloud Console > **Google Auth Platform** > **Data Access**, add these scopes:

- `https://www.googleapis.com/auth/analytics.readonly`
- `https://www.googleapis.com/auth/webmasters.readonly`
- `https://www.googleapis.com/auth/adwords` *(sensitive)*
- `https://www.googleapis.com/auth/content` *(sensitive)*

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Authorize

```bash
python3 authorize.py --extra-scopes https://www.googleapis.com/auth/adwords https://www.googleapis.com/auth/content
```

This opens a browser for Google OAuth consent. The resulting token is saved to `~/.config/google-mcp/token.json`.

Without `--extra-scopes`, only GA4 and GSC tools will work.

### 6. Google Ads: developer token

Google Ads requires a developer token. Create `~/.config/google-mcp/config.json`:

```json
{
  "google_ads": {
    "developer_token": "YOUR_DEVELOPER_TOKEN"
  }
}
```

This file is optional. Without it, GA4, GSC and Merchant Center tools still work. Google Ads tools require it.

You can also add default IDs to avoid passing them on every call:

```json
{
  "google_ads": {
    "developer_token": "YOUR_DEVELOPER_TOKEN",
    "customer_id": "1234567890",
    "login_customer_id": "1234567890"
  },
  "merchant_center": {
    "merchant_id": "123456789"
  }
}
```

### 7. Google Merchant Center: GCP project registration

Merchant API v1 requires registering your GCP project with each Merchant Center account. This is a one-time step per account. See [Register as a developer](https://developers.google.com/merchant/api/guides/quickstart/registration).

### 8. Configure Claude Code

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "google-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/google-mcp/server.py"],
      "env": {
        "GOOGLE_MCP_CONFIG_DIR": "/path/to/.config/google-mcp"
      }
    }
  }
}
```

Restart Claude Code. The 21 tools will be available immediately.

## Configuration

All paths are configurable via environment variables:

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_MCP_CONFIG_DIR` | `~/.config/google-mcp` | Directory for credentials, token and config files |
| `GOOGLE_MCP_CREDENTIALS_FILE` | `{config_dir}/credentials.json` | OAuth client credentials file |
| `GOOGLE_MCP_TOKEN_FILE` | `{config_dir}/token.json` | OAuth token file |
| `GOOGLE_MCP_CONFIG_FILE` | `{config_dir}/config.json` | Extended config (Ads developer token, default IDs) |

## Architecture

```
server.py           FastMCP entry point, 21 @mcp.tool() wrappers
auth.py             OAuth2 centralized (get_credentials, get_ads_client)
config.py           Optional config.json loader (developer token, default IDs)
tools_ga4.py        GA4 via google-api-python-client (REST)
tools_gsc.py        GSC via google-api-python-client (REST)
tools_batch.py      Batch orchestration over GA4/GSC tools
tools_ads.py        Google Ads via subprocess isolation (gRPC in child process)
_ads_impl.py        Google Ads gRPC implementation (runs in subprocess)
tools_merchant.py   Merchant Center via REST (requests HTTP)
authorize.py        One-time OAuth2 flow with --extra-scopes
```

**Why subprocess for Google Ads?** The `google-ads` SDK uses gRPC, which conflicts with FastMCP's asyncio event loop over stdio transport. Running Ads calls in a subprocess isolates gRPC from the MCP server process. All other APIs use REST and run in-process.

## Usage examples

Once configured, you can ask Claude Code things like:

- "List my GA4 properties"
- "Show me the top 20 pages by sessions on property 123456789 for the last 7 days"
- "What queries drive traffic to example.com?"
- "Is this URL indexed? https://example.com/page"
- "Show realtime active users on my site"
- "List my Google Ads accounts"
- "Show campaign performance for customer 9006396761 last month"
- "Generate keyword ideas for 'chaussures running' in France"
- "List my Merchant Center accounts"
- "Show product issues for merchant 5300442232"
- "Run a traffic report on all my GA4 properties at once"

## Why this exists

The official Google MCP servers for GA4 and GSC require **service account** credentials (`google.auth.default()`), which means creating a service account, granting it access to each property, and managing key files. This is cumbersome for individual users.

This server uses **OAuth2 user credentials** (the same flow as signing in with your Google account), which means it works with whatever properties you already have access to -- no extra setup per property. One authentication, all your Google data.

## License

MIT -- see [LICENSE](LICENSE).

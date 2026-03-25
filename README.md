# Google MCP Server

A unified [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that gives AI assistants direct access to **Google Analytics 4** and **Google Search Console** data.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and standard Google REST APIs. Uses OAuth2 user credentials -- no service account needed.

## Tools

### Google Analytics 4

| Tool | Description |
|---|---|
| `ga4_list_properties` | List all accessible GA4 properties |
| `ga4_run_report` | Run standard reports (dimensions, metrics, filters, sorting, date ranges) |
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

## Setup

### 1. Prerequisites

- Python 3.10+
- A Google Cloud project with these APIs enabled:
  - Google Analytics Data API
  - Google Analytics Admin API
  - Google Search Console API

### 2. Create OAuth credentials

1. Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials** > **OAuth client ID** > **Desktop application**
3. Download the JSON file
4. Save it as `~/.config/google-mcp/credentials.json`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Authorize

```bash
python3 authorize.py
```

This opens a browser for Google OAuth consent. The resulting token is saved to `~/.config/google-mcp/token.json`.

### 5. Configure Claude Code

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "google-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/google-mcp/server.py"]
    }
  }
}
```

Restart Claude Code. The 9 tools will be available immediately.

## Configuration

All paths are configurable via environment variables:

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_MCP_CONFIG_DIR` | `~/.config/google-mcp` | Directory for credentials and token files |
| `GOOGLE_MCP_CREDENTIALS_FILE` | `{config_dir}/credentials.json` | OAuth client credentials file |
| `GOOGLE_MCP_TOKEN_FILE` | `{config_dir}/token.json` | OAuth token file |

Example with custom paths:

```json
{
  "mcpServers": {
    "google-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/google-mcp/server.py"],
      "env": {
        "GOOGLE_MCP_CONFIG_DIR": "/path/to/config"
      }
    }
  }
}
```

## Usage examples

Once configured, you can ask Claude Code things like:

- "List my GA4 properties"
- "Show me the top 20 pages by sessions on property 123456789 for the last 7 days"
- "What queries drive traffic to example.com?"
- "Is this URL indexed? https://example.com/page"
- "Show realtime active users on my site"
- "What sitemaps are submitted for sc-domain:example.com?"

## Why this exists

The official Google MCP servers for GA4 and GSC require **service account** credentials (`google.auth.default()`), which means creating a service account, granting it access to each property, and managing key files. This is cumbersome for individual users.

This server uses **OAuth2 user credentials** (the same flow as signing in with your Google account), which means it works with whatever properties you already have access to -- no extra setup per property.

## Roadmap

- [ ] Google Ads API tools (keyword data, campaign reports)
- [ ] Google Merchant Center tools (product catalog, status)
- [ ] Batch reporting (multiple properties at once)

## License

MIT -- see [LICENSE](LICENSE).

#!/usr/bin/env python3
"""Google MCP Server -- GA4 + GSC unified MCP for Claude Code."""

import json
import os
import sys
import traceback
from typing import Any

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tools_ga4
import tools_gsc

mcp = FastMCP("Google MCP")


# -- GA4 --------------------------------------------------------------------


@mcp.tool()
def ga4_list_properties() -> str:
    """List all GA4 properties accessible on the Google account."""
    try:
        result = tools_ga4.ga4_list_properties()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def ga4_run_report(
    property_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str = "28daysAgo",
    end_date: str = "today",
    dimension_filter: dict | None = None,
    order_by: str | None = None,
    order_desc: bool = True,
    limit: int = 100,
) -> str:
    """Run a standard GA4 report.

    Args:
        property_id: GA4 property ID (e.g. "123456789")
        dimensions: Dimensions (e.g. ["pagePath", "country", "date", "sessionDefaultChannelGroup"])
        metrics: Metrics (e.g. ["sessions", "screenPageViews", "activeUsers", "bounceRate"])
        start_date: Start date ("2024-01-01" or "28daysAgo" or "7daysAgo")
        end_date: End date ("2024-01-31" or "today" or "yesterday")
        dimension_filter: Optional filter {"dimension": "pagePath", "match_type": "CONTAINS|EXACT|BEGINS_WITH|ENDS_WITH|REGEXP", "value": "/blog/"}
        order_by: Metric or dimension name for sorting (e.g. "sessions")
        order_desc: Descending sort (default True)
        limit: Max rows returned (default 100, max 10000)
    """
    try:
        result = tools_ga4.ga4_run_report(
            property_id=property_id,
            dimensions=dimensions,
            metrics=metrics,
            start_date=start_date,
            end_date=end_date,
            dimension_filter=dimension_filter,
            order_by=order_by,
            order_desc=order_desc,
            limit=limit,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def ga4_realtime_report(
    property_id: str,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
    limit: int = 50,
) -> str:
    """GA4 realtime report (currently active users).

    Args:
        property_id: GA4 property ID
        dimensions: Realtime dimensions (e.g. ["unifiedScreenName", "country", "city"]). Default: ["unifiedScreenName"]
        metrics: Realtime metrics (e.g. ["activeUsers"]). Default: ["activeUsers"]
        limit: Max rows
    """
    try:
        result = tools_ga4.ga4_realtime_report(
            property_id=property_id,
            dimensions=dimensions,
            metrics=metrics,
            limit=limit,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def ga4_get_metadata(property_id: str) -> str:
    """List all available dimensions and metrics for a GA4 property.

    Args:
        property_id: GA4 property ID
    """
    try:
        result = tools_ga4.ga4_get_metadata(property_id=property_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


# -- GSC ---------------------------------------------------------------------


@mcp.tool()
def gsc_list_sites() -> str:
    """List all verified sites in Google Search Console."""
    try:
        result = tools_gsc.gsc_list_sites()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def gsc_search_analytics(
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    search_type: str = "web",
    row_limit: int = 1000,
    start_row: int = 0,
    dimension_filter_groups: list[dict] | None = None,
    aggregation_type: str = "auto",
) -> str:
    """Retrieve Search Analytics data from Google Search Console.

    Args:
        site_url: GSC property (e.g. "sc-domain:example.com" or "https://www.example.com/")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dimensions: From ["query", "page", "country", "device", "date", "searchAppearance"]. Default: ["query"]
        search_type: "web", "image", "video", "news", "discover", "googleNews"
        row_limit: Max 25000 rows per request
        start_row: Offset for pagination (0, 25000, 50000...)
        dimension_filter_groups: Advanced filters. Ex: [{"groupType": "and", "filters": [{"dimension": "query", "operator": "contains", "expression": "keyword"}]}]
            operators: "contains", "equals", "notContains", "notEquals", "includingRegex", "excludingRegex"
        aggregation_type: "auto", "byPage", "byProperty"
    """
    try:
        result = tools_gsc.gsc_search_analytics(
            site_url=site_url,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
            dimension_filter_groups=dimension_filter_groups,
            aggregation_type=aggregation_type,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def gsc_inspect_url(site_url: str, inspection_url: str) -> str:
    """Inspect a URL's indexing status in Google (verdict, coverage, crawl, robots.txt).

    Args:
        site_url: GSC property (e.g. "sc-domain:example.com")
        inspection_url: Full URL to inspect (e.g. "https://www.example.com/page.html")
    """
    try:
        result = tools_gsc.gsc_inspect_url(site_url=site_url, inspection_url=inspection_url)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def gsc_list_sitemaps(site_url: str) -> str:
    """List submitted sitemaps for a site in Google Search Console.

    Args:
        site_url: GSC property (e.g. "sc-domain:example.com")
    """
    try:
        result = tools_gsc.gsc_list_sitemaps(site_url=site_url)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


@mcp.tool()
def gsc_submit_url(site_url: str, url: str) -> str:
    """Submit a URL for Google indexing via Search Console.

    Args:
        site_url: GSC property
        url: Full URL to submit
    """
    try:
        result = tools_gsc.gsc_submit_url(site_url=site_url, url=url)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    mcp.run()

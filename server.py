#!/usr/bin/env python3
"""Google MCP Server -- GA4 + GSC + Google Ads + Merchant Center."""

# === CRITIQUE : silence total AVANT tout import de SDK ===
# Le transport stdio MCP utilise stdout exclusivement pour JSON-RPC.
# Toute écriture parasite (warning, log, print) casse le protocole.
import warnings
warnings.filterwarnings("ignore")

import json
import logging
import os
import sys
import traceback
from typing import Any

# Silencer les loggers des SDK Google avant leur import
for _logger_name in [
    "google.ads", "google.api_core", "google.auth", "google.auth.transport",
    "urllib3", "requests", "grpc", "protobuf", "absl",
]:
    logging.getLogger(_logger_name).setLevel(logging.CRITICAL)

# absl-py (dépendance google-ads) écrit sur stdout par défaut
try:
    from absl import logging as _absl_logging
    _absl_logging.set_verbosity(_absl_logging.FATAL)
except ImportError:
    pass

# Rediriger les logs du serveur vers un fichier
_log_file = open("/tmp/mcp_google_server.log", "a", buffering=1)
logging.basicConfig(stream=_log_file, level=logging.WARNING)

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tools_ga4
import tools_gsc
import tools_batch
# tools_ads et tools_merchant : lazy import dans chaque @mcp.tool()

mcp = FastMCP("Google MCP")


# -- GA4 --------------------------------------------------------------------


@mcp.tool()
def ga4_list_properties() -> str:
    """List all GA4 properties accessible on the Google account."""
    try:
        result = tools_ga4.ga4_list_properties()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def ga4_get_metadata(property_id: str) -> str:
    """List all available dimensions and metrics for a GA4 property.

    Args:
        property_id: GA4 property ID
    """
    try:
        result = tools_ga4.ga4_get_metadata(property_id=property_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# -- GSC ---------------------------------------------------------------------


@mcp.tool()
def gsc_list_sites() -> str:
    """List all verified sites in Google Search Console."""
    try:
        result = tools_gsc.gsc_list_sites()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def gsc_list_sitemaps(site_url: str) -> str:
    """List submitted sitemaps for a site in Google Search Console.

    Args:
        site_url: GSC property (e.g. "sc-domain:example.com")
    """
    try:
        result = tools_gsc.gsc_list_sitemaps(site_url=site_url)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# -- Batch -------------------------------------------------------------------


@mcp.tool()
def ga4_batch_report(
    property_ids: list[str],
    dimensions: list[str],
    metrics: list[str],
    start_date: str = "28daysAgo",
    end_date: str = "today",
    dimension_filter: dict | None = None,
    order_by: str | None = None,
    order_desc: bool = True,
    limit: int = 100,
) -> str:
    """Run the same GA4 report across multiple properties at once.

    Args:
        property_ids: List of GA4 property IDs (e.g. ["123456789", "987654321"])
        dimensions: Dimensions (e.g. ["pagePath", "country"])
        metrics: Metrics (e.g. ["sessions", "screenPageViews"])
        start_date: Start date ("2024-01-01" or "28daysAgo")
        end_date: End date ("2024-01-31" or "today")
        dimension_filter: Optional filter (applied to all properties)
        order_by: Sort by metric or dimension
        order_desc: Descending sort (default True)
        limit: Max rows per property
    """
    try:
        result = tools_batch.ga4_batch_report(
            property_ids=property_ids,
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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def gsc_batch_analytics(
    site_urls: list[str],
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    search_type: str = "web",
    row_limit: int = 1000,
    start_row: int = 0,
    dimension_filter_groups: list[dict] | None = None,
    aggregation_type: str = "auto",
) -> str:
    """Run the same Search Analytics query across multiple GSC properties at once.

    Args:
        site_urls: List of GSC properties (e.g. ["sc-domain:site1.com", "sc-domain:site2.com"])
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dimensions: From ["query", "page", "country", "device", "date", "searchAppearance"]
        search_type: "web", "image", "video", "news", "discover", "googleNews"
        row_limit: Max rows per site (max 25000)
        start_row: Offset for pagination
        dimension_filter_groups: Advanced filters
        aggregation_type: "auto", "byPage", "byProperty"
    """
    try:
        result = tools_batch.gsc_batch_analytics(
            site_urls=site_urls,
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
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# -- Google Ads --------------------------------------------------------------


@mcp.tool()
def ads_list_customers() -> str:
    """List all accessible Google Ads accounts (customer ID, name, currency, timezone)."""
    try:
        import tools_ads
        result = tools_ads.ads_list_customers()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR ads_list_customers: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

@mcp.tool()
def ads_campaign_report(
    customer_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> str:
    """Google Ads campaign performance report (impressions, clicks, cost, conversions, CPC, CTR).

    Args:
        customer_id: Google Ads customer ID (optional, falls back to config)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max campaigns returned
    """
    try:
        import tools_ads
        result = tools_ads.ads_campaign_report(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def ads_adgroup_report(
    customer_id: str | None = None,
    campaign_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> str:
    """Google Ads ad group performance report.

    Args:
        customer_id: Google Ads customer ID (optional)
        campaign_id: Filter by campaign (optional)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max ad groups returned
    """
    try:
        import tools_ads
        result = tools_ads.ads_adgroup_report(
            customer_id=customer_id,
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def ads_keyword_report(
    customer_id: str | None = None,
    campaign_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> str:
    """Google Ads keyword performance report (with quality score).

    Args:
        customer_id: Google Ads customer ID (optional)
        campaign_id: Filter by campaign (optional)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max keywords returned
    """
    try:
        import tools_ads
        result = tools_ads.ads_keyword_report(
            customer_id=customer_id,
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def ads_keyword_ideas(
    keywords: list[str],
    customer_id: str | None = None,
    language_id: str = "1002",
    location_ids: list[str] | None = None,
    page_size: int = 50,
) -> str:
    """Generate keyword ideas via Google Ads Keyword Planner (search volume, CPC, competition).

    Note: requires an account with spending history for exact volumes.

    Args:
        keywords: Seed keywords (e.g. ["chaussures running", "baskets sport"])
        customer_id: Google Ads customer ID (optional)
        language_id: Language ID ("1002" = French, "1000" = English)
        location_ids: Geo target IDs (default: ["2250"] = France)
        page_size: Max keyword ideas returned
    """
    try:
        import tools_ads
        result = tools_ads.ads_keyword_ideas(
            keywords=keywords,
            customer_id=customer_id,
            language_id=language_id,
            location_ids=location_ids,
            page_size=page_size,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# -- Merchant Center ---------------------------------------------------------


@mcp.tool()
def merchant_list_accounts() -> str:
    """List all accessible Google Merchant Center accounts (discover account IDs before querying)."""
    try:
        import tools_merchant
        result = tools_merchant.merchant_list_accounts()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def merchant_list_products(
    merchant_id: str | None = None,
    page_size: int = 250,
) -> str:
    """List products from Google Merchant Center catalog.

    Args:
        merchant_id: Merchant Center account ID (optional, falls back to config)
        page_size: Max products per page
    """
    try:
        import tools_merchant
        result = tools_merchant.merchant_list_products(
            merchant_id=merchant_id,
            page_size=page_size,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def merchant_product_status(
    merchant_id: str | None = None,
    page_size: int = 250,
) -> str:
    """Get product approval statuses from Merchant Center (approved, disapproved, pending, issues).

    Args:
        merchant_id: Merchant Center account ID (optional)
        page_size: Max products to check
    """
    try:
        import tools_merchant
        result = tools_merchant.merchant_product_status(
            merchant_id=merchant_id,
            page_size=page_size,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def merchant_account_status(merchant_id: str | None = None) -> str:
    """Get Merchant Center account information (name, language, timezone).

    Args:
        merchant_id: Merchant Center account ID (optional)
    """
    try:
        import tools_merchant
        result = tools_merchant.merchant_account_status(
            merchant_id=merchant_id,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def merchant_list_product_issues(
    merchant_id: str | None = None,
    severity_filter: str | None = None,
    page_size: int = 250,
) -> str:
    """List product issues aggregated by type (disapprovals, warnings, with examples).

    Args:
        merchant_id: Merchant Center account ID (optional)
        severity_filter: Filter by severity ("ERROR", "WARNING") — optional
        page_size: Max products to analyze
    """
    try:
        import tools_merchant
        result = tools_merchant.merchant_list_product_issues(
            merchant_id=merchant_id,
            severity_filter=severity_filter,
            page_size=page_size,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_file.write(f"ERROR: {e}\n")
        _log_file.flush()
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()

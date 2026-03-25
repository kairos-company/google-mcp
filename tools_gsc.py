"""Outils Google Search Console API."""

from typing import Any

from googleapiclient.discovery import build

from auth import get_credentials


def _get_service():
    return build("searchconsole", "v1", credentials=get_credentials())


def _get_webmasters_service():
    return build("webmasters", "v3", credentials=get_credentials())


def gsc_list_sites() -> list[dict]:
    """Liste tous les sites vérifiés dans Google Search Console."""
    service = _get_webmasters_service()
    result = service.sites().list().execute()
    sites = result.get("siteEntry", [])
    return [{"url": s["siteUrl"], "level": s.get("permissionLevel", "")} for s in sites]


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
) -> dict[str, Any]:
    """Récupère les données Search Analytics de GSC.

    Args:
        site_url: URL du site (ex: "sc-domain:example.com" ou "https://www.example.com/")
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        dimensions: Liste parmi ["query", "page", "country", "device", "date", "searchAppearance"]
        search_type: "web", "image", "video", "news", "discover", "googleNews"
        row_limit: Max 25000 lignes
        start_row: Offset pour pagination
        dimension_filter_groups: Filtres [{
            "groupType": "and",
            "filters": [{"dimension": "query", "operator": "contains", "expression": "mot"}]
        }]
        aggregation_type: "auto", "byPage", "byProperty"
    """
    service = _get_webmasters_service()

    body: dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions or ["query"],
        "type": search_type,
        "rowLimit": min(row_limit, 25000),
        "startRow": start_row,
        "aggregationType": aggregation_type,
    }

    if dimension_filter_groups:
        body["dimensionFilterGroups"] = dimension_filter_groups

    result = service.searchanalytics().query(siteUrl=site_url, body=body).execute()

    rows = []
    for row in result.get("rows", []):
        r = {}
        for i, dim in enumerate(body["dimensions"]):
            r[dim] = row["keys"][i]
        r["clicks"] = row.get("clicks", 0)
        r["impressions"] = row.get("impressions", 0)
        r["ctr"] = round(row.get("ctr", 0) * 100, 2)
        r["position"] = round(row.get("position", 0), 1)
        rows.append(r)

    return {
        "row_count": len(rows),
        "rows": rows,
    }


def gsc_inspect_url(site_url: str, inspection_url: str) -> dict[str, Any]:
    """Inspecte l'indexation d'une URL dans Google.

    Args:
        site_url: Propriété GSC (ex: "sc-domain:example.com")
        inspection_url: URL complète à inspecter
    """
    service = _get_service()

    result = service.urlInspection().index().inspect(
        body={
            "inspectionUrl": inspection_url,
            "siteUrl": site_url,
        }
    ).execute()

    inspection = result.get("inspectionResult", {})
    index_status = inspection.get("indexStatusResult", {})
    crawl_status = index_status.get("crawlTimeSecs")

    return {
        "verdict": index_status.get("verdict", "N/D"),
        "coverage_state": index_status.get("coverageState", "N/D"),
        "indexing_state": index_status.get("indexingState", "N/D"),
        "page_fetch_state": index_status.get("pageFetchState", "N/D"),
        "robots_txt_state": index_status.get("robotsTxtState", "N/D"),
        "last_crawl_time": index_status.get("lastCrawlTime", "N/D"),
        "crawl_time_secs": crawl_status,
        "referring_urls": index_status.get("referringUrls", []),
        "sitemap": index_status.get("sitemap", []),
    }


def gsc_list_sitemaps(site_url: str) -> list[dict]:
    """Liste les sitemaps soumis pour un site.

    Args:
        site_url: URL du site (ex: "sc-domain:example.com")
    """
    service = _get_webmasters_service()
    result = service.sitemaps().list(siteUrl=site_url).execute()
    sitemaps = result.get("sitemap", [])
    return [{
        "path": s.get("path", ""),
        "type": s.get("type", ""),
        "last_submitted": s.get("lastSubmitted", ""),
        "last_downloaded": s.get("lastDownloaded", ""),
        "warnings": s.get("warnings", 0),
        "errors": s.get("errors", 0),
        "contents": [{
            "type": c.get("type", ""),
            "submitted": c.get("submitted", 0),
            "indexed": c.get("indexed", 0),
        } for c in s.get("contents", [])],
    } for s in sitemaps]


def gsc_submit_url(site_url: str, url: str) -> dict[str, str]:
    """Soumet une URL à l'indexation Google.

    Args:
        site_url: Propriété GSC
        url: URL à soumettre
    """
    service = _get_service()
    service.urlInspection().index().inspect(
        body={
            "inspectionUrl": url,
            "siteUrl": site_url,
        }
    ).execute()
    return {"status": "URL soumise", "url": url}

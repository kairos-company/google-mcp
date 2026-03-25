"""Outils GA4 — via googleapiclient discovery (REST)."""

from typing import Any

from googleapiclient.discovery import build

from auth import get_credentials


def _get_admin_service():
    return build("analyticsadmin", "v1beta", credentials=get_credentials())


def _get_data_service():
    return build("analyticsdata", "v1beta", credentials=get_credentials())


def _rows_to_dicts(response: dict) -> list[dict]:
    """Convertit une réponse JSON GA4 en liste de dicts."""
    dim_headers = [h["name"] for h in response.get("dimensionHeaders", [])]
    met_headers = [h["name"] for h in response.get("metricHeaders", [])]
    rows = []
    for row in response.get("rows", []):
        d = {}
        for i, dv in enumerate(row.get("dimensionValues", [])):
            d[dim_headers[i]] = dv.get("value", "")
        for i, mv in enumerate(row.get("metricValues", [])):
            d[met_headers[i]] = mv.get("value", "")
        rows.append(d)
    return rows


def ga4_list_properties() -> list[dict]:
    """Liste toutes les propriétés GA4 accessibles."""
    service = _get_admin_service()
    results = []
    request = service.accountSummaries().list()
    while request:
        response = request.execute()
        for summary in response.get("accountSummaries", []):
            account_name = summary.get("displayName", "")
            for prop in summary.get("propertySummaries", []):
                prop_id = prop.get("property", "").split("/")[-1]
                results.append({
                    "account": account_name,
                    "property_id": prop_id,
                    "property_name": prop.get("displayName", ""),
                })
        request = service.accountSummaries().list_next(request, response)
    return results


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
) -> dict[str, Any]:
    """Exécute un rapport GA4.

    Args:
        property_id: ID de la propriété GA4 (ex: "123456789")
        dimensions: Liste de dimensions (ex: ["pagePath", "country"])
        metrics: Liste de métriques (ex: ["sessions", "screenPageViews"])
        start_date: Date de début (ex: "2024-01-01" ou "28daysAgo")
        end_date: Date de fin (ex: "2024-01-31" ou "today")
        dimension_filter: Filtre optionnel {"dimension": "pagePath", "match_type": "CONTAINS", "value": "/blog/"}
        order_by: Métrique ou dimension pour le tri
        order_desc: Tri descendant (défaut True)
        limit: Nombre max de lignes (défaut 100)
    """
    service = _get_data_service()

    body: dict[str, Any] = {
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "limit": limit,
    }

    if dimension_filter:
        body["dimensionFilter"] = {
            "filter": {
                "fieldName": dimension_filter["dimension"],
                "stringFilter": {
                    "matchType": dimension_filter.get("match_type", "CONTAINS"),
                    "value": dimension_filter["value"],
                },
            }
        }

    if order_by:
        ob: dict[str, Any] = {"desc": order_desc}
        if order_by in metrics:
            ob["metric"] = {"metricName": order_by}
        else:
            ob["dimension"] = {"dimensionName": order_by}
        body["orderBys"] = [ob]

    response = service.properties().runReport(
        property=f"properties/{property_id}", body=body
    ).execute()

    return {
        "row_count": response.get("rowCount", 0),
        "rows": _rows_to_dicts(response),
    }


def ga4_realtime_report(
    property_id: str,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Rapport temps réel GA4.

    Args:
        property_id: ID de la propriété GA4
        dimensions: Dimensions temps réel. Défaut: ["unifiedScreenName"]
        metrics: Métriques temps réel. Défaut: ["activeUsers"]
        limit: Nombre max de lignes
    """
    if not dimensions:
        dimensions = ["unifiedScreenName"]
    if not metrics:
        metrics = ["activeUsers"]

    service = _get_data_service()
    body = {
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "limit": limit,
    }

    response = service.properties().runRealtimeReport(
        property=f"properties/{property_id}", body=body
    ).execute()

    return {
        "row_count": response.get("rowCount", 0),
        "rows": _rows_to_dicts(response),
    }


def ga4_get_metadata(property_id: str) -> dict[str, Any]:
    """Retourne les dimensions et métriques disponibles pour une propriété GA4."""
    service = _get_data_service()
    data = service.properties().getMetadata(
        name=f"properties/{property_id}/metadata"
    ).execute()

    dims = [{"name": d["apiName"], "display": d.get("uiName", ""), "category": d.get("category", "")} for d in data.get("dimensions", [])]
    mets = [{"name": m["apiName"], "display": m.get("uiName", ""), "category": m.get("category", "")} for m in data.get("metrics", [])]
    return {
        "dimensions_count": len(dims),
        "metrics_count": len(mets),
        "dimensions": dims,
        "metrics": mets,
    }

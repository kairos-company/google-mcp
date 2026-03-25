"""Outils batch — rapports multi-propriétés GA4 et GSC."""

import traceback
from typing import Any

import tools_ga4
import tools_gsc


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
) -> dict[str, Any]:
    """Lance le même rapport GA4 sur plusieurs propriétés.

    Args:
        property_ids: Liste d'IDs de propriétés GA4 (ex: ["123456789", "987654321"])
        dimensions: Dimensions du rapport
        metrics: Métriques du rapport
        start_date: Date de début
        end_date: Date de fin
        dimension_filter: Filtre optionnel (appliqué à toutes les propriétés)
        order_by: Tri par métrique ou dimension
        order_desc: Tri descendant
        limit: Nombre max de lignes par propriété
    """
    results = {}
    errors = {}
    for pid in property_ids:
        try:
            results[pid] = tools_ga4.ga4_run_report(
                property_id=pid,
                dimensions=dimensions,
                metrics=metrics,
                start_date=start_date,
                end_date=end_date,
                dimension_filter=dimension_filter,
                order_by=order_by,
                order_desc=order_desc,
                limit=limit,
            )
        except Exception as e:
            traceback.print_exc()
            errors[pid] = str(e)
    return {"results": results, "errors": errors}


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
) -> dict[str, Any]:
    """Lance la même requête Search Analytics sur plusieurs sites GSC.

    Args:
        site_urls: Liste de propriétés GSC (ex: ["sc-domain:site1.com", "sc-domain:site2.com"])
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        dimensions: Dimensions du rapport
        search_type: Type de recherche
        row_limit: Max lignes par site
        start_row: Offset pagination
        dimension_filter_groups: Filtres avancés
        aggregation_type: Type d'agrégation
    """
    results = {}
    errors = {}
    for url in site_urls:
        try:
            results[url] = tools_gsc.gsc_search_analytics(
                site_url=url,
                start_date=start_date,
                end_date=end_date,
                dimensions=dimensions,
                search_type=search_type,
                row_limit=row_limit,
                start_row=start_row,
                dimension_filter_groups=dimension_filter_groups,
                aggregation_type=aggregation_type,
            )
        except Exception as e:
            traceback.print_exc()
            errors[url] = str(e)
    return {"results": results, "errors": errors}

"""Implémentation Google Ads — gRPC. Exécuté dans un sous-processus isolé."""

# Silence total AVANT les imports gRPC/google-ads
import warnings
import os
import sys

warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"
os.environ["PYTHONWARNINGS"] = "ignore"
sys.stderr = open(os.devnull, "w")

from typing import Any

from auth import get_ads_client
from config import get_ads_config


def _clean_customer_id(customer_id: str | None = None) -> str:
    cid = customer_id or get_ads_config().get("customer_id")
    if not cid:
        raise ValueError(
            "customer_id requis : passez-le en paramètre ou configurez "
            "'google_ads.customer_id' dans config.json"
        )
    return cid.replace("-", "")


def ads_list_customers() -> list[dict]:
    """Liste tous les comptes Google Ads accessibles."""
    client = get_ads_client()
    customer_service = client.get_service("CustomerService")
    accessible = customer_service.list_accessible_customers()

    results = []
    ga_service = client.get_service("GoogleAdsService")
    for resource_name in accessible.resource_names:
        cid = resource_name.split("/")[-1]
        try:
            query = "SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone FROM customer LIMIT 1"
            response = ga_service.search(customer_id=cid, query=query)
            for row in response:
                results.append({
                    "customer_id": str(row.customer.id),
                    "name": row.customer.descriptive_name,
                    "currency": row.customer.currency_code,
                    "time_zone": row.customer.time_zone,
                })
        except Exception:
            results.append({
                "customer_id": cid,
                "name": "(accès refusé)",
                "currency": "",
                "time_zone": "",
            })
    return results


def ads_campaign_report(
    customer_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> dict[str, Any]:
    cid = _clean_customer_id(customer_id)
    client = get_ads_client(customer_id=cid)
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id, campaign.name, campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.average_cpc, metrics.ctr
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """
    response = ga_service.search(customer_id=cid, query=query)
    rows = []
    for row in response:
        rows.append({
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "status": row.campaign.status.name,
            "channel_type": row.campaign.advertising_channel_type.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(row.metrics.cost_micros / 1_000_000, 2),
            "conversions": round(row.metrics.conversions, 2),
            "average_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "ctr": round(row.metrics.ctr * 100, 2),
        })
    return {"row_count": len(rows), "rows": rows}


def ads_adgroup_report(
    customer_id: str | None = None,
    campaign_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> dict[str, Any]:
    cid = _clean_customer_id(customer_id)
    client = get_ads_client(customer_id=cid)
    ga_service = client.get_service("GoogleAdsService")

    where_clause = f"WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'"
    if campaign_id:
        where_clause += f" AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            campaign.id, campaign.name,
            ad_group.id, ad_group.name, ad_group.status,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.ctr
        FROM ad_group
        {where_clause}
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """
    response = ga_service.search(customer_id=cid, query=query)
    rows = []
    for row in response:
        rows.append({
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "adgroup_id": str(row.ad_group.id),
            "adgroup_name": row.ad_group.name,
            "status": row.ad_group.status.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(row.metrics.cost_micros / 1_000_000, 2),
            "conversions": round(row.metrics.conversions, 2),
            "ctr": round(row.metrics.ctr * 100, 2),
        })
    return {"row_count": len(rows), "rows": rows}


def ads_keyword_report(
    customer_id: str | None = None,
    campaign_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> dict[str, Any]:
    cid = _clean_customer_id(customer_id)
    client = get_ads_client(customer_id=cid)
    ga_service = client.get_service("GoogleAdsService")

    where_clause = f"WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'"
    if campaign_id:
        where_clause += f" AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            campaign.name, ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.average_cpc, metrics.ctr
        FROM keyword_view
        {where_clause}
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """
    response = ga_service.search(customer_id=cid, query=query)
    rows = []
    for row in response:
        rows.append({
            "campaign": row.campaign.name,
            "adgroup": row.ad_group.name,
            "keyword": row.ad_group_criterion.keyword.text,
            "match_type": row.ad_group_criterion.keyword.match_type.name,
            "quality_score": row.ad_group_criterion.quality_info.quality_score,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(row.metrics.cost_micros / 1_000_000, 2),
            "conversions": round(row.metrics.conversions, 2),
            "average_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "ctr": round(row.metrics.ctr * 100, 2),
        })
    return {"row_count": len(rows), "rows": rows}


def ads_keyword_ideas(
    keywords: list[str],
    customer_id: str | None = None,
    language_id: str = "1002",
    location_ids: list[str] | None = None,
    page_size: int = 50,
) -> list[dict]:
    cid = _clean_customer_id(customer_id)
    client = get_ads_client(customer_id=cid)

    if location_ids is None:
        location_ids = ["2250"]

    kp_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordIdeasRequest")

    request.customer_id = cid
    request.language = client.get_service("GoogleAdsService").language_constant_path(language_id)
    request.geo_target_constants = [
        client.get_service("GoogleAdsService").geo_target_constant_path(loc_id)
        for loc_id in location_ids
    ]
    request.include_adult_keywords = False
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

    request.keyword_seed.keywords.extend(keywords)
    request.page_size = page_size

    response = kp_service.generate_keyword_ideas(request=request)

    results = []
    for idea in response.results:
        m = idea.keyword_idea_metrics
        results.append({
            "keyword": idea.text,
            "avg_monthly_searches": m.avg_monthly_searches,
            "competition": m.competition.name,
            "competition_index": m.competition_index,
            "low_top_of_page_bid": round(m.low_top_of_page_bid_micros / 1_000_000, 2) if m.low_top_of_page_bid_micros else None,
            "high_top_of_page_bid": round(m.high_top_of_page_bid_micros / 1_000_000, 2) if m.high_top_of_page_bid_micros else None,
        })
    return results

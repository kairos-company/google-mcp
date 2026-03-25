"""Outils Google Merchant Center — via Merchant API v1 (REST pur, sans gRPC)."""

import logging
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("google.auth").setLevel(logging.CRITICAL)

import requests
from typing import Any

from auth import get_credentials
from config import get_merchant_id

BASE_URL = "https://merchantapi.googleapis.com/accounts/v1"


def _get_headers() -> dict:
    """Retourne les headers HTTP avec le token OAuth2."""
    creds = get_credentials()
    return {"Authorization": f"Bearer {creds.token}"}


def _merchant_get(path: str) -> dict:
    """GET sur l'API Merchant v1."""
    resp = requests.get(f"{BASE_URL}/{path}", headers=_get_headers())
    resp.raise_for_status()
    return resp.json()


def _require_merchant_id(merchant_id: str | None = None) -> str:
    mid = get_merchant_id(merchant_id)
    if not mid:
        raise ValueError(
            "merchant_id requis : passez-le en paramètre ou configurez "
            "'merchant_center.merchant_id' dans config.json. "
            "Utilisez merchant_list_accounts pour découvrir vos comptes."
        )
    return mid


def merchant_list_accounts() -> list[dict]:
    """Liste tous les comptes Merchant Center accessibles."""
    data = _merchant_get("accounts")
    accounts = []
    for account in data.get("accounts", []):
        accounts.append({
            "name": account.get("name", ""),
            "account_id": account.get("name", "").split("/")[-1],
            "account_name": account.get("accountName", ""),
            "language_code": account.get("languageCode", ""),
        })
    return accounts


def merchant_list_products(
    merchant_id: str | None = None,
    page_size: int = 250,
) -> dict[str, Any]:
    """Liste les produits du catalogue Merchant Center.

    Args:
        merchant_id: ID du compte Merchant (optionnel, fallback sur config)
        page_size: Nombre max de produits
    """
    mid = _require_merchant_id(merchant_id)
    data = _merchant_get(f"accounts/{mid}/products?pageSize={page_size}")
    products = []
    for product in data.get("products", []):
        attrs = product.get("productAttributes", {})
        products.append({
            "name": product.get("name", ""),
            "offer_id": product.get("offerId", ""),
            "title": attrs.get("title", ""),
            "content_language": product.get("contentLanguage", ""),
            "feed_label": product.get("feedLabel", ""),
        })
    return {"count": len(products), "products": products}


def merchant_product_status(
    merchant_id: str | None = None,
    page_size: int = 250,
) -> dict[str, Any]:
    """Récupère les statuts de tous les produits (approuvés, refusés, avertissements).

    Args:
        merchant_id: ID du compte Merchant (optionnel)
        page_size: Nombre max de produits
    """
    mid = _require_merchant_id(merchant_id)
    data = _merchant_get(f"accounts/{mid}/products?pageSize={page_size}")

    approved = 0
    disapproved = 0
    pending = 0
    issues_list = []

    for product in data.get("products", []):
        attrs = product.get("productAttributes", {})
        title = attrs.get("title", "") or product.get("offerId", "") or product.get("name", "")
        status = product.get("productStatus", {})

        product_issues = []
        product_status_str = "approved"

        for dest in status.get("destinationStatuses", []):
            if dest.get("disapprovedCountries"):
                product_status_str = "disapproved"
            elif dest.get("pendingCountries") and product_status_str != "disapproved":
                product_status_str = "pending"

        for issue in status.get("itemLevelIssues", []):
            product_issues.append({
                "code": issue.get("code", ""),
                "severity": issue.get("severity", ""),
                "description": issue.get("description", ""),
                "detail": issue.get("detail", ""),
                "documentation": issue.get("documentation", ""),
                "resolution": issue.get("resolution", ""),
                "applicable_countries": issue.get("applicableCountries", []),
            })

        if product_status_str == "approved":
            approved += 1
        elif product_status_str == "disapproved":
            disapproved += 1
        else:
            pending += 1

        if product_issues:
            issues_list.append({
                "product": title,
                "offer_id": product.get("offerId", ""),
                "status": product_status_str,
                "issues": product_issues,
            })

    return {
        "summary": {"approved": approved, "disapproved": disapproved, "pending": pending, "total": approved + disapproved + pending},
        "products_with_issues": issues_list,
    }


def merchant_account_status(merchant_id: str | None = None) -> dict[str, Any]:
    """Récupère l'état général du compte Merchant Center.

    Args:
        merchant_id: ID du compte Merchant (optionnel)
    """
    mid = _require_merchant_id(merchant_id)
    data = _merchant_get(f"accounts/{mid}")
    return {
        "account_id": mid,
        "account_name": data.get("accountName", ""),
        "language_code": data.get("languageCode", ""),
    }


def merchant_list_product_issues(
    merchant_id: str | None = None,
    severity_filter: str | None = None,
    page_size: int = 250,
) -> dict[str, Any]:
    """Liste les produits avec des problèmes, agrégés par type d'issue.

    Args:
        merchant_id: ID du compte Merchant (optionnel)
        severity_filter: Filtrer par sévérité ("ERROR", "WARNING") — optionnel
        page_size: Nombre max de produits à analyser
    """
    status_data = merchant_product_status(merchant_id=merchant_id, page_size=page_size)

    issue_counts: dict[str, int] = {}
    issue_examples: dict[str, list] = {}

    for product in status_data["products_with_issues"]:
        for issue in product["issues"]:
            code = issue["code"]
            severity = issue["severity"]
            if severity_filter and severity_filter.upper() not in severity.upper():
                continue
            if code not in issue_counts:
                issue_counts[code] = 0
                issue_examples[code] = []
            issue_counts[code] += 1
            if len(issue_examples[code]) < 3:
                issue_examples[code].append({
                    "product": product["product"],
                    "offer_id": product["offer_id"],
                    "description": issue["description"],
                    "detail": issue["detail"],
                    "severity": severity,
                })

    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "total_products_with_issues": len(status_data["products_with_issues"]),
        "summary": status_data["summary"],
        "issues_by_type": [{"code": code, "count": count, "examples": issue_examples[code]} for code, count in sorted_issues],
    }

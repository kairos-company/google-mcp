"""Outils Google Ads — exécutés dans un sous-processus pour isoler gRPC."""

import json
import os
import subprocess
import sys
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _run_ads_subprocess(func_name: str, **kwargs) -> Any:
    """Exécute une fonction ads dans un sous-processus Python isolé.

    Nécessaire car le SDK google-ads utilise gRPC, incompatible avec
    l'event loop asyncio de FastMCP (crash du serveur MCP).
    """
    code = f"""
import sys, os, json
sys.path.insert(0, {_SCRIPT_DIR!r})
os.chdir({_SCRIPT_DIR!r})
import _ads_impl
result = _ads_impl.{func_name}(**{kwargs!r})
print(json.dumps(result, ensure_ascii=False))
"""
    env = os.environ.copy()
    env["GOOGLE_MCP_CONFIG_DIR"] = os.environ.get("GOOGLE_MCP_CONFIG_DIR", os.path.expanduser("~/.config/google-mcp"))
    env["PYTHONWARNINGS"] = "ignore"
    env["GRPC_VERBOSITY"] = "ERROR"
    env["GLOG_minloglevel"] = "3"

    result = subprocess.run(
        [sys.executable, "-c", code],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Erreur ads ({func_name}) : {result.stderr.strip()}")
    return json.loads(result.stdout)


def ads_list_customers() -> list[dict]:
    """Liste tous les comptes Google Ads accessibles."""
    return _run_ads_subprocess("ads_list_customers")


def ads_campaign_report(
    customer_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> dict[str, Any]:
    """Rapport de performance par campagne Google Ads.

    Args:
        customer_id: ID client Google Ads (optionnel, fallback sur config)
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        limit: Nombre max de campagnes
    """
    return _run_ads_subprocess("ads_campaign_report", customer_id=customer_id, start_date=start_date, end_date=end_date, limit=limit)


def ads_adgroup_report(
    customer_id: str | None = None,
    campaign_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> dict[str, Any]:
    """Rapport de performance par groupe d'annonces.

    Args:
        customer_id: ID client Google Ads (optionnel)
        campaign_id: Filtrer par campagne (optionnel)
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        limit: Nombre max de groupes
    """
    return _run_ads_subprocess("ads_adgroup_report", customer_id=customer_id, campaign_id=campaign_id, start_date=start_date, end_date=end_date, limit=limit)


def ads_keyword_report(
    customer_id: str | None = None,
    campaign_id: str | None = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    limit: int = 100,
) -> dict[str, Any]:
    """Rapport de performance par mot-clé Google Ads.

    Args:
        customer_id: ID client Google Ads (optionnel)
        campaign_id: Filtrer par campagne (optionnel)
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        limit: Nombre max de mots-clés
    """
    return _run_ads_subprocess("ads_keyword_report", customer_id=customer_id, campaign_id=campaign_id, start_date=start_date, end_date=end_date, limit=limit)


def ads_keyword_ideas(
    keywords: list[str],
    customer_id: str | None = None,
    language_id: str = "1002",
    location_ids: list[str] | None = None,
    page_size: int = 50,
) -> list[dict]:
    """Génère des idées de mots-clés via le Keyword Planner Google Ads.

    Note : nécessite un compte avec historique de dépenses pour des volumes exacts.

    Args:
        keywords: Liste de mots-clés de départ (ex: ["chaussures running", "baskets sport"])
        customer_id: ID client Google Ads (optionnel)
        language_id: ID de la langue ("1002" = français, "1000" = anglais)
        location_ids: IDs des zones géographiques (défaut: ["2250"] = France)
        page_size: Nombre max d'idées retournées
    """
    return _run_ads_subprocess("ads_keyword_ideas", keywords=keywords, customer_id=customer_id, language_id=language_id, location_ids=location_ids, page_size=page_size)

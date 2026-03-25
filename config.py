"""Chargement de la configuration étendue (Google Ads, Merchant Center).

Le fichier config.json est OPTIONNEL. Il sert de valeurs par défaut
pour éviter de passer les IDs à chaque appel. Sans config.json,
les outils de découverte (ads_list_customers, merchant_list_accounts)
fonctionnent quand même — il suffit de passer les IDs en paramètres.
"""

import json
import os

from auth import CONFIG_DIR

CONFIG_FILE = os.environ.get(
    "GOOGLE_MCP_CONFIG_FILE", os.path.join(CONFIG_DIR, "config.json")
)

_cached_config: dict | None = None


def get_config() -> dict:
    """Lit et retourne la configuration depuis config.json.

    Retourne un dict vide si le fichier n'existe pas.
    """
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    if not os.path.exists(CONFIG_FILE):
        _cached_config = {}
        return _cached_config

    with open(CONFIG_FILE) as f:
        _cached_config = json.load(f)

    return _cached_config


def get_ads_config() -> dict:
    """Retourne la section google_ads de la config (peut être vide)."""
    return get_config().get("google_ads", {})


def get_merchant_id(merchant_id: str | None = None) -> str | None:
    """Retourne le merchant_id passé en paramètre ou depuis la config.

    Retourne None si aucun n'est disponible.
    """
    if merchant_id:
        return str(merchant_id)
    mid = get_config().get("merchant_center", {}).get("merchant_id")
    return str(mid) if mid else None

"""Centralized OAuth2 authentication for Google APIs."""

import json
import os
import sys

import google.auth.transport.requests
from google.oauth2.credentials import Credentials

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/google-mcp")

CONFIG_DIR = os.environ.get("GOOGLE_MCP_CONFIG_DIR", DEFAULT_CONFIG_DIR)
CREDENTIALS_FILE = os.environ.get(
    "GOOGLE_MCP_CREDENTIALS_FILE", os.path.join(CONFIG_DIR, "credentials.json")
)
TOKEN_FILE = os.environ.get(
    "GOOGLE_MCP_TOKEN_FILE", os.path.join(CONFIG_DIR, "token.json")
)

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


def _load_token_data() -> dict:
    """Lit credentials.json + token.json et retourne les données combinées.

    Retourne un dict avec : client_id, client_secret, refresh_token, token, token_uri, scopes.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(
            f"ERREUR : fichier credentials introuvable : {CREDENTIALS_FILE}\n"
            "Lancez d'abord : python3 authorize.py",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    if not os.path.exists(TOKEN_FILE):
        print(
            f"ERREUR : fichier token introuvable : {TOKEN_FILE}\n"
            "Lancez d'abord : python3 authorize.py",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    with open(CREDENTIALS_FILE) as f:
        client_config = json.load(f)

    client_info = client_config.get("installed", client_config.get("web", {}))

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    return {
        "client_id": client_info["client_id"],
        "client_secret": client_info["client_secret"],
        "refresh_token": token_data["refresh_token"],
        "token": token_data.get("token"),
        "token_uri": token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        "scopes": token_data.get("scopes", SCOPES),
    }


def get_credentials() -> Credentials:
    """Build OAuth2 Credentials from the stored refresh token."""
    data = _load_token_data()

    creds = Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )

    # Toujours rafraîchir — le token stocké est souvent expiré
    creds.refresh(google.auth.transport.requests.Request())

    return creds


def get_ads_client(customer_id: str | None = None):
    """Construit un GoogleAdsClient à partir des credentials OAuth2 + config.

    Le developer_token est requis dans config.json.
    Le customer_id et login_customer_id sont optionnels (découverte via ads_list_customers).

    Args:
        customer_id: ID client Google Ads (optionnel, fallback sur config.json).
    """
    import sys
    from google.ads.googleads.client import GoogleAdsClient
    from config import get_ads_config

    data = _load_token_data()
    ads_config = get_ads_config()

    developer_token = ads_config.get("developer_token")
    if not developer_token:
        print(
            "ERREUR : 'google_ads.developer_token' requis dans config.json pour utiliser Google Ads.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    cid = customer_id or ads_config.get("customer_id", "")
    if cid:
        cid = cid.replace("-", "")

    client_dict = {
        "developer_token": developer_token,
        "client_id": data["client_id"],
        "client_secret": data["client_secret"],
        "refresh_token": data["refresh_token"],
        "use_proto_plus": True,
    }

    login_cid = ads_config.get("login_customer_id", cid)
    if login_cid:
        client_dict["login_customer_id"] = login_cid.replace("-", "")

    return GoogleAdsClient.load_from_dict(client_dict)

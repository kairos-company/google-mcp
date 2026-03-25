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


def get_credentials() -> Credentials:
    """Build OAuth2 Credentials from the stored refresh token."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(
            f"ERREUR: fichier credentials introuvable : {CREDENTIALS_FILE}\n"
            "Lancez d'abord : python3 authorize.py",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    if not os.path.exists(TOKEN_FILE):
        print(
            f"ERREUR: fichier token introuvable : {TOKEN_FILE}\n"
            "Lancez d'abord : python3 authorize.py",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    with open(CREDENTIALS_FILE) as f:
        client_config = json.load(f)

    client_info = client_config.get("installed", client_config.get("web", {}))
    client_id = client_info["client_id"]
    client_secret = client_info["client_secret"]

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data["refresh_token"],
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=client_id,
        client_secret=client_secret,
        scopes=token_data.get("scopes", SCOPES),
    )

    if not creds.valid:
        creds.refresh(google.auth.transport.requests.Request())

    return creds

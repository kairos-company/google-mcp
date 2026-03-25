#!/usr/bin/env python3
"""OAuth2 authorization flow for Google MCP.

Run this script once to generate a token.json file that the MCP server
will use to authenticate with Google APIs.

Prerequisites:
  1. Create an OAuth2 client ID in Google Cloud Console
     (APIs & Services > Credentials > Create Credentials > OAuth client ID > Desktop app)
  2. Download the JSON and save it as credentials.json in the config directory

Usage:
  python3 authorize.py [--config-dir ~/.config/google-mcp]
"""

import argparse
import json
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


def main():
    parser = argparse.ArgumentParser(description="Google MCP OAuth2 authorization")
    parser.add_argument(
        "--config-dir",
        default=os.environ.get("GOOGLE_MCP_CONFIG_DIR", os.path.expanduser("~/.config/google-mcp")),
        help="Directory containing credentials.json (default: ~/.config/google-mcp)",
    )
    parser.add_argument(
        "--extra-scopes",
        nargs="*",
        default=[],
        help="Additional OAuth scopes to request (e.g. for Google Ads, Merchant Center)",
    )
    args = parser.parse_args()

    config_dir = args.config_dir
    os.makedirs(config_dir, exist_ok=True)

    credentials_file = os.path.join(config_dir, "credentials.json")
    token_file = os.path.join(config_dir, "token.json")

    if not os.path.exists(credentials_file):
        print(
            f"ERROR: {credentials_file} not found.\n\n"
            "To create it:\n"
            "  1. Go to https://console.cloud.google.com/apis/credentials\n"
            "  2. Create an OAuth 2.0 Client ID (Desktop application)\n"
            "  3. Download the JSON file\n"
            "  4. Save it as: {credentials_file}\n"
        )
        sys.exit(1)

    scopes = SCOPES + args.extra_scopes

    print(f"Requesting scopes: {scopes}")
    print(f"Config directory:  {config_dir}")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else scopes,
    }

    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\nToken saved to: {token_file}")
    print("Google MCP is ready to use.")


if __name__ == "__main__":
    main()

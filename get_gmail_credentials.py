#!/usr/bin/env python3
"""
Run this ONCE locally to generate your Gmail OAuth credentials.
It will open a browser for you to authorize access, then print the
JSON you need to paste into your GitHub secret (GMAIL_CREDENTIALS_JSON).

Prerequisites:
  pip install google-auth-oauthlib google-api-python-client

Setup:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or use an existing one)
  3. Enable the Gmail API
  4. Go to APIs & Services → Credentials → Create Credentials → OAuth client ID
  5. Application type: Desktop app
  6. Download the JSON and save it as 'client_secret.json' in this folder
  7. Run: python get_gmail_credentials.py
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    creds_dict = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "scopes":        creds.scopes,
    }

    print("\n✅ Authorization successful!\n")
    print("=" * 60)
    print("Copy everything below into your GitHub secret named:")
    print("GMAIL_CREDENTIALS_JSON")
    print("=" * 60)
    print(json.dumps(creds_dict, indent=2))
    print("=" * 60)

    with open("gmail_credentials.json", "w") as f:
        json.dump(creds_dict, f, indent=2)
    print("\nAlso saved to gmail_credentials.json (do NOT commit this file!)")

if __name__ == "__main__":
    main()

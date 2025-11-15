import json
import time
from stravalib import Client
import requests

TOKEN_FILE = "../tokens.json"

def load_tokens():
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=4)

def refresh_if_needed(tokens):
    """Refresh access token automatically if expired."""
    if time.time() < tokens["expires_at"]:
        return tokens  # Token still valid

    print("Access token expired — refreshing...")
    
    response = requests.post(
        "https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": tokens["client_id"],
            "client_secret": tokens["client_secret"],
            "refresh_token": tokens["refresh_token"],
            "grant_type": "refresh_token"
        }
    )

    new_tokens = response.json()

    # Fusionner les infos (client_id/secret restent)
    tokens["access_token"] = new_tokens["access_token"]
    tokens["refresh_token"] = new_tokens["refresh_token"]
    tokens["expires_at"] = new_tokens["expires_at"]

    save_tokens(tokens)
    print("Token rafraîchi ✔️")

    return tokens

# ----------------------------------------------------
# 🏃 Script principal
# ----------------------------------------------------

tokens = load_tokens()
tokens = refresh_if_needed(tokens)

client = Client(access_token=tokens["access_token"])

# Exemple : récupérer une activité
activities = client.get_activities(limit=1)
for a in activities:
    print(a.id, a.name)

import json
import time
import os
import warnings
warnings.filterwarnings('ignore', message='No rates present in response headers')
from stravalib import Client


os.environ['SILENCE_TOKEN_WARNINGS'] = 'True'

# Initialize Strava client
client = Client()

# File to store tokens (access, refresh, expiration)
# Tokens are given with your strava application
TOKEN_FILE = "tokens.json"

# Load tokens from json file
# Store it
# Refresh it when the acces token is expired (every 6 hours)
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
    


    new_tokens = client.refresh_access_token(
        client_id=tokens["client_id"],
        client_secret=tokens["client_secret"],
        refresh_token=tokens["refresh_token"]
    )
    tokens["access_token"] = new_tokens["access_token"]
    tokens["refresh_token"] = new_tokens["refresh_token"]
    tokens["expires_at"] = new_tokens["expires_at"]

    save_tokens(tokens)
    print("Token refreshed")

    return tokens

tokens = load_tokens()
tokens = refresh_if_needed(tokens)

# Re-initialize client with valid access token
# The client contains now all my running data
client = Client(access_token=tokens["access_token"])



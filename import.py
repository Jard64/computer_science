
import stravalib
import os
from time import time
from stravalib import Client

#Set your client_id
MY_STRAVA_CLIENT_ID = int(os.environ.get('CLIENT_ID'))

#Set your client_secret
MY_STRAVA_CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

client = Client()
url = client.authorization_url(
    client_id=MY_STRAVA_CLIENT_ID,
    redirect_uri="http://localhost:500/authorization",
)

print(url)

client = Client()

#Use this token to make API calls
access_token='293a195f57891526a13cc67ada60e6c1048ed9d6'
client.access_token = access_token

#Use this token to keep your session alive
last_refresh_token = 'b693d8a9ef901c1b90955dc1a4b16cdab141c55d'
client.refresh_token = last_refresh_token

#Initial expiration time
client.token_expires_at = 1763034879

if time() > client.token_expires_at:
    refresh_response = client.refresh_access_token(
        client_id=MY_STRAVA_CLIENT_ID,
        client_secret="TON_CLIENT_SECRET",
        refresh_token=client.refresh_token
    )
    access_token = refresh_response["access_token"]
    expires_at = refresh_response["expires_at"]
    refresh_token = refresh_response["refresh_token"]

client.access_token = access_token

athlete = client.get_athlete()
print(f"Athlete: {athlete.firstname} {athlete.lastname}")





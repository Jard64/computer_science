
import os
from time import time
from stravalib import Client

#Set your client_id
MY_STRAVA_CLIENT_ID = int(os.environ.get('STRAVA_CLIENT_ID'))

#Set your client_secret
MY_STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')

client = Client()
url = client.authorization_url(
    client_id=MY_STRAVA_CLIENT_ID,
    redirect_uri="http://localhost:500/authorization",
)

print(url)

client = Client()

#Use this token to make API calls
access_token='4520415a3e46580ebb4dab2223d712b9accf424b'
client.access_token = access_token

#Use this token to keep your session alive
refresh_token='1cc1daea3458fe337feab64e03971a958d1c1b05'
client.refresh_token = refresh_token

#Initial expiration time
token_expires_at = 1763197179
client.token_expires = token_expires_at

if time() > client.token_expires:
    refresh_response = client.refresh_access_token(
        client_id=MY_STRAVA_CLIENT_ID,
        client_secret=MY_STRAVA_CLIENT_SECRET,
        refresh_token=client.refresh_token
    )
    access_token = refresh_response["access_token"]
    expires_at = refresh_response["expires_at"]
    refresh_token = refresh_response["refresh_token"]

client.access_token = access_token



athlete = client.get_athlete()
print(f"Bonjour {athlete.firstname} !")

activities = client.get_activities(limit=1)
for a in activities:
    print(a.id, a.name)






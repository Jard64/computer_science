
import stravalib
from stravalib import Client

# Connecte-toi avec ton access token
client = Client(access_token="96f194676c4cdae3bb3fdfc9007a4a98e964f952")

activity_id = 300  # remplace par ton ID d'activité

# Récupère les streams (types possibles: 'time', 'latlng', 'distance', 'altitude', etc.)
streams = client.get_activity_streams(activity_id, types=['time', 'altitude', 'latlng'], resolution='medium')

# Affiche les données récupérées
for stream_type, stream in streams.items():
    print(stream_type, stream.data[:10])  # on affiche les 10 premiers points

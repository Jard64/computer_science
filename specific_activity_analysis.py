from matplotlib import pyplot as plt
from api_call import client
import numpy as np
import datetime

#Statistics for specific activity
def activity_stream_bpm(activity_id):
    cardio_activity = client.get_activity_streams(activity_id=activity_id,types=['heartrate'],series_type=['distance'])
    bpm=cardio_activity['heartrate'].data
    distance=cardio_activity['distance'].data
    plt.plot(distance, bpm)

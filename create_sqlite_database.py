import sqlite3
from api_call import client
import json
from tqdm import tqdm

conn = sqlite3.connect("sqlite_activity_database.db")
cursor = conn.cursor()
ACTIVITIES=client.get_activities()

#Columns of activity table
LIST_ACTIVITY_DATA_TYPES = ['distance', 'moving_time', 'total_elevation_gain',
                             'average_speed', 'max_speed', 'average_cadence',
                               'average_watts', 'kilojoules', 'has_heartrate', 'average_heartrate', 
                               'max_heartrate', 'elev_high', 'elev_low']


STREAM_TYPES=['time', 'distance', 'heartrate','altitude','cadence','grade_smooth','velocity_smooth','watts']


cursor.execute("""
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY
);
               """)

#Create one column for each activity data type

activity_columns = cursor.execute("PRAGMA table_info(activity);").fetchall()
activity_columns = [column[1] for column in activity_columns]
for activity_data_type in LIST_ACTIVITY_DATA_TYPES:
    if activity_data_type not in [activity_column for activity_column in activity_columns]:
        cursor.execute(f"""
        ALTER TABLE activity
        ADD COLUMN {activity_data_type} REAL;
        """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS streams (
    id INTEGER,
    stream_type TEXT,
    stream_value TEXT,
    PRIMARY KEY (id, stream_type),
    CONSTRAINT fk_activity FOREIGN KEY (id) REFERENCES activity(id)
);
               """)

def insert_activity_data():
    activities = ACTIVITIES
    activities = [ activity for activity in activities if activity.sport_type=='Run' or activity.sport_type=='TrailRun' ]
    list_activity_id=cursor.execute("SELECT id FROM activity;").fetchall()
    all_ids = [activity.id for activity in activities]
    list_activity_id=[item[0] for item in list_activity_id]
    for activity_id in tqdm(all_ids):
        if activity_id not in list_activity_id:
            activity=client.get_activity(activity_id)
            cursor.execute("""INSERT OR IGNORE INTO activity (id) VALUES (?);""", (activity_id,))
            for activity_data_type in LIST_ACTIVITY_DATA_TYPES:
                activity_data_value=getattr(activity,activity_data_type)
                cursor.execute(f"""UPDATE activity SET {activity_data_type} = ? WHERE id = ?;""", (activity_data_value, activity_id))



def insert_stream_data():
    activities = ACTIVITIES
    activities = [ activity for activity in activities if activity.sport_type=='Run' or activity.sport_type=='TrailRun' ]
    all_ids = [activity.id for activity in activities]
    list_activity_id=cursor.execute("SELECT id FROM activity;").fetchall()
    list_activity_id=[item[0] for item in list_activity_id]
    for activity_id in tqdm(all_ids):
        if activity_id not in list_activity_id:
            for stream_type in STREAM_TYPES:
                stream=client.get_activity_streams(activity_id=activity_id, types=[stream_type], series_type=['time'])
                try:
                    stream_json=json.dumps(stream[stream_type].data)
                except KeyError:
                    stream_json=json.dumps([])
                cursor.execute("""INSERT OR IGNORE INTO streams (id, stream_type, stream_value) VALUES (?, ?, ?);""", (activity_id, stream_type, stream_json))


            

insert_activity_data()
insert_stream_data()




conn.commit()
conn.close()


#Architecture of the database

#Table activity
# id | info1 | info2 | ...
# 1001 | ...   | ... | ...
# 1002 | ...   | ... | ...

#Table streams
# id | stream_type | stream_value
# 1001 | heartrate   | [val1, val2, ...]
# 1001 | distance    | [val1, val2, ...]
# 1002 | heartrate   | [val1, val2, ...]
# 1002 | distance    | [val1, val2, ...]
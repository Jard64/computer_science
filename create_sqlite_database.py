import sqlite3
from api_call import client
import json
from tqdm import tqdm
from datetime import datetime


conn = sqlite3.connect("sqlite_activity_database.db")
cursor = conn.cursor()

# Columns of activity table
LIST_ACTIVITY_DATA_TYPES = ['distance', 'moving_time', 'total_elevation_gain',
                             'average_speed', 'max_speed', 'average_cadence',
                             'average_watts', 'kilojoules', 'has_heartrate', 
                             'average_heartrate', 'max_heartrate', 'elev_high', 'elev_low']

STREAM_TYPES = ['time', 'distance', 'heartrate', 'altitude', 'cadence', 
                'grade_smooth', 'velocity_smooth', 'watts']

# Create activity table
cursor.execute("""
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY,
    sport_type TEXT,
    name TEXT,
    start_date TEXT
);
""")

# Add columns dynamically
activity_columns = cursor.execute("PRAGMA table_info(activity);").fetchall()
activity_columns = [column[1] for column in activity_columns]
for activity_data_type in LIST_ACTIVITY_DATA_TYPES:
    if activity_data_type not in activity_columns:
        cursor.execute(f"""
        ALTER TABLE activity
        ADD COLUMN {activity_data_type} REAL;
        """)

# Create streams table
cursor.execute("""
CREATE TABLE IF NOT EXISTS streams (
    id INTEGER,
    stream_type TEXT,
    stream_value TEXT,
    PRIMARY KEY (id, stream_type),
    FOREIGN KEY (id) REFERENCES activity(id)
);
""")

# Create index for faster queries
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_streams_id ON streams(id);
""")

# Track API calls (optional but useful)
cursor.execute("""
CREATE TABLE IF NOT EXISTS api_calls (
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    endpoint TEXT,
    activity_id INTEGER
);
""")

conn.commit()


def log_api_call(endpoint, activity_id=None):
    """Log API calls to track rate limits"""
    cursor.execute("""
        INSERT INTO api_calls (endpoint, activity_id) 
        VALUES (?, ?);
    """, (endpoint, activity_id))


def insert_activity_data():
    """Insert activity data, using cached data from get_activities() first"""
    print("Fetching activities list...")
    log_api_call('get_activities')
    activities = client.get_activities()
    activities = [activity for activity in activities 
                  if activity.sport_type in ['Run', 'TrailRun']]
    activities_dict = {a.id: a for a in activities}

    list_activity_id = cursor.execute("SELECT id FROM activity;").fetchall()
    list_activity_id = {item[0] for item in list_activity_id}  # Use set for faster lookup
    
    for activity in tqdm(activities, desc="Processing activities"):
        activity_id = activity.id
        
        if activity_id not in list_activity_id:
            # Use data from get_activities() first (no API call needed)
            cursor.execute("""
                INSERT OR IGNORE INTO activity (id, sport_type, name, start_date) 
                VALUES (?, ?, ?, ?);
            """, (activity_id, str(activity.sport_type), 
                  str(activity.name), str(activity.start_date)))
            
            # Check which fields are available in the summary
            needs_detailed_fetch = False
            for activity_data_type in LIST_ACTIVITY_DATA_TYPES:
                try:
                    activity_data_value = getattr(activity, activity_data_type)
                    if activity_data_value is not None:
                        cursor.execute(f"""
                            UPDATE activity SET {activity_data_type} = ? WHERE id = ?;
                        """, (float(activity_data_value) if activity_data_value else None, 
                              activity_id))
                    else:
                        needs_detailed_fetch = True
                except AttributeError:
                    needs_detailed_fetch = True
            
            # Only fetch detailed activity if necessary
            if needs_detailed_fetch:
                print(f"\nFetching detailed data for activity {activity_id}...")
                log_api_call('get_activity', activity_id)
                detailed_activity = activities_dict[activity_id]
                
                for activity_data_type in LIST_ACTIVITY_DATA_TYPES:
                    try:
                        try:
                            activity_data_value = getattr(detailed_activity, activity_data_type)
                        except:
                            detailed_activity=client.get_activity(activity_id)
                            activity_data_value = getattr(detailed_activity, activity_data_type)
                        cursor.execute(f"""
                            UPDATE activity SET {activity_data_type} = ? WHERE id = ?;
                        """, (float(activity_data_value) if activity_data_value else None, 
                              activity_id))
                    except (AttributeError, TypeError):
                        pass
            
            # Commit every 10 activities to avoid losing everything on error
            if activity.id % 10 == 0:
                conn.commit()
    
    conn.commit()


def insert_stream_data():
    """Insert stream data only for activities that don't have streams yet"""
    activities = client.get_activities()
    activities = [activity for activity in activities 
                  if activity.sport_type in ['Run', 'TrailRun']]
    all_ids = [activity.id for activity in activities]
    
    # Get activities that exist in activity table
    list_activity_id = cursor.execute("SELECT id FROM activity;").fetchall()
    list_activity_id = {item[0] for item in list_activity_id}
    
    # Get activities that already have streams
    existing_streams = cursor.execute("""
        SELECT DISTINCT id FROM streams;
    """).fetchall()
    existing_stream_ids = {item[0] for item in existing_streams}
    
    for activity_id in tqdm(all_ids, desc="Processing streams"):
        # Only fetch streams if activity exists AND streams don't exist
        if activity_id in list_activity_id and activity_id not in existing_stream_ids:
            print(f"\nFetching streams for activity {activity_id}...")
            log_api_call('get_activity_streams', activity_id)
            
            try:
                # Fetch all streams at once (more efficient)
                streams = client.get_activity_streams(
                    activity_id=activity_id, 
                    types=STREAM_TYPES, 
                    series_type='time'
                )
                
                for stream_type in STREAM_TYPES:
                    try:
                        stream_json = json.dumps(streams[stream_type].data)
                    except (KeyError, AttributeError):
                        stream_json = json.dumps([])
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO streams (id, stream_type, stream_value) 
                        VALUES (?, ?, ?);
                    """, (activity_id, stream_type, stream_json))
                
                # Commit every activity to avoid losing data
                conn.commit()
                
            except Exception as e:
                print(f"Error fetching streams for activity {activity_id}: {e}")
                conn.rollback()


def get_api_call_stats():
    """Check how many API calls were made"""
    result = cursor.execute("""
        SELECT endpoint, COUNT(*) as count 
        FROM api_calls 
        WHERE timestamp > datetime('now', '-1 day')
        GROUP BY endpoint;
    """).fetchall()

    result_15 = cursor.execute("""
        SELECT endpoint, COUNT(*) as count 
        FROM api_calls 
        WHERE timestamp > datetime('now', '-15 minutes')
        GROUP BY endpoint;
    """).fetchall()
    
    print("\n=== API Calls in last 24h ===")
    total = 0
    for endpoint, count in result:
        print(f"{endpoint}: {count} calls")
        total += count
    print(f"TOTAL: {total} calls")
    print(f"Remaining today: {1000 - total} calls")

    print("\n=== API Calls in last 15 minutes ===")
    total = 0
    now = datetime.now()
    current_minute = now.minute
    current_hour = now.hour
    next_quarter = ((current_minute //15)+1)*15 %60
    current_hour=+1 if next_quarter==0 else current_hour
    current_hour=current_hour%24
    text_time=f"{current_hour:02d}:{next_quarter:02d}"
    for endpoint, count in result_15:
        print(f"{endpoint}: {count} calls")
        total += count
    print(f"TOTAL: {total} calls")
    print("Remaining until " +text_time +f": {100 - total} calls")



if __name__ == "__main__":
    try:
        insert_activity_data()
        insert_stream_data()
        get_api_call_stats()
    finally:
        conn.commit()
        conn.close()
        print("\nDatabase closed successfully!")

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
# Computer_Science - My Strava Analysis

## Description
This project aims to import my running data from my Strava account for analysis. The analysis will be divided into several objectives:
- Importing my running and weather data and storing it in the correct format
- Store data into local sql table
- Compute a GAP metrics from my own data
- More developpement should come in the future

## User Guide
- `api_call.py` 
    Handle the api call with the token given by [Strava](https://www.strava.com/settings/api)  
- `global_analysis.py`
    Analysis of the global performance evolution based on average data of each activity
- `specific_activity_analysis.py`
    Aims to focus on the activities stream i.e. the temporal series (heartrate,speed etc..)
- `create_sqlite_database.py`
    Create a database to stock all the data from Strava, make update when new activities has been added




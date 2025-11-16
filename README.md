# Computer_Science - My Strava Analysis

## Description
This project aims to import my running data from my Strava account for analysis. The analysis will be divided into several objectives:
- Importing my running and weather data and storing it in the correct format
- Determining key factors that influence speed and fatigue
- Making performance predictions and comparing prediction models (physiological vs machine learning)
- Evaluating overtraining

## User Guide
- `Main.py`
- `strava_api_call.py` 
    Handle the strava api call with the token given by [Strava](https://www.strava.com/settings/api)  
- `global_analysis.py`
    Analysis of the global performance evolution based on average data of each activity
- `specific_activity_analysis.py`
    Aims to focus on the activities stream i.e. the temporal series of 
      - Heartrate 
      - Speed 
      - Pace 
      - Elevation 
      - Power 
      - Cadence 
      - Smooth velocity 
      - Temperature 

## Links
- [Enduraw website](https://enduraw-data.com)
- [A paper describing the Paris Olympics marathon performance](https://shorturl.at/V8ryZ)
- [An article dealing with trail pacing plan](https://shorturl.at/5Z1Yd)
- [Description of the GAP metric](https://pickletech.eu/blog-gap/)
- [Strava API description](https://developers.strava.com/docs/reference/)
- [Stravalib documentation](https://stravalib.readthedocs.io/en/latest/)




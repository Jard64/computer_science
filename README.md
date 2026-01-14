# Computer_Science - My Strava Analysis

## Description
This project aims to import my running data from my Strava account for analysis. The analysis will be divided into several objectives:
- Importing my running and weather data and storing it in the correct format
- Determining key factors that influence speed and fatigue
- Making performance predictions and comparing prediction models (physiological vs machine learning)
- Evaluating overtraining

## User Guide
- `Main.py`
- `api_call.py` 
    Handle the api call with the token given by [Strava](https://www.strava.com/settings/api)  
- `global_analysis.py`
    Analysis of the global performance evolution based on average data of each activity
- `specific_activity_analysis.py`
    Aims to focus on the activities stream i.e. the temporal series (heartrate,speed etc..)
- `create_sqlite_database.py`
    Create a database to stock all the data from Strava, make update when new activities has been added

## Links
- [Firstbeat Technologies Ltd VO2max Estimation White Paper](https://www.firstbeat.com/wp-content/uploads/2017/06/white_paper_VO2max_30.6.2017.pdf)
- [Garmin Hill Score Methodology](https://www.garmin.com/en-AU/garmin-technology/running-science/running-dynamics/hill-score/) 
- [Firstbeat Physiological Analysis Documentation](https://www.firstbeat.com/wp-content/uploads/2017/06/white_paper_VO2max_30.6.2017.pdf)
- [Enduraw Performance Analytics Platform](https://enduraw-data.com)
- [World Athletics: Paris Olympics Marathon Performance Analysis](https://shorturl.at/V8ryZ)
- [Trail Running Pacing Strategy Analysis](https://shorturl.at/5Z1Yd)
- [Grade Adjusted Pace (GAP) Metric Specification](https://pickletech.eu/blog-gap/)
- [Strava API Technical Documentation](https://developers.strava.com/docs/reference/)
- [Stravalib Python Library Documentation](https://stravalib.readthedocs.io/en/latest/)




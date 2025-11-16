from matplotlib import pyplot as plt
from api_call import client
import numpy as np
import datetime

MIN_RUNNING_TIME=1200  
RUN_ACTIVITY_TYPE='Run'
HEART_RATE_STREAM_TYPE='heartrate'



def number_of_activities():
    activities=client.get_athlete_stats()
    count=0
    for a in activities:
        if a.type=='Run' and a.moving_time>1200:
            count+=1
    return count

def total_time_hours():
    activities=client.get_activities()
    total_time=0
    for a in activities:
        if a.type=='Run' and a.moving_time>1200:
            total_time+=a.moving_time
    return int(total_time/3600)

def last_activity_date():
    activities=client.get_activities()
    for a in activities:
        if a.type=='Run' and a.moving_time>1200:
            return a.start_date.date()
        
def first_activity_date():
    activities=client.get_activities()
    activities_list=list(activities)
    activities_list.reverse()
    for a in activities_list:
        if a.type=='Run' and a.moving_time>1200:
            return a.start_date.date()
    
def total_distance_km():
    activities=client.get_activities()
    total_distance=0
    for a in activities:
        if a.type=='Run' and a.moving_time>1200:
            total_distance+=a.distance
    return int(total_distance/1000)

#Faster versions using a built-in function in stravalib
#Do not exclude short activities (less than 20 minutes)
#Permit to limit the number of API calls (limited to 100 per 15 minutes)
def number_of_activities_bis():
    activities_count=client.get_athlete_stats().all_run_totals.count
    return activities_count

def total_time_hours_bis():
    total_time=client.get_athlete_stats().all_run_totals.moving_time
    return int(total_time/3600)

def total_distance_km_bis():
    total_distance=client.get_athlete_stats().all_run_totals.distance
    return int(total_distance/1000)
    
def show_global_statistics():
    print('last run date:',last_activity_date())
    print('first run date:',first_activity_date())
    print("Number of runs longer than 20 minutes:",number_of_activities_bis())
    print("Total time spent running (in hours):",total_time_hours_bis())
    print("Total distance run (in km):",total_distance_km_bis())




#Overall statistics
def get_average_bpm():
    activities=client.get_activities()
    avg_bpm=np.array([])
    for a in activities:
        if a.type=='Run' and a.moving_time>1200 and a.average_heartrate is not None:
            avg_bpm=np.append(avg_bpm,a.average_heartrate)
    avg_bpm=avg_bpm[::-1]
    return avg_bpm

def get_dates():
    activities=client.get_activities()
    date=np.array([])
    for a in activities:
        if a.type=='Run' and a.moving_time>1200 and a.average_heartrate is not None:
            date=np.append(date,a.start_date.date())
    date=date[::-1]
    return date

def get_average_pace():
    activities=client.get_activities()
    avg_pace=np.array([])
    for a in activities:
        if a.type=='Run' and a.moving_time>1200 and a.average_speed is not None and a.average_heartrate is not None:
            pace=1000/a.average_speed
            pace=pace//60 + (pace%60)/60
            avg_pace=np.append(avg_pace,pace)
    avg_pace=avg_pace[::-1]
    return avg_pace

def get_average_speed():
    activities=client.get_activities()
    avg_speed=np.array([])
    for a in activities:
        if a.type=='Run' and a.moving_time>1200 and a.average_speed is not None and a.average_heartrate is not None:
            avg_speed=np.append(avg_speed,a.average_speed*3.6)
    avg_speed=avg_speed[::-1]
    return avg_speed

def get_elevation_gain():
    activities=client.get_activities()
    elevation_gain=np.array([])
    for a in activities:
        if a.type=='Run' and a.moving_time>1200 and a.total_elevation_gain is not None and a.average_heartrate is not None:
            elevation_gain=np.append(elevation_gain,a.total_elevation_gain)
    elevation_gain=elevation_gain[::-1]
    return elevation_gain

def get_temperature():
    activities=client.get_activities()
    temperature=np.array([])
    for a in activities:
        if a.type=='Run' and a.moving_time>1200 and a.average_temp is not None and a.average_heartrate is not None:
            temperature=np.append(temperature,a.average_temp)
    temperature=temperature[::-1]
    return temperature


def personal_best_evolution(distance_km=10,min_time=3000):
    activities=client.get_activities()
    activities=list(activities)
    activities.reverse()
    personal_best_time=[min_time]
    list_potential_pb=[]
    for a in activities:
        if a.type=='Run':
            if a.moving_time>1200 and a.average_speed>12/3.6:
                list_potential_pb.append(a.id)
    list_potential_pb.reverse()
    for id in list_potential_pb:
        a=client.get_activity(id)
        for effort in a.best_efforts:
            if effort.distance==distance_km*1000:
                if effort.moving_time<personal_best_time[-1]:
                    personal_best_time.append(effort.moving_time)
    return personal_best_time[1:]


###############PLOTS################
def scatter_average_bpm():
    avg_bpm=get_average_bpm()
    date=get_dates()
    scatter_average_bpm=plt.scatter(date,avg_bpm)
    return scatter_average_bpm

def plot_bpm_trend():    
    avg_bpm=get_average_bpm()
    date=get_dates()
    reg=np.polyfit(range(len(date)),avg_bpm,1)
    print(reg)
    plot_bpm = plt.plot(date,np.polyval(reg,range(len(date))),color='red')
    return plot_bpm

def scatter_average_pace():
    avg_pace=get_average_pace()
    date=get_dates()
    scatter_average_pace=plt.scatter(date,avg_pace)
    return scatter_average_pace

def plot_pace_trend():    
    avg_pace=get_average_pace()
    date=get_dates()
    reg=np.polyfit(range(len(date)),avg_pace,1)
    print(reg)
    plot_pace = plt.plot(date,np.polyval(reg,range(len(date))),color='red')
    return plot_pace

def scatter_average_speed():
    avg_speed=get_average_speed()
    date=get_dates()
    scatter_average_speed=plt.scatter(date,avg_speed)
    return scatter_average_speed

def plot_speed_trend():    
    avg_speed=get_average_speed()
    date=get_dates()
    reg=np.polyfit(range(len(date)),avg_speed,1)
    print(reg)
    plot_speed = plt.plot(date,np.polyval(reg,range(len(date))),color='red')
    return plot_speed

def scatter_efficiency():
    average_speed=get_average_pace()
    average_bpm=get_average_bpm()
    date=get_dates()
    efficiency=average_bpm/(average_speed)*60 #New metric: beats per km
    scatter=plt.scatter(date,efficiency)
    return scatter

def plot_efficiency_trend():    
    average_speed=get_average_pace()
    average_bpm=get_average_bpm()
    date=get_dates()
    efficiency=average_bpm/(average_speed)*60 #New metric: beats per km
    reg=np.polyfit(range(len(date)),efficiency,1)
    print(reg)
    plot_efficiency = plt.plot(date,np.polyval(reg,range(len(date))),color='red')
    return plot_efficiency

def scatter_average_bpm_with_speed():
    average_bpm=get_average_bpm()
    avg_speed=get_average_speed()
    avg_date=get_dates()
    scatter=plt.scatter(avg_date,average_bpm,c=avg_speed,cmap='viridis',vmin=8, vmax=17)
    return scatter


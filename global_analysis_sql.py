from matplotlib import pyplot as plt
import numpy as np
import datetime
import sqlite3
from api_call import client
from functools import partial

conn = sqlite3.connect("sqlite_activity_database.db")
cursor = conn.cursor()



# ============== STATISTIQUES GLOBALES ==============

def number_of_activities():
    """Compte le nombre d'activités"""
    result = cursor.execute("""
        SELECT COUNT(*) FROM activity
        ;
    """).fetchone()
    return result[0]

def all_activities_id():
    """Get all_activities_id from the databse"""
    result= cursor.execute("""
        SELECT id FROM activity
                           ;""").fetchall()
    list_id=[id[0] for id in result]
    return list_id

def total_time_hours():
    """Temps total en heures"""
    result = cursor.execute("""
        SELECT SUM(moving_time) FROM activity;
    """).fetchone()
    total_time = result[0] or 0
    return int(total_time / 3600)


def last_activity_date():
    """Date de la dernière activité"""
    result = cursor.execute("""
        SELECT start_date FROM activity
        ORDER BY start_date DESC
        LIMIT 1;
    """).fetchone()
    
    if result:
        date_str = result[0].split()[0]
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    return None

        
def first_activity_date():
    """Date de la première activité"""
    result = cursor.execute("""
        SELECT start_date FROM activity
         
        ORDER BY start_date ASC
        LIMIT 1;
    """).fetchone()
    
    if result:
        date_str = result[0].split()[0]
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    return None

    
def total_distance_km():
    """Distance totale en km"""
    result = cursor.execute("""
        SELECT SUM(distance) FROM activity
         ;
    """).fetchone()
    total_distance = result[0] or 0
    return int(total_distance / 1000)


def show_global_statistics():
    """Affiche les statistiques globales"""
    print('last run date:', last_activity_date())
    print('first run date:', first_activity_date())
    print("Number of runs :", number_of_activities())
    print("Total time spent running (in hours):", total_time_hours())
    print("Total distance run (in km):", total_distance_km())


# ============== DONNÉES POUR LES GRAPHIQUES ==============

def get_average_bpm():
    """Récupère la FC moyenne pour chaque course"""
    activities = cursor.execute("""
        SELECT average_heartrate FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    avg_bpm = np.array([a[0] for a in activities])
    avg_bpm = avg_bpm[::-1]  # Inverser pour ordre chronologique
    return avg_bpm


def get_monthly_distance():
    """Get total distance per month in km"""
    activities=cursor.execute("""
            SELECT start_date, distance FROM activity""")
    monthly_distance={}
    for activity in activities:
        date_str=activity[0].split()[0]
        date_objet=datetime.datetime.strptime(date_str,"%Y-%m-%d").date()
        month_years=f"{date_objet.month}-{date_objet.year}"
        distance=activity[1]/1000
        if month_years in monthly_distance:
            monthly_distance[month_years]+=distance
        else:
            monthly_distance[month_years]=distance
    return monthly_distance
            

def get_dates():
    """Récupère les dates des courses"""
    activities = cursor.execute("""
        SELECT start_date FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    date = np.array([])
    for a in activities:
        date_str = a[0].split()[0]
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        date = np.append(date, date_obj)
    
    date = date[::-1]
    return date

def ids_from_dates(list_dates):
    ids=np.array([])
    for date in list_dates:
        result=cursor.execute("""
            SELECT id FROM activity
            WHERE start_date LIKE ?;
        """, (f"{date}%",)).fetchone()
        if result:
            ids=np.append(ids,result[0])
    return ids

def dates_from_ids(list_ids):
    """Récupère les dates des courses à partir d'une liste d'IDs"""
    date = np.array([])
    for activity_id in list_ids:
        result = cursor.execute("""
            SELECT start_date FROM activity
            WHERE id = ?;
        """, (activity_id,)).fetchone()
        
        if result:
            date_str = result[0].split()[0]
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            date = np.append(date, date_obj)
    
    return date


def get_average_pace():
    """Get average pace in (min/km)"""
    activities = cursor.execute("""
        SELECT average_speed FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    avg_pace = np.array([])
    for a in activities:
        if a[0] is not None and a[0] > 0:
            pace = 1000 / a[0]
            pace = pace // 60 + (pace % 60) / 60
            avg_pace = np.append(avg_pace, pace)
    
    avg_pace = avg_pace[::-1]
    return avg_pace


def get_average_speed():
    """Get average speed in (km/h)"""
    activities = cursor.execute("""
        SELECT average_speed FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    avg_speed = np.array([])
    for a in activities:
        if a[0] is not None:
            avg_speed = np.append(avg_speed, a[0] * 3.6)
    
    avg_speed = avg_speed[::-1]
    return avg_speed

def get_average_cadence():
    """Get average cadence in (step/min)"""
    activities = cursor.execute("""
        SELECT average_cadence FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    avg_cadence = np.array([])
    for a in activities:
        if a[0] is not None:
            #Convert for cycle cadence to run cadence
            avg_cadence = np.append(avg_cadence, a[0] * 2) 
    
    avg_cadence = avg_cadence[::-1]
    return avg_cadence

def get_elevation_gain():
    """Récupère le dénivelé positif"""
    activities = cursor.execute("""
        SELECT total_elevation_gain FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    elevation_gain = np.array([])
    for a in activities:
        elevation_gain = np.append(elevation_gain, a[0])
    
    elevation_gain = elevation_gain[::-1]
    return elevation_gain

def get_running_effectiveness():
    """Get running effectiveness (speed/watts/kg)"""
    activities = cursor.execute("""
        SELECT average_speed, average_watts,start_date FROM activity
        WHERE total_elevation_gain IS NOT NULL 
        AND average_heartrate IS NOT NULL
        AND average_speed IS NOT NULL
        AND average_watts IS NOT NULL
        ORDER BY start_date DESC;
    """).fetchall()
    
    running_effectiveness = np.array([])
    activity_with_power_date=np.array([])
    for a in activities:
        if a[1] is not None and a[1] > 0:
            weight = 64  # Assume weight has not significantly changed
            effectiveness = (a[0] * 3.6) / (a[1] / weight)
            running_effectiveness = np.append(running_effectiveness, effectiveness)
            activity_with_power_date=np.append(activity_with_power_date,a[2].split()[0])
    
    running_effectiveness = running_effectiveness[::-1]
    activity_with_power_date=activity_with_power_date[::-1]
    return running_effectiveness,activity_with_power_date

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


# ============== GRAPHIQUES ==============

def scatter_average_bpm():
    """Nuage de points: FC moyenne vs date"""
    avg_bpm = get_average_bpm()
    date = get_dates()
    scatter_average_bpm = plt.scatter(date, avg_bpm,color="#b30909")
    plt.xticks(size=8)
    return scatter_average_bpm


def plot_bpm_trend():    
    """Tendance de la FC moyenne"""
    avg_bpm = get_average_bpm()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_bpm, 1)
    print(reg)
    plot_bpm = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    plt.xticks(size=8)
    return plot_bpm

def scatter_average_cadence():
    """Scatter plot: Average cadence vs date"""
    avg_cadence = get_average_cadence()
    date = get_dates()
    scatter_average_cadence = plt.scatter(date, avg_cadence,color="#be0744")
    plt.xticks(size=8)
    return scatter_average_cadence

def plot_cadence_trend():    
    """Average cadence trend"""
    avg_cadence = get_average_cadence()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_cadence, 1)
    print(reg)
    plot_cadence = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    plt.xticks(size=8)
    return plot_cadence

def scatter_average_pace():
    """Nuage de points: Allure vs date"""
    avg_pace = get_average_pace()
    date = get_dates()
    scatter_average_pace = plt.scatter(date, avg_pace)
    plt.xticks(size=8)
    return scatter_average_pace


def plot_pace_trend():    
    """Tendance de l'allure"""
    avg_pace = get_average_pace()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_pace, 1)
    print(reg)
    plot_pace = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    plt.xticks(size=8)
    return plot_pace


def scatter_average_speed():
    """Nuage de points: Vitesse vs date"""
    avg_speed = get_average_speed()
    date = get_dates()
    scatter_average_speed = plt.scatter(date, avg_speed)
    plt.xticks(size=8)
    return scatter_average_speed


def plot_speed_trend():    
    """Tendance de la vitesse"""
    avg_speed = get_average_speed()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_speed, 1)
    print(reg)
    plot_speed = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    plt.xticks(size=8)
    return plot_speed


def scatter_efficiency():
    """Efficacité: battements par km"""
    average_speed = get_average_pace()
    average_bpm = get_average_bpm()
    date = get_dates()
    efficiency = average_bpm / (average_speed) * 60  # New metric: beats per km
    scatter = plt.scatter(date, efficiency)
    plt.xticks(size=8)
    return scatter


def plot_efficiency_trend():    
    """Tendance de l'efficacité"""
    average_speed = get_average_pace()
    average_bpm = get_average_bpm()
    date = get_dates()
    efficiency = average_bpm / (average_speed) * 60  # New metric: beats per km
    reg = np.polyfit(range(len(date)), efficiency, 1)
    print(reg)
    plot_efficiency = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    plt.xticks(size=8)
    return plot_efficiency


def scatter_average_bpm_with_speed():
    """FC avec vitesse en couleur"""
    average_bpm = get_average_bpm()
    avg_speed = get_average_speed()
    avg_date = get_dates()
    scatter = plt.scatter(avg_date, average_bpm, c=avg_speed, cmap='viridis', vmin=8, vmax=17)
    return scatter


def scatter_average_bpm_speed():
    """FC vs Vitesse, coloré par dénivelé"""
    average_bpm = get_average_bpm()
    avg_speed = get_average_speed()
    elevation_gain = get_elevation_gain()
    scatter = plt.scatter(avg_speed, average_bpm, c=elevation_gain, cmap='plasma')
    return scatter


def plot_average_bpm_speed_trend(altitude_gain_limit=100):    
    """Tendance FC vs Vitesse avec filtre dénivelé"""
    average_bpm = get_average_bpm()
    avg_speed = get_average_speed()
    elevation_gain = get_elevation_gain()
    
    # Filter to keep only runs with elevation gain below a certain limit
    filtered_avg_speed = [avg_speed[i] for i in range(len(elevation_gain)) if elevation_gain[i] < altitude_gain_limit]
    filtered_average_bpm = [average_bpm[i] for i in range(len(elevation_gain)) if elevation_gain[i] < altitude_gain_limit]
    
    reg = np.polyfit(avg_speed, average_bpm, 1)
    reg_flat = np.polyfit(filtered_avg_speed, filtered_average_bpm, 1)
    
    print(np.corrcoef(avg_speed, average_bpm))
    print(np.corrcoef(filtered_avg_speed, filtered_average_bpm))
    
    plot_bpm_speed = plt.plot(avg_speed, np.polyval(reg, avg_speed), color='red')
    plot_bpm_speed_flat = plt.plot(filtered_avg_speed, np.polyval(reg_flat, filtered_avg_speed), color='green')
    
    plt.xticks(size=8)
    return plot_bpm_speed

def plot_corrcoef_evolution():
    corr_coefficients=[]
    for alt_gain_limit in np.linspace(10,2000,500):
        average_bpm=get_average_bpm()
        avg_speed=get_average_speed()
        elevation_gain=get_elevation_gain()
        #Filter to keep only runs with elevation gain below a certain limit
        filtered_avg_speed=[avg_speed[i] for i in range(len(elevation_gain)) if elevation_gain[i]<alt_gain_limit]
        filtered_average_bpm=[average_bpm[i] for i in range(len(elevation_gain)) if elevation_gain[i]<alt_gain_limit]
        corr_coefficients.append(np.corrcoef(filtered_avg_speed, filtered_average_bpm)[0,1])
    corrcoef_evolution=plt.plot(np.linspace(10,2000,500),corr_coefficients)
    plt.xticks(size=8)
    return corrcoef_evolution

def plot_settings(function, title,xlabel,ylabel,filename,grid=False,save=False):
    
    plot=function()
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if grid :
        plt.grid()
    if save:
        plt.savefig("./Results/"+filename, dpi=300)
    
    return plot

def plot_monthly_distance(save=False):
    monthly_distance=get_monthly_distance()
    months=list(monthly_distance.keys())
    distances=list(monthly_distance.values())
    plt.plot(months, distances, linestyle='-', color='#FC4C02',
              marker='o', markeredgecolor='#FC4C02', markerfacecolor='none')
    plt.xticks(rotation=90)
    plt.xticks(size=8)
    plt.xlabel("Month-Year")
    plt.ylabel("Monthly distance (km)")
    plt.title("Totale distance run per months")
    plt.grid(axis='y')
    save_plt = plt.savefig("./Results/monthly_distance.png",dpi=300) if save else None
    plt.tight_layout()
    plt.xticks(size=8)

def scatter_running_effectiveness():
    """Plot running effectiveness over time"""
    running_effectiveness,date=get_running_effectiveness()
    
    plt.scatter(date,running_effectiveness,color="#d408bc")
    plt.title("Running effectiveness over time")
    plt.xlabel("Date")
    plt.ylabel("Running effectiveness (speed/watts/kg)")
    plt.tight_layout()
    plt.xticks(size=8)

def plot_running_effectiveness_trend():
    """Plot running effectiveness trend"""
    running_effectiveness,date=get_running_effectiveness()
    
    reg = np.polyfit(range(len(date)), running_effectiveness, 1)
    print(reg)
    plot_efficiency = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    plt.xticks(size=8)
    plt.tight_layout()
    return plot_efficiency
    

# ============== USE CASES ==============

if __name__ == "__main__":
    
    # Exemple de graphique
    
    plt.figure()
    plot_settings(plot_corrcoef_evolution,xlabel='elevation gain (m)',
                                     ylabel='Correlation coefficient ',
                                     title='Correlation coefficient variation following the data set max elevation',
                                     filename='correlation_coefficient_settings.png',
                                     grid=True,save=False)



    plt.figure()
    scatter_average_bpm_speed()
    partial_plot_average_bpm_speed_trend=partial(plot_average_bpm_speed_trend, altitude_gain_limit=18)
    plot_settings(partial_plot_average_bpm_speed_trend,
                  title='Average Heart Rate vs Average Speed',
                  xlabel='Average Speed (km/h)',
                  ylabel='Average Heart Rate (bpm)',
                  filename='average_bpm_speed.png',
                  grid=False, save=False)
    plt.legend(['Runs','Global trend','Low elevation Trend'])
    
    plt.figure()
    scatter_average_cadence()
    plot_settings(plot_cadence_trend,
                  title='Average Cadence over years',
                  xlabel='date',
                  ylabel='Average Cadence (step/min)',
                  filename='average_cadence_over_time.png',
                  grid=False, save=True)
    plt.xticks(size=8)
    plt.savefig('./Results/average_cadence_over_time.png',dpi=300)

    plt.figure()
    scatter_average_bpm()
    plot_settings(plot_bpm_trend,
                  title='Average heartrate over years',
                  xlabel='date',
                  ylabel='Average heartrate (pulse/min)',
                  filename='average_heartrate_over_time.png',
                  grid=False, save=True)
    plt.xticks(size=8)
    plt.savefig('./Results/average_heartrate_over_time.png',dpi=300)   

    plt.figure()
    scatter_efficiency()
    plot_settings(plot_efficiency_trend,
                  title='Average efficiency over years',
                  xlabel='date',
                  ylabel='Average efficiency (pulse/km)',
                  filename='average_efficiency_over_time.png',
                  grid=False, save=True)
    plt.xticks(size=8)
    plt.savefig('./Results/average_efficiency_over_time.png',dpi=300)

    plt.figure()
    plot_monthly_distance(save=True)

    plt.figure()
    scatter_average_pace()
    plot_settings(plot_pace_trend,
                  title='Average pace over years',
                  xlabel='date',
                  ylabel='Average pace (min/km)',
                  filename='average_pace_over_time.png',
                  grid=False, save=True)
    plt.xticks(size=8)
    plt.savefig('./Results/average_pace_over_time.png',dpi=300) 

    plt.figure()
    scatter_running_effectiveness()
    plot_settings(plot_running_effectiveness_trend,
                  title='Running effectiveness over years',
                  xlabel='date',
                  ylabel="Running effectiveness (speed/watts/kg)",
                  filename='running_effectiveness_over_time.png',
                  grid=False,save=True)
    
    show_global_statistics()

    plt.show()
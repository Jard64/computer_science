from matplotlib import pyplot as plt
import numpy as np
import datetime
import sqlite3
from api_call import client

conn = sqlite3.connect("sqlite_activity_database_copy.db")
cursor = conn.cursor()



# ============== STATISTIQUES GLOBALES ==============

def number_of_activities():
    """Compte le nombre d'activités"""
    result = cursor.execute("""
        SELECT COUNT(*) FROM activity
        ;
    """).fetchone()
    return result[0]


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


def get_dates():
    """Récupère les dates des courses"""
    activities = cursor.execute("""
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


def get_average_pace():
    """Récupère l'allure moyenne (min/km)"""
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
    """Récupère la vitesse moyenne (km/h)"""
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
    scatter_average_bpm = plt.scatter(date, avg_bpm)
    return scatter_average_bpm


def plot_bpm_trend():    
    """Tendance de la FC moyenne"""
    avg_bpm = get_average_bpm()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_bpm, 1)
    print(reg)
    plot_bpm = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    return plot_bpm


def scatter_average_pace():
    """Nuage de points: Allure vs date"""
    avg_pace = get_average_pace()
    date = get_dates()
    scatter_average_pace = plt.scatter(date, avg_pace)
    return scatter_average_pace


def plot_pace_trend():    
    """Tendance de l'allure"""
    avg_pace = get_average_pace()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_pace, 1)
    print(reg)
    plot_pace = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    return plot_pace


def scatter_average_speed():
    """Nuage de points: Vitesse vs date"""
    avg_speed = get_average_speed()
    date = get_dates()
    scatter_average_speed = plt.scatter(date, avg_speed)
    return scatter_average_speed


def plot_speed_trend():    
    """Tendance de la vitesse"""
    avg_speed = get_average_speed()
    date = get_dates()
    reg = np.polyfit(range(len(date)), avg_speed, 1)
    print(reg)
    plot_speed = plt.plot(date, np.polyval(reg, range(len(date))), color='red')
    return plot_speed


def scatter_efficiency():
    """Efficacité: battements par km"""
    average_speed = get_average_pace()
    average_bpm = get_average_bpm()
    date = get_dates()
    efficiency = average_bpm / (average_speed) * 60  # New metric: beats per km
    scatter = plt.scatter(date, efficiency)
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
    return corrcoef_evolution



# ============== EXEMPLE D'UTILISATION ==============

if __name__ == "__main__":
    
    # Exemple de graphique
    plt.figure()
    
    plot_corrcoef_evolution()
    plt.title('Correlation coefficient variation following the data set max elevation')
    plt.xlabel('elevation gain (m)')
    plt.ylabel('Correlation coefficient ')
    plt.grid()
    plt.savefig('./Results/correlation_coefficient.png', dpi=300)

    plt.figure()
    scatter_average_bpm_speed()
    plot_average_bpm_speed_trend(altitude_gain_limit=18)
    plt.legend(['Runs','Global trend','Low elevation Trend'])
    plt.title('Average Heart Rate vs Average Speed')
    plt.colorbar(label='Elevation Gain (m)')
    plt.xlabel('Average Speed (km/h)')
    plt.ylabel('Average Heart Rate (bpm)')
    plt.savefig('./Results/average_bpm_speed.png', dpi=300)
    plt.show()
"""
Module for specific activity analysis from Strava data.
Handles time-series analysis, windowing, clustering, and GAP model regression.
"""

from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import r2_score
import sqlite3
import json
import numpy as np
import scipy.interpolate as interpolate
from global_analysis_sql import all_activities_id, dates_from_ids, ids_from_dates

# ============================================================================
# CONSTANTS
# ============================================================================

COLORS = ['green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

# Training zone definitions (km/h)
SPEED_ZONE_FOOTING = [0, 12.5]
SPEED_ZONE_TEMPO = [12.5, 16.5]
SPEED_ZONE_VMA = [16.5, 21]
SPEED_ZONE_SPRINT = [21, 30]

# Heart rate zone definitions (bpm)
HR_ZONE_FOOTING = [100, 155]
HR_ZONE_TEMPO = [155, 180]
HR_ZONE_VMA = [180, 200]

# Gradient limit
GRAD_LIMIT_HIGH=20
GRAD_LIMIT_LOW=-20

# Database connection
conn = sqlite3.connect("sqlite_activity_database.db")
cursor = conn.cursor()


# ============================================================================
# DATA RETRIEVAL FUNCTIONS
# ============================================================================

def ids_restricted(restriction_types):
    """
    Get all activity IDs where specified stream types are not null.
    
    Args:
        restriction_types: List of stream types to check (e.g., ['heartrate', 'velocity_smooth'])
    
    Returns:
        List of activity IDs that have all specified stream types
    """
    query = "SELECT id FROM streams WHERE stream_type IN ("
    query += ",".join(f"'{restriction}'" for restriction in restriction_types)
    query += (") AND stream_value IS NOT NULL AND stream_value != '[]' "
              "GROUP BY id HAVING COUNT(DISTINCT stream_type) = ?;")
    
    activities_id = cursor.execute(query, (len(restriction_types),)).fetchall()
    return [activity[0] for activity in activities_id]


def activity_stream(activity_id, stream_type):
    """
    Retrieve a specific stream and distance data for an activity.
    
    Args:
        activity_id: Strava activity ID
        stream_type: Type of stream to retrieve (e.g., 'heartrate', 'velocity_smooth')
    
    Returns:
        Tuple of (stream_data, distance_data) as numpy arrays
        Returns ([None], [None]) if data is not available
    """
    stream_query = """
        SELECT stream_value FROM streams 
        WHERE id=? AND stream_type=?;
    """
    stream_result = cursor.execute(stream_query, (activity_id, stream_type)).fetchone()
    
    distance_query = """
        SELECT stream_value FROM streams 
        WHERE id=? AND stream_type='distance';
    """
    distance_result = cursor.execute(distance_query, (activity_id,)).fetchone()
    
    try:
        stream_data = json.loads(stream_result[0])
        distance_data = json.loads(distance_result[0])
    except (TypeError, AttributeError):
        return np.array([None]), np.array([None])
    
    return np.array(stream_data), np.array(distance_data)


# ============================================================================
# WINDOWING AND PREPROCESSING FUNCTIONS
# ============================================================================

def windowed_average(activity_id, stream_type, data_min, data_max, 
                     std_threshold=5, window_time=60):
    """
    Resample activity stream data using window averaging.
    Filters out windows with high standard deviation or out-of-bounds averages.
    
    Args:
        activity_id: Strava activity ID
        stream_type: Type of stream to process
        data_min: Minimum acceptable average value
        data_max: Maximum acceptable average value
        std_threshold: Maximum allowed standard deviation within window
        window_time: Window size in seconds
    
    Returns:
        Array of averaged values (None for rejected windows)
    """
    data, _ = activity_stream(activity_id, stream_type)
    time, _ = activity_stream(activity_id, 'time')
    
    # Convert velocity from m/s to km/h
    if stream_type == 'velocity_smooth':
        data = np.array([s * 3.6 if s is not None else None for s in data])
    
    # Calculate window size from time data
    try:
        time_step = time[time > time[0]][0] - time[0]
        window_size = int(window_time / time_step)
    except (IndexError, ZeroDivisionError):
        return None
    
    averaged_data = []
    
    for i in range(0, len(data), window_size):
        window = data[i:i + window_size]
        window = np.array(window)
        
        # Check window validity
        if len(window) != window_size:
            averaged_data.append(None)
            continue
        
        window_avg = np.mean(window)
        window_std = np.std(window)
        
        # Filter based on statistical criteria
        is_valid = (window_std < std_threshold and 
                   data_min < window_avg < data_max)
        
        # Additional filter for velocity: reject high acceleration
        if stream_type == 'velocity_smooth' and is_valid:
            acceleration = np.gradient(window)
            if np.mean(acceleration) > 0.5:
                averaged_data.append(None)
                continue
        
        averaged_data.append(window_avg if is_valid else None)
    
    return np.array(averaged_data, dtype=float)


def global_windowed_average():
    """
    Compute windowed averages across all activities for HR, gradient, and speed.
    
    Returns:
        Tuple of (heart_rate, gradient, speed) as concatenated numpy arrays
    """
    all_activities = ids_restricted(['heartrate', 'grade_smooth', 'velocity_smooth'])
    
    # Collect windowed data for each activity
    windows_hr = [
        windowed_average(activity_id, 'heartrate', 130, 185)
        for activity_id in all_activities
        if windowed_average(activity_id, 'heartrate', 130, 185) is not None
    ]
    
    windows_grad = [
        windowed_average(activity_id, 'grade_smooth', GRAD_LIMIT_LOW, GRAD_LIMIT_HIGH)
        for activity_id in all_activities
        if windowed_average(activity_id, 'grade_smooth', GRAD_LIMIT_LOW, GRAD_LIMIT_HIGH) is not None
    ]
    
    windows_speed = [
        windowed_average(activity_id, 'velocity_smooth', 8, 20)
        for activity_id in all_activities
        if windowed_average(activity_id, 'velocity_smooth', 8, 20) is not None
    ]
    
    # Concatenate all windows
    all_hr = np.concatenate(windows_hr)
    all_grad = np.concatenate(windows_grad)
    all_speed = np.concatenate(windows_speed)
    
    # Remove NaN values
    mask = ~(np.isnan(all_hr) | np.isnan(all_grad) | np.isnan(all_speed))
    
    return all_hr[mask], all_grad[mask], all_speed[mask]


def windowed_normalized_average_efficiency():
    """
    Compute normalized efficiency (HR/speed) across all activities.
    Normalization is done per activity relative to flat terrain efficiency.
    
    Returns:
        Array of normalized efficiency values
    """
    normalized_efficiency = np.array([])
    
    for activity_id in ids_restricted(['heartrate', 'grade_smooth', 'velocity_smooth']):
        window_hr = windowed_average(activity_id, 'heartrate', 130, 185)
        window_speed = windowed_average(activity_id, 'velocity_smooth', 8, 20)
        window_gradient = windowed_average(activity_id, 'grade_smooth', GRAD_LIMIT_LOW, GRAD_LIMIT_HIGH)
        
        # Filter out NaN values
        mask = ~(np.isnan(window_hr) | np.isnan(window_gradient) | np.isnan(window_speed))
        clean_hr = window_hr[mask]
        clean_gradient = window_gradient[mask]
        clean_speed = window_speed[mask]
        
        # Calculate raw efficiency
        window_efficiency = clean_hr / clean_speed
        
        # Normalize by flat terrain efficiency (|gradient| < 5%)
        flat_mask = np.abs(clean_gradient) < 5
        
        average_flat_efficiency = np.mean(window_efficiency[flat_mask])
        normalized = window_efficiency / average_flat_efficiency
        normalized_efficiency = np.append(normalized_efficiency, normalized)

    return normalized_efficiency


# ============================================================================
# REGRESSION AND MODELING FUNCTIONS
# ============================================================================

def efficiency_regression_polynomial(regression_degree,return_true_values=False):
    """
    Compute Grade Adjusted Pace (GAP) model using polynomial regression.
    Creates a metric independent of elevation gain.
    
    Args:
        regression_degree: Degree of polynomial for regression
    
    Returns:
        polynomial_function

    """
    # Get windowed data
    _, gradient_data, _ = global_windowed_average()
    efficiency_data = windowed_normalized_average_efficiency()
    
    # Remove NaN values
    mask = ~(np.isnan(efficiency_data) | np.isnan(gradient_data))
    clean_efficiency = efficiency_data[mask]
    clean_gradient = gradient_data[mask]
    
    # Polynomial regression
    coeffs = np.polyfit(clean_gradient, clean_efficiency, regression_degree)
    poly_function = np.poly1d(coeffs)  # Use poly1d, not Polynomial

    if not return_true_values:
        return poly_function
    else:
        return poly_function,clean_efficiency,clean_gradient



def efficiency_regression_spline(return_true_values=False,smoothing=0.0):
    """
    Compute Grade Adjusted Pace (GAP) model using cubic B-spline regression.
    Creates a metric independent of elevation gain.
    Do not use that function for the moment, need to smooth and reduce noise on the measurements
    Way of improvement: gaussian_kde, use weight for make_splrep
    Args:
    
    Returns:
        B-spline function

    """
    # Get windowed data
    _, gradient_data, _ = global_windowed_average()
    efficiency_data = windowed_normalized_average_efficiency()
    
    # Remove NaN values
    mask = ~(np.isnan(efficiency_data) | np.isnan(gradient_data))
    clean_efficiency = efficiency_data[mask]
    clean_gradient = gradient_data[mask]
    
    # Remove duplicates values of Gradient
    reverse_clean_gradient=clean_gradient[::-1]


    # Sort the values of gradient and remove duplicates
    clean_gradient=clean_gradient[::-1]
    clean_efficiency[::-1]
    sorted_clean_gradient,indices_sorted_clean_gradient=np.unique(clean_gradient,return_index=True)
    sorted_clean_efficiency=clean_efficiency[indices_sorted_clean_gradient]
   

    # Polynomial regression
    standard_dev=clean_efficiency.std()

    bspline = interpolate.make_splrep(sorted_clean_gradient,sorted_clean_efficiency,s=smoothing)
    

    if not return_true_values:
        return bspline
    else:
        return bspline,sorted_clean_efficiency,sorted_clean_gradient




# ============================================================================
# CLUSTERING FUNCTIONS
# ============================================================================

def clustering(data_x, data_y, n_clusters=5):
    """
    Cluster data points using K-means to identify training zones.
    
    Args:
        data_x: First feature (e.g., speed)
        data_y: Second feature (e.g., heart rate)
        n_clusters: Number of clusters
    
    Returns:
        Tuple of (labels, centroids)
    """
    data_points = np.array(list(zip(data_x, data_y)))
    
    # Normalize data for better clustering
    scaler = StandardScaler()
    data_normalized = scaler.fit_transform(data_points)
    
    # K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(data_normalized)
    
    # Transform centroids back to original scale
    centroids_original = scaler.inverse_transform(kmeans.cluster_centers_)
    
    print(f"Inertia: {kmeans.inertia_}")
    print(f"Number of clusters: {n_clusters}")
    
    return labels, centroids_original


def scatter_centers(data_x, data_y, n_clusters=5):
    """
    Plot cluster centroids on current figure.
    
    Args:
        data_x: First feature
        data_y: Second feature  
        n_clusters: Number of clusters
    """
    _, centroids = clustering(data_x, data_y, n_clusters)
    
    for i, center in enumerate(centroids):
        plt.scatter(center[0], center[1], 
                   color=COLORS[i], marker='X', s=200)
        
# ============================================================================
# REGRESSION QUALITY
# ============================================================================

def regression_quality(regression='polynomial',regression_degree=2,smoothing=0.0):
    """
    Determine quality of the regression using the R squared score
    
    Args:
        regression: {"polynomial","spline"}, the type of regression
        regression_degree: The number of degree for the polynomial regression 
    """
    if regression=='polynomial':
        f_pred,y_true,x_true=efficiency_regression_polynomial(regression_degree=regression_degree,return_true_values=True)
        y_pred=np.array([f_pred(x) for x in x_true])
        score=r2_score(y_true,y_pred)
        return score
    elif regression=='spline':
        f_pred,y_true,x_true=efficiency_regression_polynomial(regression_degree=regression_degree,return_true_values=True,smoothing=smoothing)
        y_pred=np.array([f_pred.__call__(x) for x in x_true])
        score=r2_score(y_true,y_pred)
        return score


# ============================================================================
# MAIN ANALYSIS AND PLOTTING
# ============================================================================

def plot_specific_activity(activity_id):
    """
    Create scatter plot of HR vs speed for a specific activity.
    
    Args:
        activity_id: Strava activity ID
        date: Date string for title
    """
    bpm, _ = activity_stream(activity_id, 'heartrate')
    speed, _ = activity_stream(activity_id, 'velocity_smooth')
    time, _ = activity_stream(activity_id, 'time')
    date=dates_from_ids([activity_id])[0]
    
    # Convert speed to km/h
    speed = speed * 3.6
    
    plt.figure(figsize=(10, 6))
    plt.scatter(speed, bpm, c=time, cmap='seismic', alpha=0.6)
    plt.xlabel("Speed (km/h)")
    plt.ylabel("Heart rate (bpm)")
    plt.title(f"Heart rate vs Speed for activity of {date}")
    plt.colorbar(label='Time (s)')
    plt.grid(True, alpha=0.3)
    
    filename = f"./Results/specific_activity_fc_vs_speed_{activity_id}_{date}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Saved: {filename}")


def plot_gap_model(regression='polynomial',smoothing=0):
    """
    Create plot showing GAP model regression results.
    """
    _,gradient_data,_=global_windowed_average()

    # Get efficiency data
    efficiency_data = windowed_normalized_average_efficiency()
        
    # Sort gradient for smooth plotting
    gradient_sorted = np.sort(gradient_data)

    if regression=='spline':
        
        # Compute regression (degree 2)
        spline_function = efficiency_regression_spline(smoothing=smoothing)
        
        # Compute GAP adjustment factor
        # Normalize by flat terrain value (gradient = 0)
        gap_factor = spline_function 
        origin_value= gap_factor.__call__(0)
        gap_values = [(gap_factor.__call__(grad)/origin_value - 1) for grad in gradient_sorted]
        

    elif regression == 'polynomial':
        # Compute regression (degree 2)
        
        poly_function = efficiency_regression_polynomial(regression_degree=2)
        # Compute GAP adjustment factor
        # Normalize by flat terrain value (gradient = 0)
        gap_factor = poly_function / poly_function(0) - 1
        gap_values = [gap_factor(grad) for grad in gradient_sorted]

    else:
        return None
 
        # Plot
    plt.figure(figsize=(12, 6))
    plt.scatter(gradient_data, efficiency_data - 1, 
            alpha=0.3, s=10, label='Data points')
    plt.plot(gradient_sorted, gap_values, 
            'r-', linewidth=2, label='GAP model')
    plt.xlabel("Gradient (%)")
    plt.ylabel("Normalized efficiency - 1")
    plt.title("Grade Adjusted Pace (GAP) Model")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filename = "./Results/gap_model_regression_"+regression+".png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Saved: {filename}")
    return gap_values

    


# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

if __name__ == "__main__":


    # date_semi="2025-12-06"
    # print(date_semi)
    # id_semi=ids_from_dates([date_semi])[0]
    # _,gradient_data,_=global_windowed_average()
    # poly_function = efficiency_regression_polynomial(regression_degree=2)
    # efficiency_data = windowed_normalized_average_efficiency()
    # gradient_sorted = np.sort(gradient_data)
    # speed,distance=activity_stream(id_semi,'velocity_smooth')
    # time,distance=activity_stream(id_semi,'time')
    # gradient,distance=activity_stream(id_semi,'grade_smooth')
    # speed=[s*3.6 for s in speed]  #convert m/s to km/h

    # gap_factor = poly_function / poly_function(0) - 1
    # gap_values=np.array([gap_factor(grad) for grad in gradient])
    # mean_speed=np.mean(speed)
    # adjusted_speed=speed*(1+gap_values)

    # mean_adjusted_speed=np.mean(adjusted_speed)
    # mean_adjusted_pace=60/mean_adjusted_speed
    # mean_pace=60/mean_speed
    # print(str(int(mean_adjusted_pace))+":"+str((mean_adjusted_pace-int(mean_adjusted_pace))*0.6)[2:5])
    # print(str(int(mean_pace))+":"+str((mean_pace-int(mean_pace))*0.6)[2:5])


    # date_course="2025-06-29"
    # print()
    # print(date_course)
    # id_semi=ids_from_dates([date_course])[0]
    # _,gradient_data,_=global_windowed_average()
    # poly_function = efficiency_regression_polynomial(regression_degree=2)
    # efficiency_data = windowed_normalized_average_efficiency()
    # gradient_sorted = np.sort(gradient_data)
    # speed,distance=activity_stream(id_semi,'velocity_smooth')
    # time,distance=activity_stream(id_semi,'time')
    # gradient,distance=activity_stream(id_semi,'grade_smooth')
    # speed=[s*3.6 for s in speed]  #convert m/s to km/h

    # gap_factor = poly_function / poly_function(0) - 1
    # gap_values=np.array([gap_factor(grad) for grad in gradient])
    # mean_speed=np.mean(speed)
    # adjusted_speed=speed*(1+gap_values)
    
    # mean_adjusted_speed=np.mean(adjusted_speed)
    # mean_adjusted_pace=60/mean_adjusted_speed
    # mean_pace=60/mean_speed
    # print(str(int(mean_adjusted_pace))+":"+str((mean_adjusted_pace-int(mean_adjusted_pace))*0.6)[2:5])
    # print(str(int(mean_pace))+":"+str((mean_pace-int(mean_pace))*0.6)[2:5])
    


    plot_gap_model(regression='spline',smoothing=1)
      
    



    plt.show()
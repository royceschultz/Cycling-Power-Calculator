def compute_global_metrics(df):
    if df is None or df.empty:
        return {
            "Total Time": "-",
            "Total Distance": "-",
            "Average Speed": "-",
            "Average Power": "-"
        }
    # Total ride time
    if 'timestamp' in df and df['timestamp'].notnull().any():
        t0 = df['timestamp'].iloc[0]
        t1 = df['timestamp'].iloc[-1]
        delta = t1 - t0
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            total_time = f"{hours}hr {minutes}min {seconds}sec"
        elif minutes > 0:
            total_time = f"{minutes}min {seconds}sec"
        else:
            total_time = f"{seconds}sec"
    else:
        total_time = "-"
    # Total distance (in km)
    if 'distance' in df and df['distance'].notnull().any():
        total_distance = df['distance'].max() / 1000  # meters to km
        total_distance = f"{total_distance:.2f} km"
    else:
        total_distance = "-"
    # Average speed (in km/h)
    if 'speed' in df and df['speed'].notnull().any():
        avg_speed = df['speed'].mean() * 3.6  # m/s to km/h
        avg_speed = f"{avg_speed:.1f} km/h"
    else:
        avg_speed = "-"
    # Average power (in W)
    if 'power' in df and df['power'].notnull().any():
        avg_power = df['power'].mean()
        avg_power = f"{avg_power:.0f} W"
    else:
        avg_power = "-"
    return {
        "Total Time": total_time,
        "Total Distance": total_distance,
        "Average Speed": avg_speed,
        "Average Power": avg_power,
    }

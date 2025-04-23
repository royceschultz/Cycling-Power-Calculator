import os
import fitparse
import pandas as pd

BASE_FOLDER = 'rides'

def load_fit_file(filename):
    path = os.path.join(BASE_FOLDER, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {filename} not found in {BASE_FOLDER}")
    fitfile = fitparse.FitFile(path)

    data = []
    record_types = {
        'timestamp',
        'position_lat', 'position_long', 'altitude',
        'power', 'heart_rate', 'cadence',
        'speed', 'distance', 'temperature',
        'gps_accuracy', 'grade',
        'enhanced_altitude', 'enhanced_speed',
    }

    types_found = set()
    for record in fitfile.get_messages("record"):
        # Records can contain multiple pieces of data (ex: timestamp, latitude, longitude, etc)
        point = {}

        for field in record:
            # Print the name and value of the data (and the units if it has any)
            if field.units:
                metric = field.name, field.units
            else:
                metric = field.name

            if metric not in types_found:
                types_found.add(metric)

            if field.name in record_types:
                point[field.name] = field.value

        data.append(point)

    df = pd.DataFrame(data)

    # Convert latitude and longitude from semi-circles to degrees
    # degrees = semicircles * (180 / 2^31)

    if 'position_lat' in df:
        df['position_lat'] = df['position_lat'].apply(
            lambda x: x * (180 / 2**31) if pd.notnull(x) else x
        )
    if 'position_long' in df:
        df['position_long'] = df['position_long'].apply(
            lambda x: x * (180 / 2**31) if pd.notnull(x) else x
        )

    # Fill columns with NA if they are not present in the data
    for col in record_types:
        if col not in df.columns:
            df[col] = None

    print(f"Types found in {filename}:")
    for metric in types_found:
        print(metric)
    print(f"Total records: {len(df)}")
    # Print the nth record (values at the start may be null)
    n = 10
    if len(df) > n:
        print(f"Record {n}:")
        print(df.iloc[n])
    return df

def load_gpx_file(filename):
    raise NotImplementedError("GPX file loading is not implemented yet.")
    path = os.path.join(BASE_FOLDER, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {filename} not found in {BASE_FOLDER}")
    return None

def load_file(filename):
    print(f"Loading file: {filename}")
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.fit':
        return load_fit_file(filename)
    elif ext == '.gpx':
        return load_gpx_file(filename)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def get_ride_files(filetype_filter="Both"):
    if not os.path.exists(BASE_FOLDER):
        return [], {}
    if filetype_filter == "Both":
        exts = ('.fit', '.gpx')
    elif filetype_filter == ".fit":
        exts = ('.fit',)
    else:
        exts = ('.gpx',)
    files = [
        f for f in os.listdir(BASE_FOLDER)
        if os.path.isfile(os.path.join(BASE_FOLDER, f)) and f.endswith(exts)
    ]
    # Map filename to full path
    file_map = {f: os.path.join(BASE_FOLDER, f) for f in files}
    return files, file_map

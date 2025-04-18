
import datetime

from ipywidgets import DatePicker
from IPython.display import display
from dateutil import tz

# we use pandas to visualize the results we get
import pandas as pd

# The stride client library, used to make the calls to the stride api
import stride



TO_CINEMA = "29094"

METROPOLIN_REF = "15"
IL_TIME = datetime.timezone(datetime.timedelta(hours=3))


def get_scheduled_rides(from_day, to_day, route_short_name):
    return stride.get('/gtfs_routes/list', {'date_from': from_day, 'date_to': to_day, 'route_short_name': route_short_name,}, pre_requests_callback='print')

def get_actual_rides(from_day, to_day, line_refs, operator_refs):
    siri_rides = stride.get('/siri_rides/list', {
    'scheduled_start_time_from': datetime.datetime.combine(from_day, datetime.time(), datetime.timezone.utc),
    'scheduled_start_time_to': datetime.datetime.combine(to_day, datetime.time(23,59), datetime.timezone.utc),
    'siri_route__line_refs': ','.join(line_refs),
    'siri_route__operator_refs': ','.join(operator_refs),
    'order_by': 'scheduled_start_time asc'
}, pre_requests_callback='print')
    return siri_rides


def get_first_ride_on_hour(rides, hour):
    for siri_ride in rides:
        if siri_ride['scheduled_start_time'].hour >= hour:
            return siri_ride


def get_stops_for_ride(siri_ride):
    siri_ride_stops = stride.get('/siri_ride_stops/list', {
    'siri_ride_ids': str(siri_ride['id']),
    'order_by': 'order asc',
    'expand_related_data': True}, pre_requests_callback='print')
    return siri_ride_stops

def get_stops():
    stops = stride.get('/siri_stops/list', {
    'limit': 5,
    'expand_related_data': True}, pre_requests_callback='print')
    return stops


def get_snapshots():
    stops = stride.get('/siri_snapshots/list', {
    'limit': 1,
    'expand_related_data': True}, pre_requests_callback='print')
    return stops

def get_stop_by_id(id):
    stops = stride.get('/siri_stops/get', {
    'id': id,
    'expand_related_data': True}, pre_requests_callback='print')
    return stops


def find_good_table(from_date_widget, to_date_widget):
    gtfs = get_scheduled_rides(from_day=from_date_widget.value, to_day=to_date_widget.value, route_short_name="8")
    siri = get_actual_rides(from_day=from_date_widget.value, to_day=to_date_widget.value, line_refs=[TO_CINEMA], operator_refs=[METROPOLIN_REF])
    ride = get_first_ride_on_hour(siri, 8)

    print(ride)

    siri_ride_stops = get_stops_for_ride(ride)
    df = pd.DataFrame(siri_ride_stops)
    df.loc[:, [
        'order', 'gtfs_stop__city', 'gtfs_stop__name', 'gtfs_ride_stop__departure_time', 
        'nearest_siri_vehicle_location__recorded_at_time'
    ]]

    # if the ride has at least one stop departure time, it's a good table
    if any([stop["gtfs_ride_stop__departure_time"] is not None for stop in siri_ride_stops]):
        print(df)
        print("on date", from_date_widget)
        return from_date_widget
    # if the ride has at least one stop name, it's a good table
    if any([stop["gtfs_stop__name"] is not None for stop in siri_ride_stops]):
        print(df)
        print("on date", from_date_widget)
        return from_date_widget

def print_column(table, column_name):
    print(column_name)
    ([print(str(entry[column_name])) for entry in table])

def get_ref_from_short_name(shortname):
    t = DatePicker(description='Date:', value=datetime.date(2025,1,1)).value
    return stride.get('/gtfs_routes/list', {
    'date_from': t, 'date_to': t,
    'route_short_name': shortname,}, pre_requests_callback='print')
    

def search_good_table():
    for i in range(3,4):
        for j in range(1,2):
            date_widget = DatePicker(description='Date:', value=datetime.date(2025,i,j))
            print(i,j)
            if find_good_table(date_widget, date_widget):
                break


def get_locations(from_day, to_day, line_refs, operator_refs):
    return stride.get('/siri_vehicle_locations/list', {
    'limit': 1000000,
    'siri_routes__line_ref': line_refs,
    'siri_routes__operator_ref': operator_refs,
    'siri_rides__schedualed_start_time_from': from_date,
    'siri_rides__schedualed_start_time_to': to_date,
    'order_by': 'recorded_at_time desc'}, pre_requests_callback='print')

from_date = DatePicker(description='Date:', value=datetime.date(2025,1,1))
to_date = DatePicker(description='Date:', value=datetime.date(2025,1,2))



def get_mean_time_between_location_records():
    # Get the mean time between location records for a specific date range
    means = []
    for i in range(1,30):
        from_date = datetime.datetime(2025, 1, i, 8 , 59, tzinfo=tz.gettz('Israel'))
        to_date = datetime.datetime(2025,1, i, 9, 31, tzinfo=tz.gettz('Israel'))

        locations = get_locations(from_date, to_date, [TO_CINEMA], [METROPOLIN_REF])
        print(len(locations))

        df = pd.DataFrame(locations)



        if 'recorded_at_time' not in df.columns:
            print("Column 'recorded_at_time' not found in DataFrame.")
            continue
        recorded_at_time_set = set(df['recorded_at_time'])
        # Calculate the mean distance (in time) between two consecutive time records in the set
        if len(recorded_at_time_set) > 1:
            # Convert the set to a sorted list of datetime objects
            sorted_times = sorted(recorded_at_time_set)
            # Calculate the time differences between consecutive records
            time_differences = [t2 - t1 for t1, t2 in zip(sorted_times[:-1], sorted_times[1:])]
            # Calculate the mean time difference
            mean_time_difference = sum(time_differences, datetime.timedelta()) / len(time_differences)
            print("Mean time difference between consecutive records:", mean_time_difference)

            means.append(mean_time_difference)
        else:
            print("Not enough time records to calculate mean time difference.")

        print("Unique recorded_at_time values:", len(recorded_at_time_set))

    [print(mean) for mean in means]

def check_how_dist_from_start_works():
    # this function is used to prove that distance from start is always increasing:
    # distance is distance rode and not euclidean distance from start
    LINE_REF = "17518"
    OPERATOR_REF = "32"

    from_date = datetime.datetime(2025, 1, 16, 8 , 59, tzinfo=tz.gettz('Israel'))
    to_date = datetime.datetime(2025,1, 16, 9, 15, tzinfo=tz.gettz('Israel'))

    locations = get_locations(from_date, to_date, [LINE_REF], [OPERATOR_REF])
    df = pd.DataFrame(locations)
    print(df)
    # Print the selected columns: 'lon', 'lat', 'distance_from_journey_start', 'recorded_at_time'
    if {'lon', 'lat', 'distance_from_journey_start', 'recorded_at_time'}.issubset(df.columns):
        # Set pandas to display all rows
        pd.set_option('display.max_rows', None)
        print(df[['recorded_at_time', 'lon', 'lat', 'distance_from_journey_start']])
    else:
        print("One or more required columns are missing in the DataFrame.")


    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import matplotlib.cm as cm


    if {'lon', 'lat', 'recorded_at_time'}.issubset(df.columns):
        # Convert 'recorded_at_time' to datetime if it's not already
        df['recorded_at_time'] = pd.to_datetime(df['recorded_at_time'])

        # Normalize the recorded_at_time to a range of 0 to 1 for coloring
        norm = mcolors.Normalize(vmin=df['recorded_at_time'].min().timestamp(), vmax=df['recorded_at_time'].max().timestamp())
        colormap = plt.get_cmap('viridis')

        # Map the normalized times to colors
        colors = df['recorded_at_time'].apply(lambda x: colormap(norm(x.timestamp())))

        # Plot the points
        plt.figure(figsize=(10, 6))
        plt.scatter(df['lon'], df['lat'], c=colors, edgecolor='k', s=50)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Location Points Colored by Recorded Time')
        #plt.colorbar(cm.ScalarMappable(norm=norm, cmap=colormap), label='Recorded Time')
        plt.show()
    else:
        print("One or more required columns are missing in the DataFrame.")


    if {'lon', 'lat', 'distance_from_journey_start'}.issubset(df.columns):
        # Convert 'distance_from_journey_start' to datetime if it's not already
        df['distance_from_journey_start'] = pd.to_datetime(df['distance_from_journey_start'])

        # Normalize the distance_from_journey_start to a range of 0 to 1 for coloring
        norm = mcolors.Normalize(vmin=df['distance_from_journey_start'].min().timestamp(), vmax=df['distance_from_journey_start'].max().timestamp())
        colormap = plt.get_cmap('viridis')

        # Map the normalized times to colors
        colors = df['distance_from_journey_start'].apply(lambda x: colormap(norm(x.timestamp())))

        # Plot the points
        plt.figure(figsize=(10, 6))
        plt.scatter(df['lon'], df['lat'], c=colors, edgecolor='k', s=50)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Location Points Colored by Recorded Time')
        #plt.colorbar(cm.ScalarMappable(norm=norm, cmap=colormap), label='Recorded Time')
        plt.show()
    else:
        print("One or more required columns are missing in the DataFrame.")


LINE_REF = "8177"
LINE_REF = "8176"
OPERATOR_REF = "15"
from_date = datetime.datetime(2025, 1, 17, 8 , 59, tzinfo=tz.gettz('Israel'))
to_date = datetime.datetime(2025,1, 17, 9, 15, tzinfo=tz.gettz('Israel'))

locations = get_locations(from_date, to_date, [LINE_REF], [OPERATOR_REF])

df = pd.DataFrame(locations)
if {'lon', 'lat', 'distance_from_journey_start', 'recorded_at_time','siri_ride_stop_id'}.issubset(df.columns):
    # Set pandas to display all rows
    pd.set_option('display.max_rows', None)
    print(df[['recorded_at_time', 'lon', 'lat', 'distance_from_journey_start', 'siri_ride_stop_id']])

    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    if {'lon', 'lat', 'siri_ride_stop_id'}.issubset(df.columns):
        # Get unique siri_ride_stop_id values
        unique_stop_ids = df['siri_ride_stop_id'].unique()

        # Create a color map for the unique siri_ride_stop_id values
        colormap = plt.get_cmap('tab10')
        colors = {stop_id: colormap(i / len(unique_stop_ids)) for i, stop_id in enumerate(unique_stop_ids)}

        # Plot the points
        plt.figure(figsize=(10, 6))
        for stop_id in unique_stop_ids:
            stop_data = df[df['siri_ride_stop_id'] == stop_id]
            plt.scatter(stop_data['lon'], stop_data['lat'], label=f'Stop ID: {stop_id}', color=colors[stop_id], edgecolor='k', s=50)
        # Ensure the graph has the same scale for x and y axes
        plt.axis('equal')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Location Points Colored by siri_ride_stop_id')
        plt.legend()
        plt.show()
    else:
        print("One or more required columns are missing in the DataFrame.")
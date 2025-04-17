
import datetime

from ipywidgets import DatePicker
from IPython.display import display

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
    

def main():
    for i in range(3,4):
        for j in range(1,2):
            date_widget = DatePicker(description='Date:', value=datetime.date(2025,i,j))
            print(i,j)
            if find_good_table(date_widget, date_widget):
                break

main()
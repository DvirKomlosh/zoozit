

import pandas as pd
from api_functions import get_locations, get_start_time_for_ride_id
from ipywidgets import DatePicker
import datetime
from dateutil import tz


OPERATOR_REFS = {
    "METROPOLIN": 15,
}

LINE_REFS = {
    "8_to_cinema": 29094
}



FROM_TIME = datetime.datetime(2025, 4, 20, 0 , 0, tzinfo=tz.gettz('Israel'))
TO_TIME = datetime.datetime(2025, 4, 26, 0 , 0, tzinfo=tz.gettz('Israel'))


def get_time_brackets(siri_ride_ids):
    scheduled_start_times = dict()
    for ride_id in siri_ride_ids:
        scheduled_start_time = get_start_time_for_ride_id(ride_id)
        scheduled_start_time = scheduled_start_time.astimezone(tz.gettz('Israel'))
        scheduled_start_time = scheduled_start_time.time()
        if scheduled_start_time not in scheduled_start_times:
            scheduled_start_times[scheduled_start_time] = []
        scheduled_start_times[scheduled_start_time].append(ride_id)
    return scheduled_start_times

def main():
    locations = get_locations(FROM_TIME, TO_TIME, LINE_REFS["8_to_cinema"], OPERATOR_REFS["METROPOLIN"])
    df = pd.DataFrame(locations)
    siri_ride_ids = df['siri_ride__id'].unique().tolist()
    brackets = get_time_brackets(siri_ride_ids)
    for bracket in brackets:
        print(bracket, brackets[bracket])


if __name__ == "__main__":
    main()
from typing import Dict, List, Tuple
from api_functions import get_locations_for_kmenas
import pandas as pd
from datetime import datetime
from dateutil import tz

from consts import (
    K,
    LINE_REFS,
    OPERATOR_REFS,
    SIRI_STOP_ORDER,
    SIRI_STOPS_TO_NAME,
    Latitute,
    LineRef,
    LocationId,
    Longtitude,
    OperatorRef,
    SiriRideStopId,
    SiriStopId,
)
import time

from get_data import get_arrival_data
from stop_to_stop import generate_time_diffs


def next_stop_eta(
    recorded_at_time: datetime,
    lon: Longtitude,
    lat: Latitute,
    start_time: datetime,
    next_stop_id: SiriStopId,
    line_ref: LineRef,
    operator_ref: OperatorRef,
    k=K,
) -> int:
    """
    knn implementation to get the ETA for the next stop
    returns the estimated seconds to arrive at the next stop
    """
    locations, arrival_dict = get_relavent_locations(
        start_time, next_stop_id, line_ref, operator_ref
    )
    seconds_to_arrive = run_knn(locations, arrival_dict, recorded_at_time, lon, lat, k)
    return seconds_to_arrive


def get_relavent_locations(
    start_time: datetime,
    next_stop_id: SiriStopId,
    line_ref: LineRef,
    operator_ref: OperatorRef,
) -> pd.DataFrame:
    """
    returns all relevant locations for knn in a dataframe.
    a location is relevant if it is:
        - in the same time
        - the same day of week
        - has the same next_stop_id
    """
    location_ids, siri_ride_stop_ids, arrival_dict = get_relavent_ids(
        start_time, next_stop_id
    )
    if len(location_ids) == 0 or len(siri_ride_stop_ids) == 0:
        raise Exception(
            "no valid precalculated arrival time found for the given parameters. can't estimate"
        )
    locations = get_locations_for_kmenas(
        location_ids, siri_ride_stop_ids, line_ref, operator_ref
    )
    return pd.DataFrame(locations), arrival_dict


def get_relavent_ids(
    start_time: datetime, next_stop_id: SiriStopId
) -> Tuple[List[LocationId], List[SiriRideStopId], Dict[SiriRideStopId, datetime]]:
    """
    returns all relavent Location ids, siri_ride_stop_ids that are relevant for the knn.
    also returns a dictionary of arrival times for each stop.
    """

    day_of_week = start_time.strftime("%A")
    start_hour = start_time.strftime("%H:%M:%S")
    data = get_arrival_data()

    filtered_data = data[
        (data["start_time"] == start_hour)
        & (data["day_of_week"] == day_of_week)
        & ((data["siri_stop_id"]) == next_stop_id)
    ]

    location_ids = list(set(filtered_data["id"].tolist()))
    siri_ride_stop_ids = filtered_data["siri_ride_stop_id"].tolist()
    arrival_dict = dict(
        zip(filtered_data["siri_ride_stop_id"], filtered_data["arrival_time"])
    )

    return location_ids, siri_ride_stop_ids, arrival_dict


def calculate_distance(
    location, lon: Longtitude, lat: Latitute, recorded_at_time: datetime
) -> float:
    """
    calculates knn distance between a location and a lon, lat, recorded_at_time values of the current location.

    location: a row from a locations dataframe
    """
    other_lon = float(location["lon"])
    other_lat = float(location["lat"])
    distance = ((other_lon - lon) ** 2 + (other_lat - lat) ** 2) ** 0.5
    return distance


def sort_locations(
    locations: pd.DataFrame, lon: Longtitude, lat: Latitute, recorded_at_time: datetime
) -> pd.DataFrame:
    """
    returns a sorted dataframe of locations based on the distance from the given lon, lat, recorded_at_time.
    """
    locations["distance"] = locations.apply(
        lambda row: calculate_distance(row, lon, lat, recorded_at_time), axis=1
    )
    sorted_locations = locations.sort_values(by="distance")
    return sorted_locations


def calculate_time_to_arrive(location) -> int:
    """
    calculates the time to arrive (in seconds) for a given location.
    based on the arrival time and the recorded at time.
    """
    arrival_time = datetime.strptime(location["arrival_time"], "%H:%M:%S").time()
    recorded_at_time = (
        location["recorded_at_time"].astimezone(tz.gettz("Israel")).time()
    )
    seconds_to_arrive = (
        datetime.combine(datetime.min, arrival_time)
        - datetime.combine(datetime.min, recorded_at_time)
    ).total_seconds()
    return seconds_to_arrive


def run_knn(locations, arrival_dict, recorded_at_time, lon, lat, k):
    """
    finds the K nearest neighbors to the given lon, lat, recorded_at_time,
    and returns the estimated seconds to arrive at the next stop.
    """
    sorted = sort_locations(locations, lon, lat, recorded_at_time)
    k = min(k, len(sorted))

    sorted = sorted.iloc[:k]
    sorted["arrival_time"] = sorted["siri_ride_stop_id"].map(arrival_dict)
    sorted["time_to_arrive"] = sorted.apply(calculate_time_to_arrive, axis=1)

    if (sorted["distance"] == 0).any():
        return sorted.loc[sorted["distance"] == 0, "time_to_arrive"].iloc[0]

    sorted["inverse_distance"] = 1 / sorted["distance"]

    inverse_distance_sum = sorted["inverse_distance"].sum()

    weighted_sum = (sorted["inverse_distance"] * sorted["time_to_arrive"]).sum()
    astimated_seconds_to_arrive = weighted_sum / inverse_distance_sum

    if astimated_seconds_to_arrive == 0:
        print(sorted)

    return astimated_seconds_to_arrive


def next_stops_eta(
    recorded_at_time: datetime,
    lon: Longtitude,
    lat: Latitute,
    start_time: datetime,
    next_stop_id: SiriStopId,
    line_ref: LineRef,
    operator_ref: OperatorRef,
    k=K,
) -> Dict[SiriStopId, int]:
    """
    uses knn to get the ETAs for the next stop, and uses averages of past data to determine the next stops' ETAs.
    """
    seconds_to_arrive = next_stop_eta(
        recorded_at_time,
        lon,
        lat,
        start_time,
        next_stop_id,
        line_ref,
        operator_ref,
        k,
    )
    seconds_to_arrive = int(seconds_to_arrive)  # add 1 second to avoid rounding issues
    stop_index = SIRI_STOP_ORDER.index(next_stop_id)
    next_stops = SIRI_STOP_ORDER[stop_index + 1 :]
    stop_to_stop_times = generate_time_diffs(start_time)

    arrival_times = dict()
    arrival_times[next_stop_id] = seconds_to_arrive
    last_stop = next_stop_id
    for stop in next_stops:
        arrival_times[stop] = arrival_times[last_stop] + stop_to_stop_times[stop]
        last_stop = stop

    return arrival_times


def print_etas(arrival_times: Dict[SiriStopId, int], recorded_at_time: datetime):
    """
    prints the estimated times of arrival for each stop in a readable format.
    """
    for stop, seconds in arrival_times.items():
        arrival_time = recorded_at_time + pd.to_timedelta(seconds, unit="s")
        stop_name = SIRI_STOPS_TO_NAME[stop]
        print(
            f"Stop {stop_name[::-1]} will be reached in {seconds} seconds, at {arrival_time.time()}"
        )


def main():
    lon = 34.846114
    lat = 32.134802

    time_str = "08:15:00"
    recorded_at_time_str = "08:20:00"
    date_str = "2024-01-01"
    start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    recorded_at_time = datetime.strptime(
        f"{date_str} {recorded_at_time_str}", "%Y-%m-%d %H:%M:%S"
    )
    next_stop_id = 2391

    start = time.time()
    times = next_stops_eta(
        recorded_at_time,
        lon,
        lat,
        start_time,
        next_stop_id,
        LINE_REFS["8_to_cinema"],
        OPERATOR_REFS["METROPOLIN"],
    )
    print_etas(times, recorded_at_time)
    print("Calculation time:", time.time() - start)
    return


if __name__ == "__main__":
    main()

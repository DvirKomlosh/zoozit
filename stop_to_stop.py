import datetime
import time
from typing import Dict
from api_functions import get_stop_position
from consts import (
    SIRI_STOP_ORDER,
    SIRI_STOPS_TO_CODE,
    STOP_LOCATIONS,
    LINE_REFS,
    OPERATOR_REFS,
    SiriStopId,
)
from knn import get_arrival_data, next_stop_eta


def generate_time_diffs(start_time: datetime.datetime) -> Dict[SiriStopId, int]:

    data = get_arrival_data()

    day_of_week = start_time.strftime("%A")
    start_hour = start_time.strftime("%H:%M:%S")
    data = get_arrival_data()

    filtered_data = data[
        (data["start_time"] == start_hour) & (data["day_of_week"] == day_of_week)
    ]

    rides = filtered_data["id"].unique()
    all_times = {stop: list() for stop in SIRI_STOP_ORDER}
    for i in range(len(SIRI_STOP_ORDER) - 1):
        curr = SIRI_STOP_ORDER[i]
        next = SIRI_STOP_ORDER[i + 1]

        for ride in rides:

            curr_entry = filtered_data[
                (filtered_data["id"] == ride) & (filtered_data["siri_stop_id"] == curr)
            ]
            next_entry = filtered_data[
                (filtered_data["id"] == ride) & (filtered_data["siri_stop_id"] == next)
            ]
            if len(curr_entry) != 1 or len(next_entry) != 1:
                if len(curr_entry) == 0 or len(next_entry) == 0:
                    continue
                else:
                    raise ValueError(
                        f"Expected one entry for a ride, found more then one with ride {ride}, stop: {curr}, or stop: {next}"
                    )

            curr_time = curr_entry["arrival_time"].values[0]
            next_time = next_entry["arrival_time"].values[0]
            curr_time = datetime.datetime.strptime(curr_time, "%H:%M:%S")
            next_time = datetime.datetime.strptime(next_time, "%H:%M:%S")

            diff = (next_time - curr_time).total_seconds()
            all_times[curr].append(diff)

    for stop in SIRI_STOP_ORDER[:-1]:
        if len(all_times[stop]) == 0:
            raise ValueError(f"No data found for stop {stop} at {start_time.time()}")

    times = {
        stop: sum(all_times[stop]) / len(all_times[stop])
        for stop in SIRI_STOP_ORDER[:-1]
    }
    return times


def main():
    start = time.time()

    start_time = datetime.datetime.strptime(f"2024-01-01 10:45:00", "%Y-%m-%d %H:%M:%S")
    time_diffs = generate_time_diffs(start_time)
    total = 0
    for stop, diff in time_diffs.items():
        print(f"{stop} :{int(diff)} seconds")
        total += int(diff)
    print(
        f"Total time from {SIRI_STOP_ORDER[0]} to {SIRI_STOP_ORDER[-1]}: {int(total)} seconds"
    )

    print("calculation time:"time.time() - start)
    return


if __name__ == "__main__":
    main()

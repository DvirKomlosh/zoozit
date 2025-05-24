import time
from typing import List
import pandas as pd
from api_functions import (
    get_locations,
    get_locations_by_ride_id,
    get_start_time_for_ride_id,
    get_stop_id,
)
import datetime
from dateutil import tz
import os

from consts import (
    START_HOUR,
    END_HOUR,
    OPERATOR_REFS,
    LINE_REFS,
    LineRef,
    LocationId,
    OperatorRef,
    SiriRideId,
    SiriRideStopId,
    SiriStopId,
)
from tqdm import tqdm
from typing import NewType


def generate_time_ranges(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    start_hour: datetime.time,
    end_hour: datetime.time,
) -> List[tuple[datetime.datetime, datetime.datetime]]:
    """
    Generate a list of tuples (start,end).
    where for each day between start_time and end_time, there is a tuple:
    start = start hour, end = end hour - at that day.
    """
    date_range = pd.date_range(start=start_time.date(), end=end_time.date(), freq="D")

    time_ranges = []
    for single_date in date_range:
        day_start = datetime.datetime.combine(
            single_date, datetime.time(start_hour, 0), tzinfo=start_time.tzinfo
        )
        day_end = datetime.datetime.combine(
            single_date, datetime.time(end_hour, 0), tzinfo=start_time.tzinfo
        )
        time_ranges.append((day_start, day_end))

    return time_ranges


def get_relevant_siri_ride_ids(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    line_ref: LineRef,
    operator_ref: OperatorRef,
    start_hour: datetime.time = START_HOUR,
    end_hour: datetime.time = END_HOUR,
) -> List[SiriRideId]:
    """
    Get relevant SIRI ride IDs based on the specified time range and line reference.
    """
    time_ranges = generate_time_ranges(start_time, end_time, start_hour, end_hour)
    all_siri_ride_ids = set()

    for start, end in time_ranges:
        locations_df = pd.DataFrame(get_locations(start, end, line_ref, operator_ref))
        if "siri_ride__id" not in locations_df.columns:
            continue
        siri_ride_ids = locations_df["siri_ride__id"].unique().tolist()
        all_siri_ride_ids.update(siri_ride_ids)

    return all_siri_ride_ids


def generate_data(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    line_ref: LineRef,
    operator_ref: OperatorRef,
) -> pd.DataFrame:
    """
    Generate data for the specified time range and line reference.
    If the data already exists in a CSV file, it will be loaded from there.
    """

    file_name = f"{start_time.date()}-{end_time.date()},REF{line_ref}.csv"
    if not os.path.exists(file_name):

        results_df = pd.DataFrame(
            columns=[
                "id",
                "date",
                "day_of_week",
                "start_time",
                "siri_stop_id",
                "siri_ride_stop_id",
                "arrival_time",
            ]
        )
        siri_ride_ids = get_relevant_siri_ride_ids(
            start_time, end_time, line_ref, operator_ref
        )
        print(f"\nFound {len(siri_ride_ids)} relevant unique ride ids!\n")

        for i, id in enumerate(tqdm(siri_ride_ids, desc="Processing rides")):
            start_time = get_start_time_for_ride_id(id)
            day_of_week = start_time.strftime("%A")
            date = start_time.astimezone(tz.gettz("Israel")).date()
            start_time = start_time.astimezone(tz.gettz("Israel")).time()
            arrival_times = get_arrival_times([id])

            for stop_ids, arrival_time in arrival_times.items():
                siri_stop_id, siri_ride_stop_id = int(stop_ids[0]), int(stop_ids[1])
                arrival_time = arrival_time.astimezone(tz.gettz("Israel")).time()

                results_df = pd.concat(
                    [
                        results_df,
                        pd.DataFrame(
                            [
                                {
                                    "id": id,
                                    "date": date,
                                    "day_of_week": day_of_week,
                                    "start_time": start_time,
                                    "siri_ride_stop_id": siri_ride_stop_id,
                                    "siri_stop_id": siri_stop_id,
                                    "arrival_time": arrival_time,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

        results_df.to_csv(file_name, index=False)
        return results_df
    return pd.read_csv(file_name)


def find_id_of_closest_to_stop(
    loc_df: pd.DataFrame, siri_ride_stop_id: SiriRideStopId
) -> LocationId:
    """
    gets the location id of the closest location to the given siri_ride_stop_id.
    """
    filtered_df = loc_df[loc_df["siri_ride_stop_id"] == siri_ride_stop_id]
    if not filtered_df.empty:
        max_distance_row = filtered_df.loc[
            filtered_df["distance_from_journey_start"].idxmax()
        ]
        return max_distance_row["id"]
    return None


def get_arrival_times(
    ids: List[SiriRideId],
) -> dict[tuple[SiriStopId, SiriRideStopId], datetime.datetime]:
    """
    return a dict stop : arrival time for that id
    based on the locations of the ride.

    this function assumes that the last recorded location is "at the stop":
    the recorded time is considered to be the time of arrival to the stop.
    """

    locations = get_locations_by_ride_id(ids)

    loc_df = pd.DataFrame(locations)
    times = dict()
    for siri_ride_stop_id in set(loc_df["siri_ride_stop_id"]):
        entry_id = find_id_of_closest_to_stop(loc_df, siri_ride_stop_id)
        siri_stop_id = get_stop_id(siri_ride_stop_id)
        if entry_id is not None:
            times[(siri_stop_id, siri_ride_stop_id)] = loc_df[loc_df["id"] == entry_id][
                "recorded_at_time"
            ].iloc[0]
    return times


def main():
    from_time = datetime.datetime(2024, 12, 1, 0, 1, tzinfo=tz.gettz("Israel"))
    to_time = datetime.datetime(2024, 12, 2, 0, 0, tzinfo=tz.gettz("Israel"))
    data = generate_data(
        from_time, to_time, LINE_REFS["8_to_cinema"], OPERATOR_REFS["METROPOLIN"]
    )
    print(data)


if __name__ == "__main__":
    start = time.time()
    main()
    print(time.time() - start)

import datetime
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
from knn import next_stop_eta


def generate_time_diffs(start_time: datetime.datetime) -> Dict[SiriStopId, int]:
    time_diffs = dict()
    for i in range(len(SIRI_STOP_ORDER) - 1):
        curr = SIRI_STOP_ORDER[i]
        next = SIRI_STOP_ORDER[i + 1]
        lon, lat = STOP_LOCATIONS[curr]

        time_diffs[curr] = next_stop_eta(
            start_time,
            lon,
            lat,
            start_time,
            next,
            line_ref=LINE_REFS["8_to_cinema"],
            operator_ref=OPERATOR_REFS["METROPOLIN"],
            k=30,
        )

    return time_diffs


def main():
    start_time = datetime.datetime.strptime(f"2024-01-01 08:15:00", "%Y-%m-%d %H:%M:%S")
    time_diffs = generate_time_diffs(start_time)
    for stop, diff in time_diffs.items():
        print(f"{stop} :{int(diff)} seconds")

    return
    lons = []
    lats = []
    for stop, code in SIRI_STOPS_TO_CODE.items():
        lon, lat = get_stop_position(code)
        print(f"{stop}:({lon},{lat}),")
        lons.append(lon)
        lats.append(lat)

    import matplotlib.pyplot as plt

    plt.axis("equal")
    plt.scatter(lons, lats, label=stop)

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Stop Positions")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()

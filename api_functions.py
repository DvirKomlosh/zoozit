import datetime
from typing import Dict, List, Union
import stride

pre_requests_callback = "print"
pre_requests_callback = None

from consts import (
    LineRef,
    LocationId,
    OperatorRef,
    SiriRideId,
    SiriRideStopId,
    SiriStopId,
    SiriStopCode,
)


def comma_separated_string(l) -> str:
    if hasattr(l, "__iter__") and not isinstance(l, str):
        return ",".join([str(i) for i in l])
    return str(l)


def get_locations_for_kmenas(
    locations_ids: List[LocationId],
    siri_ride_stop_ids: List[SiriRideStopId],
    line_ref: LineRef,
    operator_ref: OperatorRef,
) -> List[Dict]:

    return stride.get(
        "/siri_vehicle_locations/list",
        {
            "limit": 1000000,
            "siri_ride_stop_ids": comma_separated_string(siri_ride_stop_ids),
            "siri_rides__ids": comma_separated_string(locations_ids),
            "siri_routes__line_ref": line_ref,
            "siri_routes__operator_ref": operator_ref,
            "order_by": "recorded_at_time desc",
        },
        pre_requests_callback=pre_requests_callback,
    )


def get_locations(
    from_day: datetime.datetime,
    to_day: datetime.datetime,
    line_refs: List[LineRef],
    operator_refs: List[LineRef],
) -> List[Dict]:
    return stride.get(
        "/siri_vehicle_locations/list",
        {
            "limit": 1000000,
            "siri_routes__line_ref": comma_separated_string(line_refs),
            "siri_routes__operator_ref": comma_separated_string(operator_refs),
            "siri_rides__schedualed_start_time_from": from_day,
            "siri_rides__schedualed_start_time_to": to_day,
            "order_by": "recorded_at_time desc",
        },
        pre_requests_callback=pre_requests_callback,
    )


def get_locations_by_ride_id(ride_ids: List[SiriRideId]) -> List[Dict]:
    return stride.get(
        "/siri_vehicle_locations/list",
        {
            "limit": 1000000,
            "siri_rides__ids": ride_ids,
            "order_by": "recorded_at_time desc",
        },
        pre_requests_callback=pre_requests_callback,
    )


def get_start_time_for_ride_id(ride_id: SiriRideId) -> datetime.datetime:
    return stride.get(
        "/siri_rides/get",
        {
            "id": ride_id,
        },
        pre_requests_callback=pre_requests_callback,
    )["scheduled_start_time"]


def get_stop_id(stop_id: SiriRideId) -> SiriStopId:
    return stride.get(
        "/siri_ride_stops/get",
        {"id": stop_id},
        pre_requests_callback=pre_requests_callback,
    )["siri_stop_id"]


def get_stop_name(stop_id: SiriStopId) -> SiriStopCode:
    return stride.get(
        "/siri_stops/get", {"id": stop_id}, pre_requests_callback=pre_requests_callback
    )["code"]

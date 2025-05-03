from typing import List
import stride


def get_locations(from_day, to_day, line_refs, operator_refs):
    return stride.get('/siri_vehicle_locations/list', {
    'limit': 1000000,
    'siri_routes__line_ref': line_refs,
    'siri_routes__operator_ref': operator_refs,
    'siri_rides__schedualed_start_time_from': from_day,
    'siri_rides__schedualed_start_time_to': to_day,
    'order_by': 'recorded_at_time desc'}, pre_requests_callback='print')


def get_locations_by_ride_id(ride_ids: List[str]):
    return stride.get('/siri_vehicle_locations/list', {
    'limit': 1000000,
    'siri_rides__ids': ride_ids,
    'order_by': 'recorded_at_time desc'}, pre_requests_callback='print')

def get_start_time_for_ride_id(ride_id: str):
    return stride.get('/siri_rides/get', {
    'id': ride_id,}, pre_requests_callback='print')['scheduled_start_time']

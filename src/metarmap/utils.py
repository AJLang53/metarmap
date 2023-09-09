from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import typing
numeric = typing.Union[int, float, complex]     # Define numeric type
from collections import deque
from time import perf_counter
import random
import astral, astral.sun

def is_between_sunrise_sunset(latitude: float, longitude: float, time: datetime) -> bool:
    """Returns True if the time provided at location is between sunrise and sunset"""
    observer = astral.Observer(latitude=latitude, longitude=longitude)
    sunrise = astral.sun.sunrise(observer=observer, date = datetime.date(datetime.now())).time()
    sunset = astral.sun.sunset(observer=observer, date = datetime.date(datetime.now())).time()
    return sunrise < time < sunset

def quickselect_median(dset: typing.Iterable[numeric], pivot_fn: typing.Callable[[typing.Iterable[numeric]], numeric] = random.choice) -> float:
    """Returns the set median in average O(n) time"""
    if (len(dset)) % 2 == 1:
        return quickselect(dset, len(dset) // 2, pivot_fn)
    else:
        return 0.5* (quickselect(dset, len(dset) / 2 - 1, pivot_fn) + quickselect(dset, len(dset) / 2, pivot_fn))
    
def quickselect(l: typing.Iterable[numeric], k: int, pivot_fn: typing.Callable[[numeric], numeric]) -> numeric:
    """
    Select the kth element in l (0 based)
    :param l: list of numerics
    :param k: Index
    :param pivot_fn: Function to choose a pivot, defaults to random.choice
    :return: the kth element of l
    """
    if len(l) == 1:
        assert k == 0
        return l[0]

    pivot = pivot_fn(l)

    lows = [el for el in l if el < pivot]
    highs = [el for el in l if el > pivot]
    pivots = [el for el in l if el == pivot]

    if k < len(lows):
        return quickselect(lows, k, pivot_fn)
    elif k < len(lows) + len(pivots):
        # We got lucky and guessed the median
        return pivots[0]
    else:
        return quickselect(highs, k - len(lows) - len(pivots), pivot_fn)

def median_function_timer(fixed_length_queue: deque[numeric], function: typing.Callable[[], None], *args, **kwargs):
    """Time a function with no return"""
    start: float = 0
    stop: float = 0
    start = perf_counter()
    function(*args, **kwargs)
    stop = perf_counter()
    delta = stop - start
    fixed_length_queue.appendleft(delta)
    return quickselect_median(fixed_length_queue)

def split_new_line_text(string: str) -> typing.List:
    """Split text divided by newline characters, excluding blank lines"""
    return [element for element in string.split('\n') if element != ""]

def check_dict_for_key_path(key_path: typing.List[typing.Any], dict: dict, default: typing.Any | None = None) -> typing.Any | None:
    """
    Check if key path is in dictionary, return the value if it is
        key_path means it will check the keys in order, ex:
        dict[key_path[0]][key_path[1]]...
    Otherwise, return default (None if not provided)
    """
    # Base Case, no key path
    if len(key_path) == 0:
        return None

    # Base Case, single key
    elif len(key_path) == 1:
        try:
            val = dict(key_path[0])
        except KeyError:
            val = default
        return val

    else:
        try:
            new_dict = dict[key_path[0]]
            val = check_dict_for_key_path(key_path[1:],new_dict,default=default)
        except KeyError:
            val = default
        return val

def getStationList():
    stationList = []
    path = os.path.join('data','GB_chicago_station_list.txt')
    with open(path) as f:
        for station in f:
            station = station.strip()
            stationList.append(station)
    return stationList

def parse_station_map(path):
    '''
    The station map should be a csv file with column 1 = station ID and column 2 = LED index
    '''

    station_map = {}
    with open(path) as f:
        for line in f:
            station_id = line.split(',')[0]
            led_index = line.split(',')[1]
            station_map[station_id] = int(led_index)
    return station_map
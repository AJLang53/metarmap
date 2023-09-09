import logging
from pathlib import Path
from datetime import datetime
import typing
numeric = typing.Union[int, float, complex]     # Define numeric type
from collections import deque
from time import perf_counter
import random

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

def initializeRotatingLog(fileLevel = logging.WARNING):
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(fileLevel)

    # Send INFO messages to the console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(ch)

    # Log files in a logs folder at the main application level. Create this directory if it does not exist
    log_dir = Path(__file__).parent.parent.parent / 'logs'
    if not log_dir.exists():
        Path.mkdir(log_dir)

    # Log file should be a file labeled date_metarmap
    log_file_name = '{}_metarmap.log'.format(datetime.now().strftime('%Y-%m-%dT%H-%M-%S'))
    # LOG_FILEPATH = os.path.join(logDir,logFileName)
    LOG_FILEPATH = log_dir / log_file_name

    # Setup a Rotating Log File with fixed size for continuous logging
    # Allocate 250mb to this task, keeps file 10mb each
    rotHandler = logging.handlers.RotatingFileHandler(LOG_FILEPATH, maxBytes=10*1024*1024, backupCount=25)
    rotHandler.setFormatter(logging.Formatter('[%(asctime)s] %(name)-16s :: %(levelname)-8s :: %(message)s'))
    logger.addHandler(rotHandler)
import sys
import logging
from datetime import timedelta
from collections import deque

from threading import Event

from metarmap.loop import MainLoop
from metarmap.METAR_Map_Config import METAR_MAP_Config, METAR_COLOR_CONFIG
from METAR.ADDS_METAR_Thread import ADDSMETARThread

from metarmap.utils import median_function_timer

def main():
    logger = logging.getLogger('main_function')

    # Get the configuration
    from pathlib import Path
    map_config  = METAR_MAP_Config(logging_level=logging.DEBUG, station_map = {
        'KSLE': 0,
        'KONP': 1,
        'KOSH': 2
    },
    metar_colors_config=METAR_COLOR_CONFIG(),
    led_driver= None
    )

    # Generate the events used to communicate with this thread
    ADDSMETAR_stop_request = Event()
    ADDSMETAR_stop_request.clear()

    # Generate the thread object itself
    adds_metar_thread = ADDSMETARThread(stop_request=ADDSMETAR_stop_request,
                                            stations = map_config.station_map,
                                                update_interval=timedelta(seconds = 5),
                                                stale_data_time=timedelta(seconds = 20)
    )
    adds_metar_thread.daemon = True
    adds_metar_thread.start()

    # Create the MainLoop object to run the map
    metarmap_loop = MainLoop(config = map_config, metar_source=adds_metar_thread)

    # Run the loop as many times as you'd like
    metarmap_loop_timer_buffer: deque[float] = deque([],maxlen=25)
    try:
        while True:
            loop_length = median_function_timer(metarmap_loop_timer_buffer, metarmap_loop.loop)
            print(f'METARMAP_loop Run Time: {loop_length}')
            if metarmap_loop.metar_source.is_running:
                print(f'METAR AGE: {metarmap_loop.current_metar_state_age}')
    except KeyboardInterrupt:
        logger.critical('Loop Ended by Keyboard Interrupt')

if __name__ == '__main__':
    sys.exit(main())
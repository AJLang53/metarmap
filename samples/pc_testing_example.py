import sys
import logging
from datetime import timedelta
from collections import deque
from pathlib import Path

from threading import Event

from metarmap import MainLoop, METAR_MAP_Config, METAR_COLOR_CONFIG, Day_Night_Dimming_Config
from METAR import ADDSMETARThread

from metarmap.Logging import initialize_basic_log_stream, initialize_rotating_file_log

from metarmap.utils import median_function_timer

def main():
    logger = logging.getLogger('main_function')
    initialize_basic_log_stream(logger, logging.INFO)
    initialize_rotating_file_log(logging.getLogger(), output_directory = Path(__file__).parent, output_name = 'test_rot_log', maxBytes= 10*1024*1024, backupCount=25)

    # Construct a configuration
    station_map = {
        'KSLE': 0,
        'KONP': 1,
        'KOSH': 2
    }
    metar_colors_config=METAR_COLOR_CONFIG()
    led_driver= None
    day_night_dimming_config = Day_Night_Dimming_Config(
        day_night_dimming=True,
        brightness_dim=0.1,
        use_sunrise_sunet=True,
        day_night_latitude=45,
        day_night_longitude=-93
    )

    map_config  = METAR_MAP_Config(
        station_map=station_map,
        led_driver=led_driver,
        metar_colors_config=metar_colors_config,
        day_night_dimming_config=day_night_dimming_config
    
    )

    # Construct the METAR Source
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
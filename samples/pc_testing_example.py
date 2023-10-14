import sys
import logging
from datetime import timedelta
from collections import deque
from pathlib import Path

from threading import Event

from metarmap import MainLoop, METAR_MAP_Config, METAR_COLOR_CONFIG, Day_Night_Dimming_Config, Wind_Animation_Config
from METAR import ADDSMETARThread

from metarmap.Logging import initialize_basic_log_stream, initialize_rotating_file_log

from metarmap.utils import median_function_timer

station_map = {
    'KSLE': 0,
    'KONP': 1,
    'KOSH': 2
}

# Generate the thread object itself
adds_metar_thread = ADDSMETARThread(
    stations = station_map,
    update_interval=timedelta(minutes = 15),
    stale_data_time=timedelta(minutes = 90)
)

# Construct a configuration

metar_colors_config=METAR_COLOR_CONFIG()
led_driver= None
day_night_dimming_config = Day_Night_Dimming_Config(
    day_night_dimming=True,
    brightness_dim=0.1,
    use_sunrise_sunet=True,
    day_night_latitude=45,
    day_night_longitude=-93
)
wind_animation_config = Wind_Animation_Config(
    enabled=True,
    blink_threshold=5,
    high_wind_threshold=15
)

map_config  = METAR_MAP_Config(
    name = 'PC_Test_map',
    metar_source = adds_metar_thread,
    station_map=station_map,
    led_driver=led_driver,
    metar_colors_config=metar_colors_config,
    day_night_dimming_config=day_night_dimming_config,
    wind_animation_config=wind_animation_config
)

def main():
    logger = logging.getLogger('main_function')
    initialize_basic_log_stream(logger, logging.INFO)
    initialize_rotating_file_log(logging.getLogger(), output_directory = Path(__file__).parent.parent / 'logs', output_name = f'{map_config.name}', max_bytes= 10*1024*1024, backup_count=25)

    # Create the MainLoop object to run the map
    with MainLoop(config = map_config) as metarmap_loop:

        # Run the loop as many times as you'd like
        metarmap_loop_timer_buffer: deque[float] = deque([],maxlen=25)
        try:
            while True:
                loop_length = median_function_timer(metarmap_loop_timer_buffer, metarmap_loop.loop)
                # print(f'METARMAP_loop Run Time: {loop_length}')
                # if metarmap_loop.metar_source.is_running:
                #     print(f'METAR AGE: {metarmap_loop.current_metar_state_age}')
        except KeyboardInterrupt:
            logger.critical('Loop Ended by Keyboard Interrupt')

if __name__ == '__main__':
    sys.exit(main())
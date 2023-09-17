import sys
import logging
from datetime import timedelta
from collections import deque
from pathlib import Path

from threading import Event

# Module imports
from metarmap.MainLoop import MainLoop
from metarmap.METAR_Map_Config import METAR_MAP_Config, METAR_COLOR_CONFIG

# METAR SOURCE
from METAR.ADDS_METAR_Thread import ADDSMETARThread

# LED Driver
from LED_Control.RPi_zero_NeoPixel_LED_Driver import RPi_zero_NeoPixel_LED_Driver, RPi_zero_NeoPixel_Config
import board

from metarmap.Logging import initialize_basic_log_stream, initialize_rotating_file_log

from metarmap.utils import median_function_timer

def main():
    initialize_basic_log_stream(logging.getLogger(), logging.INFO)
    # initialize_rotating_file_log(logging.getLogger(), output_directory = Path(__file__).parent, output_name = 'test_rot_log', max_bytes = 10*1024*1024, backupCount=25)
    logger = logging.getLogger('main_function')

    # Create a configuration
    from pathlib import Path
    map_config  = METAR_MAP_Config(logging_level=logging.DEBUG, station_map = {
        'KSLE': 0,
        'KONP': 1,
        'KOSH': 2
    },
    metar_colors_config=METAR_COLOR_CONFIG(),
    led_driver= RPi_zero_NeoPixel_LED_Driver(
        config = RPi_zero_NeoPixel_Config(
                led_count=50,
                pin = board.D18,
                brightness=1.0,
                order = RPi_zero_NeoPixel_Config.supported_orders.GRB
            )
        )
    )

    # Create the METAR data source
    ADDSMETAR_stop_request = Event()
    ADDSMETAR_stop_request.clear()

    # Generate the thread object and start it
    adds_metar_thread = ADDSMETARThread(stop_request=ADDSMETAR_stop_request,
                                            stations = map_config.station_map,
                                                update_interval=timedelta(seconds = 5),
                                                stale_data_time=timedelta(seconds = 20)
    )
    adds_metar_thread.daemon = True
    adds_metar_thread.start()

    # Create the MainLoop object to run the map
    with MainLoop(config = map_config, metar_source=adds_metar_thread) as metarmap_loop:

        # Run the loop as many times as you'd like
        metarmap_loop_timer_buffer: deque[float] = deque([],maxlen=25)
        try:
            while True:
                loop_length = median_function_timer(metarmap_loop_timer_buffer, metarmap_loop.loop)
                print(metarmap_loop)
                # print(f'METARMAP_loop Run Time: {loop_length}')
                # if metarmap_loop.metar_source.is_running:
                #     print(f'METAR AGE: {metarmap_loop.current_metar_state_age}')
        except KeyboardInterrupt:
            logger.critical('Loop Ended by Keyboard Interrupt')

if __name__ == '__main__':
    sys.exit(main())
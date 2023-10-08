import sys
import logging
from datetime import timedelta
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

def main():
    initialize_basic_log_stream(logging.getLogger(), logging.INFO)
    initialize_rotating_file_log(logging.getLogger(), output_directory = Path(__file__).parent / 'logs', output_name = 'test_rot_log', max_bytes = 10*1024*1024, backupCount=25)
    logger = logging.getLogger('main_function')

    # Create a configuration

    # Map configuration, stations align with the physical map section and the LEDs in use
    map_config  = METAR_MAP_Config(logging_level=logging.DEBUG, station_map = {
        'KMKE': 29,
        'KMWC': 30,
        'KUES': 31,
        'KRYV': 33,
        'KMSN': 35,
        'KDLL': 37,
        'KUNU': 40,
        'KSBM': 44,
        'KFLD': 46,
        'KOSH': 47,
        'KY50': 49
    },
    
    # Default color config
    metar_colors_config=METAR_COLOR_CONFIG(),

    # RPi Zero with 50 neopixel strip
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
                                                update_interval=timedelta(minutes = 15),
                                                stale_data_time=timedelta(minutes = 90)
    )
    adds_metar_thread.daemon = True
    adds_metar_thread.start()

    # Create the MainLoop object to run the map
    with MainLoop(config = map_config, metar_source=adds_metar_thread) as metarmap_loop:

        # Run the loop as many times as you'd like
        try:
            while True:
                metarmap_loop.loop()
        except KeyboardInterrupt:
            logger.critical('Loop Ended by Keyboard Interrupt')

if __name__ == '__main__':
    sys.exit(main())
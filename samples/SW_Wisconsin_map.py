import sys
import logging
from datetime import timedelta
from pathlib import Path

# Module imports
from metarmap.MainLoop import MainLoop
from metarmap.METAR_Map_Config import METAR_MAP_Config, METAR_COLOR_CONFIG, Day_Night_Dimming_Config, Wind_Animation_Config

# METAR SOURCE
from METAR.ADDS_METAR_Thread import ADDSMETARThread

# LED Driver
from LED_Control.RPi_zero_NeoPixel_LED_Driver import RPi_zero_NeoPixel_LED_Driver, RPi_zero_NeoPixel_Config
import board

from metarmap.Logging import initialize_basic_log_stream, initialize_rotating_file_log

station_map = {
    'KMKE': 30,
    'KMWC': 31,
    'KUES': 32,
    'KRYV': 34,
    'KMSN': 36,
    'KDLL': 38,
    'KUNU': 41,
    'KSBM': 44,
    'KFLD': 46,
    'KOSH': 47,
    'KY50': 49
}

adds_metar_thread = ADDSMETARThread(
    stations = station_map,
    update_interval=timedelta(minutes = 15),
    stale_data_time=timedelta(minutes = 90)
)

# Map configuration
map_config  = METAR_MAP_Config(
    name = 'SW_Wisconsin_map',
    logging_level=logging.DEBUG, 

    # stations align with the physical map section and the LEDs in use
    station_map = station_map,

    metar_source=adds_metar_thread,

    # Default color config
    metar_colors_config=METAR_COLOR_CONFIG(),

    # RPi Zero with 50 neopixel strip
    led_driver= RPi_zero_NeoPixel_LED_Driver(
        config = RPi_zero_NeoPixel_Config(
            led_count=50,
            pin = board.D18,
            brightness=0.4,
            order = RPi_zero_NeoPixel_Config.supported_orders.GRB
        )
    ),

    # Day-Night uses lat/lon of Milwaukee
    day_night_dimming_config = Day_Night_Dimming_Config(
        day_night_dimming = True,
        brightness_dim = 0.1,
        use_sunrise_sunet = True,
        day_night_latitude = 43.0389,
        day_night_longitude = -87.9065
    ),

    wind_animation_config = Wind_Animation_Config(
    enabled=True,
    blink_threshold=15,
    high_wind_threshold=25
)

)

def main():
    initialize_basic_log_stream(logging.getLogger(), logging.INFO)
    initialize_rotating_file_log(logging.getLogger(), output_directory = Path(__file__).parent.parent / 'logs', output_name = f'{map_config.name}', 
                                 fileLevel= map_config.logging_level, max_bytes = 10*1024*1024, backup_count=25)
    logger = logging.getLogger('main_function')

    # Create the MainLoop object to run the map
    with MainLoop(config = map_config) as metarmap_loop:

        # Run the loop as many times as you'd like
        logger.info('Running Loop...')
        try:
            while True:
                metarmap_loop.loop()
        except KeyboardInterrupt:
            logger.critical('Loop Ended by Keyboard Interrupt')

if __name__ == '__main__':
    sys.exit(main())
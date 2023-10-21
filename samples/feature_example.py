import sys
import logging
from datetime import timedelta, datetime
from pathlib import Path
from METAR import METAR

# Module imports
from metarmap.MainLoop import MainLoop
from metarmap.METAR_Map_Config import METAR_MAP_Config, METAR_COLOR_CONFIG, Day_Night_Dimming_Config, Wind_Animation_Config, Lightning_Animation_Config

# METAR SOURCE
from metarmap.METAR_SOURCE import METAR_SOURCE

# LED Driver
from LED_Control.RPi_zero_NeoPixel_LED_Driver import RPi_zero_NeoPixel_LED_Driver, RPi_zero_NeoPixel_Config
import board

from metarmap.Logging import initialize_basic_log_stream, initialize_rotating_file_log

station_map = {
    'DEMO1': 27,
    'DEMO2': 30,
    'DEMO3': 31,
    'DEMO4': 32,
    'DEMO5': 34,
    'DEMO6': 36,
    'DEMO7': 38,
    'DEMO8': 41,
    'DEMO9': 44,
    'DEMO10': 46,
    'DEMO11': 47,
    'DEMO12': 49
}

demo_data = {
    # Demo 1: VFR, Base
    'DEMO1':  METAR(station = 'DEMO1', flight_category='VFR', wind_speed_kt=0, wind_gust_kt=0),
    # DEMO2: MVFR, Base
    'DEMO2':  METAR(station = 'DEMO1', flight_category='MVFR', wind_speed_kt=0, wind_gust_kt=0),
    # DEMO3: IFR, Base
    'DEMO3':  METAR(station = 'DEMO1', flight_category='IFR', wind_speed_kt=0, wind_gust_kt=0),
    # DEMO4: LIFR, Base
    'DEMO4':  METAR(station = 'DEMO1', flight_category='LIFR', wind_speed_kt=0, wind_gust_kt=0),
    # Demo5: VFR, Windy
    'DEMO5':  METAR(station = 'DEMO1', flight_category='VFR', wind_speed_kt=20, wind_gust_kt=0),
    # Demo6: VFR, Very Windy
    'DEMO6':  METAR(station = 'DEMO1', flight_category='VFR', wind_speed_kt=30, wind_gust_kt=30),
    # Demo7: IFR, Lightning
    'DEMO7':  METAR(station = 'DEMO1', flight_category='IFR', wind_speed_kt=0, wind_gust_kt=0, raw_text='LTG'),

}

class Demo_METAR_Source(METAR_SOURCE):

    def __init__(self, demo_data: dict[str, METAR], update_interval: timedelta):
        self.demo_data = demo_data
        self.last_update: datetime.now()
        self.update_interval = update_interval

    @property
    def live_metar_data(self) -> dict[str, METAR]:
        return self.demo_data
    
    @property
    def new_metar_data(self) -> bool:
        if datetime.now() > (self.last_update + self.update_interval):
            self._new_metar_data = True
        return self._new_metar_data
    
    @new_metar_data.setter
    def new_metar_data(self, new_state: bool) -> None:
        self._new_metar_data = new_state
        self.last_update = datetime.now()
        return
    
    def data_is_stale(self) -> bool:
        return False
    
    def is_running(self) -> bool:
        return True

# Map configuration
map_config  = METAR_MAP_Config(
    name = 'SW_Wisconsin_map',
    logging_level=logging.DEBUG, 

    # stations align with the physical map section and the LEDs in use
    station_map = station_map,

    metar_source=Demo_METAR_Source(demo_data),

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

    wind_animation_config = Wind_Animation_Config(enabled = True),
    lightning_animation_config = Lightning_Animation_Config(enabled = True)
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
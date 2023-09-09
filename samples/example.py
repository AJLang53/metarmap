import sys
import logging

import neopixel
import board

from metarmap.loop import MainLoop
from metarmap import METAR_MAP_Config, NeoPixel_Config, METAR_COLOR_CONFIG, Day_Night_Dimming_Config

def main():
    logger = logging.getLogger('main_function')

    day_night_config = Day_Night_Dimming_Config(True, 0.1, True, 45, -93)
    color_config = METAR_COLOR_CONFIG()
    neopixel_config = NeoPixel_Config(50, board.D18, brightness=1, order = neopixel.GRB)

    station_map = {
        'KSLE': 0,
        'KONP': 1,
        'S30': 2
    }

    map_config  = METAR_MAP_Config(logging_level=logging.DEBUG, station_map = station_map, neopixel_config=neopixel_config,
                                   metar_colors_config=color_config, day_night_dimming_config=day_night_config)

    # Create the MainLoop object to run the map
    metarmap_loop = MainLoop(map_config)

    # Run the loop as many times as you'd like
    try:
        while True:
            metarmap_loop.loop()
    except KeyboardInterrupt:
        logger.critical('Loop Ended by Keyboard Interrupt')
    return

if __name__ == '__main__':
    sys.exit(main())
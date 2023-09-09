from __future__ import annotations
from threading import Event
import typing
import logging
from datetime import datetime, timedelta

import neopixel
import board

from METAR import METAR
from METAR.ADDS_METAR_Thread import ADDSMETARThread
from metarmap.Config import METAR_MAP_Config, METAR_COLOR_CONFIG, NeoPixel_Config

class METAR_SOURCE(typing.Protocol):
    """Defines a valid METAR data source for the METARMAP loop to pull data from"""
    @property
    def new_metar_data(self) -> bool:
        """new_metar_data property, signals if there is new data """

    @new_metar_data.setter
    def new_metar_data(self, state: bool) -> None:
        """new_metar_data property must be settable by the retrieving object"""

    @property
    def live_metar_data(self) -> dict[str, METAR]:
        """
        The live_metar_data property should return a dictionary with key as station ID and value as
        METAR objects
        """

    @property
    def is_running(self) -> bool:
        """
        Returns if the METAR_SOURCE is still running functionally and can return valid data
        """

class Station:
    def __init__(self, idx: int, id: str, pin_index: int, active_color: typing.Tuple[float]):
        self.idx = idx
        self.id = id
        self.pin_index = pin_index
        self.active_color = active_color
        return

    def __lt__(self, other: Station) -> bool:
        return self.idx < other.idx

class MainLoop:
    '''
    Main program loop, handles the side threads and takes the configuration
    '''

    def __init__(self, config: METAR_MAP_Config, metar_source: METAR_SOURCE):
        self._logger = logging.getLogger(f'{self.__class__.__name__}')

        self.config: METAR_MAP_Config = config
        self.metar_source: METAR_SOURCE = metar_source  # METAR datasource that conforms to the protocol

        self._current_metar_state = {}   # Holder for the current metar state of the map
        self._current_metar_state_datetime: timedelta | None = None      # The age of the live data
        self.stations: list[Station] = []
        for idx, station_id in enumerate(self.config.station_map):
            self.stations.append(Station(
                idx = idx, id = station_id, pin_index = self.config.station_map[station_id], 
                active_color=self.config.metar_colors.color_clear
            ))

        # Neopixel control object
        # self._neopixel = neopixel.NeoPixel(pin = self.config.neopixel.pin, 
        #                                    n = self.config.neopixel.led_count,
        #                                    brightness=self.config.neopixel.brightness,
        #                                    pixel_order=self.config.neopixel.order,
        #                                    auto_write=False)
        return

    def __repr__(self):
        return f'METARMAP MainLoop: {self.config}'
    
    @property
    def current_metar_state_age(self) -> timedelta:
        """Return time since last update (age of current date)"""
        if self._current_metar_state_datetime is not None:
            return datetime.now()-self._current_metar_state_datetime
        return None
    
    def get_METAR_of_station(self, station_id: str):
        """Provide the cached METAR data for the station_id"""
        metar_data = None
        try:
            metar_data = self._current_metar_state[station_id]
        except KeyError:
            self._logger.error(f'No METAR data for station: {station_id}')
        return metar_data

    def _check_for_new_METAR_data(self) -> None:
        """
        Check if the metar_source has signaled new data is available
        If it is, get the live_metar_data and set the signal to false
        """
        if self.metar_source.new_metar_data:            # If there's new data from the source
            self._logger.debug(f'new metar data signaled')
            new_metar_dict = self.metar_source.live_metar_data       # Get the live data
            self._current_metar_state = new_metar_dict              # Set the current data dict to the new data
            self._current_metar_state_datetime = datetime.now()
            self.metar_source.new_metar_data = False                # Set the new data flag to false


    def _process_flight_category(self, station_metar: METAR) -> typing.Tuple[float]:
        """Handle the flight category for the base color"""

        if station_metar.flight_category == 'VFR':
            color = self.config.metar_colors.color_vfr
        elif station_metar.flight_category == 'MVFR':
            color = self.config.metar_colors.color_mvfr
        elif station_metar.flight_category == 'IFR':
            color = self.config.metar_colors.color_ifr
        elif station_metar.flight_category == 'LIFR':
            color = self.config.metar_colors.color_lifr
        return color
    
    def _process_brightness(self, color: typing.Tuple[float]) -> typing.Tuple[float]:
        """Handle the brightness configuraitons and modify color appropriately"""

        # Determine the brightness multiplier
        brightness_multiplier = 1
        if self.config.day_night_dimming is not None:
            if self.config.day_night_dimming.use_dim(datetime.now()):
                brightness_multiplier = self.config.day_night_dimming.brightness_dim

        # Apply to all elements of color tuple
        modified_color = tuple([element*brightness_multiplier for element in color])
        return modified_color


    def _update_color_map(self) -> None:
        """Update the color map between stations and their pixels using the metar data"""

        for station_id in self._current_metar_state:
            station_metar = self._current_metar_state[station_id]

            color = self._process_flight_category(station_metar)
            wind_color = self._process_wind(station_metar)
            lightning_color = self._process_lightning(station_metar)

            brightness_modified_color = self._process_brightness(color)

            # Apply the result to the object station list
            for station in self.stations:
                if station.id == station_id:
                    station.active_color = brightness_modified_color
        return

    def _update_LEDs(self) -> None:
        """
        Update the LED state based on the current METAR
        """

        # Map colors to stations based on the configuration and current conditions
        self._update_color_map()

        # Modify the LED state
        for station in self.stations:
            self._neopixel[station.pin_index] = station.active_color

        return

    def loop(self):
        self._check_for_new_METAR_data()
        # self._update_LEDs()

from collections import deque
from metarmap.utils import median_function_timer
if __name__ == '__main__':
    logger = logging.getLogger('main_function')

    # Get the configuration
    from pathlib import Path
    config_file = Path('example.cfg')
    map_config  = METAR_MAP_Config(logging_level=logging.DEBUG, station_map = {
        'KSLE': 0,
        'KONP': 1,
        'KOSH': 2
    },
    metar_colors_config=METAR_COLOR_CONFIG(),
    neopixel_config=NeoPixel_Config(
        led_count=50,
        pin = board.D18,
        brightness=1.0,
        order = neopixel.GRB
    )
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
                print('METAR AGE: {metarmap_loop.current_metar_state_age}')
    except KeyboardInterrupt:
        logger.critical('Loop Ended by Keyboard Interrupt')
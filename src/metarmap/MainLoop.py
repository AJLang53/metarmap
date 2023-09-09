from __future__ import annotations
from threading import Event
import typing
import logging
from datetime import datetime, timedelta

# Core Module Imports
from METAR import METAR
from metarmap.METAR_Map_Config import METAR_MAP_Config
from metarmap.Station import Station
from metarmap.RGB_color import RGB_color, apply_brightness

# LED Driver
try:
    from LED_Control.RPi_zero_NeoPixel_LED_Driver import RPi_zero_NeoPixel_LED_Driver, RPi_zero_NeoPixel_Config
# A NotImplementedError will be raised if the platform has not implemented these things (such as your computer)
# Just pass along, for testing on machines that hit this error you should not try to use them anyways
except NotImplementedError:
    pass

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


    def _process_flight_category(self, station_metar: METAR) -> RGB_color:
        """Handle the flight category for the base color"""

        if station_metar.flight_category == 'VFR':
            color = self.config.metar_colors.color_vfr
        elif station_metar.flight_category == 'MVFR':
            color = self.config.metar_colors.color_mvfr
        elif station_metar.flight_category == 'IFR':
            color = self.config.metar_colors.color_ifr
        elif station_metar.flight_category == 'LIFR':
            color = self.config.metar_colors.color_lifr
        else:
            raise ValueError(f'Unsupported flight_category: {station_metar.flight_category} for station_metar: {station_metar}')
        
        return color
    
    def _process_brightness(self, color: RGB_color) -> RGB_color:
        """Handle the brightness configuraitons and modify color appropriately"""

        # Default behavior is no change
        modified_color = color

        # Check if there is a day_night_dimming configuration, if there is, apply the brightness multiplier
        if self.config.day_night_dimming is not None:
            if self.config.day_night_dimming.use_dim(datetime.now()):       # The configuration itself provides the method to determine if it should be dim now
                brightness_multiplier = self.config.day_night_dimming.brightness_dim
                modified_color = apply_brightness(color, brightness_multiplier)

        return modified_color

    def _process_wind(self, *args, **kwargs):
        return
    
    def _process_lightning(self, *args, **kwargs):
        return

    def _update_color_map(self) -> None:
        """Update the color map between stations and their pixels using the metar data"""

        for station_id in self._current_metar_state:
            station_metar = self._current_metar_state[station_id]

            try:
                color = self._process_flight_category(station_metar)
            # A ValueError is raised if the station_metar does not have a supported flight category
            # Log the error, but continue through the loop (ignore this case, hopefully a new METAR will resolve it)
            except ValueError as ve:
                self._logger.error(f'Error encountered in process_flight_category for station_id: {station_id}, METAR: {station_metar}')
                continue

            wind_color = self._process_wind(station_metar)
            lightning_color = self._process_lightning(station_metar)

            brightness_modified_color = self._process_brightness(color)

            # Apply the result to the object station list
            # This is correlating the station list to the station-METAR dictionary
            for station in self.stations:
                if station.id == station_id:
                    station.active_color = brightness_modified_color
        return

    def _update_LEDs(self) -> None:
        """
        Update the LED state using the current active station data
        """

        for station in self.stations:
            # Only call this update if the color has actually changed
            if station.updated:
                # Bypass if LED_driver is not configured (allows for testing without actually using LEDs)
                if self.config.led_driver is not None:
                    self.config.led_driver.update_LED(station.pin_index, station.active_color)
                else:
                    self._logger.debug('no LED Driver configured')

        return

    def loop(self):
        # See if the METAR_SOURCE has new data available and update the mainloop data if so
        self._check_for_new_METAR_data()

        # Map colors to stations based on the configuration and current conditions
        self._update_color_map()

        # Apply the color map to the LED output as defined by the configuration
        self._update_LEDs()
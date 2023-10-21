from __future__ import annotations
from threading import Event
import typing
from types import TracebackType
import logging
from datetime import datetime, timedelta
from random import random

# Core Module Imports
from METAR import METAR
from metarmap.METAR_Map_Config import METAR_MAP_Config
from metarmap.Station import Station, Random_Blink_Manager, Burst_Blink_Manager
from metarmap.RGB_color import RGB_color, apply_brightness

# LED Driver
try:
    from LED_Control.RPi_zero_NeoPixel_LED_Driver import RPi_zero_NeoPixel_LED_Driver, RPi_zero_NeoPixel_Config
# A NotImplementedError will be raised if the platform has not implemented these things (such as your computer)
# Just pass along, for testing on machines that hit this error you should not try to use them anyways
except NotImplementedError:
    pass

def get_time_delta_to_event(event_time: datetime) -> timedelta:
    '''
    Compare the current time against the event_time provided
    '''
    currentTime = datetime.now()
    time_delta = currentTime - event_time
    return time_delta

class MainLoop:
    '''
    Main program loop, handles the side threads and takes the configuration
    '''

    def __init__(self, config: METAR_MAP_Config):
        self._logger = logging.getLogger(f'{self.__class__.__name__}')

        # A METAR_MAP_Config object defines all necessary elements of the system
        self.config: METAR_MAP_Config = config

        # The map holds the current METAR state that will drive the LEDs
        self._current_metar_state: dict[str, METAR | None] | None = None   # Holder for the current metar state of the map
        self._current_metar_state_datetime: timedelta | None = None      # The age of the live data

        wind_blink_manager: Random_Blink_Manager | None = None
        wind_gust_manager: Random_Blink_Manager | None = None
        if self.config.wind_animation.enabled:
            if self.config.wind_animation.blink_threshold is not None:
                wind_blink_manager = Random_Blink_Manager(blink_time_min=self.config.wind_animation.blink_duration_min, 
                                                          blink_time_max=self.config.wind_animation.blink_duration_min, 
                                                          duty_cycle=self.config.wind_animation.blink_duty_cycle)
            if self.config.wind_animation.gust_threshold is not None:
                wind_gust_manager = Random_Blink_Manager(blink_time_min=self.config.wind_animation.gust_duration_min, 
                                                          blink_time_max=self.config.wind_animation.gust_duration_max, 
                                                          duty_cycle=self.config.wind_animation.gust_duty_cycle)
        if self.config.lightning_animation_enabled:
            lightning_cycle_manager = Burst_Blink_Manager(cycle_duration_min=self.config.lightning_animation.cycle_duration_min,
                                                          cycle_duration_max=self.config.lightning_animation.cycle_duration_max,
                                                          cycle_duty_cycle=self.config.lightning_animation.cycle_duty_cycle,
                                                          burst_duration_min=self.config.lightning_animation.burst_duration_min,
                                                          burst_duration_max=self.config.lightning_animation.burst_duration_max,
                                                          burst_duty_cycle=self.config.lightning_animation.burst_duty_cycle)

        # The map holds the list of stations to track their LED states
        self.stations: list[Station] = []
        for idx, station_id in enumerate(self.config.station_map):
            self.stations.append(Station(
                idx = idx, id = station_id, pin_index = self.config.station_map[station_id], 
                active_color=self.config.metar_colors.color_clear,
                wind_blink_manager = wind_blink_manager,
                wind_gust_manager = wind_gust_manager,
                lightning_cycle_manager = lightning_cycle_manager
            ))

        return

    def __repr__(self):
        return f'METARMAP MainLoop: {self.config}'
    
    def __enter__(self) -> MainLoop:
        """Allow the use of with statement with this object, will ensure close is called"""
        return self

    def __exit__(self,exception_type: typing.Optional[typing.Type[BaseException]],
                 exception_value: typing.Optional[BaseException],
                 traceback: typing.Optional[TracebackType],
    ) -> None:
        """Call cleanup operations"""
        self.close()
        return

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
    
    def _time_for_new_data(self) -> bool:
        """
        Check the current time against the age of the current METAR data, 
        and return True if a new METAR should be retrieved from the METAR_SOURCE
        
        :return: bool, True if new METAR data should be retrieved
        """
        # If there is no current metar data (age is None), then it's time to request
        if self.current_metar_state_age is None:
            return True
        
        # If the age is greater than the update interval, then it's time to request
        if self.current_metar_state_age > self.config.update_interval:
            return True
        
        return False

    def _check_for_new_METAR_data(self) -> None:
        """
        Check if the metar_source has signaled new data is available
        If it is, get the live_metar_data and set the signal to false
        """
        # If there's new data from the source (or we have no data at all)
        if self.config.metar_source.new_metar_data or self._current_metar_state is None:            
            self._logger.debug(f'new metar data signaled')
            new_metar_dict = self.config.metar_source.live_metar_data       # Get the live data
            self._current_metar_state = new_metar_dict              # Set the current data dict to the new data
            self._current_metar_state_datetime = datetime.now()
            self.config.metar_source.new_metar_data = False                # Set the new data flag to false

        if self.config.metar_source.data_is_stale:
            self._logger.debug(f'metar_source signals that data is stale')
            if self._current_metar_state is not None:
                for station_id in self._current_metar_state:
                    self._current_metar_state[station_id] = METAR()
                    self._current_metar_state_datetime = None

    def _process_flight_category(self, station_metar: METAR) -> RGB_color:
        """Handle the flight category for the base color"""

        try:
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
        except AttributeError:
            raise ValueError(f'station_metar: {station_metar} does not have the flight_category attribute')
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

    def _process_wind(self, color: RGB_color, station: Station, station_metar: METAR) -> RGB_color:
        """
        If a station is deemed Windy, and the Wind feature is enabled, the station should psuedo-random and
        periodically blink to the fade color and back
        """
        # If the feature is disabled, don't do anything
        if not self.config.wind_animation_enabled:
            return color
        
        # For None states, set to effective infinity value for always failed comparisons
        blink_threshold = self.config.wind_animation.blink_threshold
        if blink_threshold is None:
            blink_threshold = 9e25
        gust_threshold = self.config.wind_animation.gust_threshold
        if gust_threshold is None:
            gust_threshold = 9e25

        # 0 out speed and gust if not present
        wind_speed = station_metar.wind_speed_kt
        if wind_speed is None:
            wind_speed = 0
        gust_speed = station_metar.wind_gust_kt
        if gust_speed is None:
            gust_speed = 0

        # High Wind feature first
        # If over the gust or wind threshold for high wind, run blink and grab the output
        if gust_speed > gust_threshold or wind_speed > gust_threshold:
            if station.high_wind_state.blink():
                return self.config.metar_colors.color_high_winds

        # Low wind blink second
        elif wind_speed > blink_threshold:
            if station.wind_state.blink():
                return self.config.metar_colors.fade(color)

        return color
    
    def _process_lightning(self, color: RGB_color, station: Station, station_metar: METAR) -> RGB_color:
        """
        Lightning can be identified in the METAR raw_text by the following strings:
         - LTG
         - TS
         - TSNO
        If a station has lightning, process the lightning display feature
        """
        # If the feature is disabled, don't do anything
        if not self.config.lightning_animation_enabled:
            return color
        
        lightning_substrings = [
            'LTG',
            'TS',
            'TSNO'
        ]
        
        # Look for the target strings
        lightning = False
        for substring in lightning_substrings:
            if station_metar.raw_text.find(substring, 4):   # Start looking after the station name only
                lightning = True
        
        if lightning:
            if station.lightning_state.blink():
                return self.config.metar_colors.color_lightning
        
        return color

    def _update_color_map(self) -> None:
        """Update the color map between stations and their pixels using the metar data"""

        # No color to update if there's no active METAR state
        if self._current_metar_state is None:
            return
        
        # Get the station state and the METAR data
        for station in self.stations:
            try:
                station_metar = self._current_metar_state[station.id]
            except KeyError:
                self._logger.error(f'No METAR data for station: {station}')
                continue
            
            # It's possible that the metar for a given station ID is None, if it could not be retreived
            if station_metar is None:
                self._logger.error(f'Station: {station.id} has no data in _current_metar_state: {self._current_metar_state}')
                continue
            
            color = None
            try:
                color = self._process_flight_category(station_metar)
            # A ValueError is raised if the station_metar does not have a supported flight category
            # Log the error, but continue through the loop (ignore this case, hopefully a new METAR will resolve it)
            except (ValueError, AttributeError) as e:
                self._logger.exception(f'Error encountered in process_flight_category for station_id: {station.id}, METAR: {station_metar}')
                continue
            
            wind_color = color
            try:
                wind_color = self._process_wind(color, station, station_metar)
            except (ValueError, AttributeError) as e:
                self._logger.exception(f'Error encountered in _process_wind for station_id: {station.id}, METAR: {station_metar}')
                continue
            
            lightning_color = wind_color
            try:
                lightning_color = self._process_lightning(color, station, station_metar)
            except (ValueError, AttributeError) as e:
                self._logger.exception(f'Error encountered in _process_lightning for station_id: {station.id}, METAR: {station_metar}')
                continue

            brightness_modified_color = self._process_brightness(lightning_color)

            # Apply the result to the object station list
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

    def close(self):
        if self.config.led_driver is not None:
            self.config.led_driver.close()
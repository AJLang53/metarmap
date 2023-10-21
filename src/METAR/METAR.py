from __future__ import annotations
import logging
from typing import TypeVar, Literal
T = TypeVar("T")

from datetime import datetime, timezone

def try_cast(cast_str: str | T, cast_type: T, exception_logger: logging.Logger | None = None) -> T | None:
    """Attempts to cast the string into the type provided, returns None on any type of failure"""
    # Trivial case, already done
    if isinstance(cast_str, cast_type):
        return cast_str
    else:
        try:
            cast_val = cast_type(cast_str)
            return cast_val
        except Exception as e:
            if exception_logger is not None:
                exception_logger.exception(f'Failed to cast string {cast_str} to {cast_type}')
            else:
                pass
        return None

class METAR:
    """Object to represent an FAA METAR"""
    def __init__(self, station: str | None = None, raw_text: str | None = None, observation_time: datetime | None = None,
                 latitude: float | None = None, longitude: float | None = None,
                 temp_c: float | None = None, dewpoint_c: float | None = None,
                 wind_dir_degrees: float | None = None, wind_speed_kt: int | None = None,
                 wind_gust_kt: float | None = None, visibility_statute_mi: float | None = None,
                 altim_in_hg: float | None = None, sea_level_pressure_mb: float | None = None,
                 wx_string: str | None = None, flight_category: str | None = None,
                 precip_in: float | None = None, metar_type: str | None = None,
                 elevation_m: float | None = None, quality_control_flag: str | None = None,
                 sky_condition: list[dict[str, str | int]] | None = None,
                 logger: logging.Logger | None = None):
        
        # Optional logger object can be provided, otherwise it'll make its own for logging issues
        if logger is None:
            self.logger: logging.Logger = logging.getLogger(f'{self.__class__.__name__}')
        else:
            self.logger = logger

        # Direct attributes
        self.station = station
        self.raw_text = raw_text
        self.flight_category = flight_category
        self.metar_type = metar_type
        self.quality_control_flag = quality_control_flag

        # Attributes that can be taken as string or resulting object (require setter method)
        self._observation_time = observation_time
        self._latitude = latitude
        self._longitude = longitude
        self._temp_c = temp_c
        self._dewpoint_c = dewpoint_c
        self._wind_dir_degrees = wind_dir_degrees
        self._wind_speed_kt = wind_speed_kt
        self._wind_gust_kt = wind_gust_kt
        self._visibility_statute_mi = visibility_statute_mi
        self._altim_in_hg = altim_in_hg
        self._sea_level_pressure_mb = sea_level_pressure_mb
        self._precip_in = precip_in
        self._elevation_m = elevation_m
        if sky_condition is None:
            self._sky_condition = []
        else:
            self._sky_condition = sky_condition

        # TODO finish this
        self._wx_string = wx_string
        return
    
    def __repr__(self):
        return f'METAR: {self.raw_text}'

    @property
    def observation_time(self) -> datetime:
        return self._observation_time
    
    @observation_time.setter
    def observation_time(self,observation_time: datetime | str):
        """Observation time can be provided as a METAR format string or a datetime object"""
        if isinstance(observation_time, datetime):
            self._observation_time = observation_time
            return
        else:
            # Attempt the conversion, leave as None if it fails
            try:
                year = int(observation_time.split('T')[0].split('-')[0])
                month = int(observation_time.split('T')[0].split('-')[1])
                day = int(observation_time.split('T')[0].split('-')[2])
                hourzulu = int(observation_time.split('T')[1].split(':')[0])
                minute = int(observation_time.split('T')[1].split(':')[1])
                second = int(observation_time.split('T')[1].split(':')[2].split('Z')[0])
                self._observation_time = datetime(year,month,day,hourzulu,minute,second,tzinfo=timezone.utc)
            except:
                self.logger.error(f'Error creating datetime object for observationTime: {observation_time}')
                return

    @property
    def latitude(self) -> float | None:
        return self._latitude
    
    @latitude.setter
    def latitude(self,val: str | float) -> None:
        """Attempt conversion"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._latitude = cast_val
        return

    @property
    def longitude(self) -> float | None:
        return self._longitude
    
    @longitude.setter
    def longitude(self,val: str | float) -> None:
        """Attempt conversion"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._longitude = cast_val
        return

    @property
    def temp_c(self) -> float | None:
        return self._temp_c
    
    @temp_c.setter
    def temp_c(self,val: str | float) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._temp_c = cast_val
        return

    @property
    def dewpoint_c(self) -> float | None:
        return self._temp_c
    
    @dewpoint_c.setter
    def dewpoint_c(self,val: str | float) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._dewpoint_c = cast_val
        return

    @property
    def wind_dir_degrees(self) -> float | Literal['VRB'] | None:
        return self._wind_dir_degrees
    
    @wind_dir_degrees.setter
    def wind_dir_degrees(self,val: str | float) -> None:
        """attempt conversion to float"""
        # Wind direction can report as VRB for variable
        if val.lower() == 'vrb':
            val = 'VRB'
        else:
            cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._wind_dir_degrees = cast_val
        return

    @property
    def wind_speed_kt(self) -> int | None:
        return self._wind_speed_kt
    
    @wind_speed_kt.setter
    def wind_speed_kt(self,val: str | int) -> None:
        """attempt conversion to float"""
        # Wind speed can report as VRB for variable, treat this as a 0 knot speed
        cast_val = try_cast(val, int, self.logger)
        if cast_val is not None:
            self._wind_speed_kt = cast_val
        return

    @property
    def wind_gust_kt(self) -> int | None:
        return self._wind_gust_kt
    
    @wind_gust_kt.setter
    def wind_gust_kt(self,val: str | int) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, int, self.logger)
        if cast_val is not None:
            self._wind_gust_kt = cast_val
        return

    @property
    def visibility_statute_mi(self) -> float | None:
        return self._visibility_statute_mi

    @visibility_statute_mi.setter
    def visibility_statute_mi(self,val: float | str) -> None:
        """
        Attempt conversion to float
        
        Visibility can come as 10+ if unlimited is being reported, we don't care about this
        """
        try:
            val = val.replace('+','')
        except AttributeError:
            pass
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._visibility_statute_mi = cast_val
        return

    @property
    def altim_in_hg(self) -> float | None:
        return self._altim_in_hg
    
    @altim_in_hg.setter
    def altim_in_hg(self,val: float | str) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._altim_in_hg = cast_val
        return

    @property
    def sea_level_pressure_mb(self) -> float | None:
        return self._sea_level_pressure_mb
    
    @sea_level_pressure_mb.setter
    def sea_level_pressure_mb(self,val: float | str) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._sea_level_pressure_mb = cast_val
        return

    @property
    def wx_string(self):
        return self._wx_string
    
    @wx_string.setter
    def wx_string(self,val):
        '''
        TODO decode wx_strings https://www.aviationweather.gov/docs/metar/wxSymbols_anno2.pdf
        '''
        self._wx_string = val

    @property
    def precip_in(self) -> float | None:
        return self._precip_in
    
    @precip_in.setter
    def precip_in(self,val: float | str) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._precip_in = cast_val
        return
    
    @property
    def elevation_m(self) -> float | None:
        return self._elevation_m
    
    @elevation_m.setter
    def elevation_m(self,val: float | str) -> None:
        """attempt conversion to float"""
        cast_val = try_cast(val, float, self.logger)
        if cast_val is not None:
            self._elevation_m = cast_val
        return

    @property
    def sky_condition(self) -> list[dict[str, str | int]] | None:
        return self._sky_condition
    
    def add_sky_condition(self,sky_cover: str | None, cloud_base_ft_agl: int | str | None) -> None:
        '''
        Appends the sky condition to the sky_condition list
        Each sky condition comes in the following form <sky_condition sky_cover="FEW" cloud_base_ft_agl="4300"/>
        There can be multiple of these items, so each should be a dictionary
        '''

        if cloud_base_ft_agl is not None:
            cloud_base_ft_agl = try_cast(cloud_base_ft_agl, int, self.logger)

        sky_condition_dict = {
            'sky_cover': sky_cover,
            'cloud_base_ft_agl': cloud_base_ft_agl
        }
        self._sky_condition.append(sky_condition_dict)
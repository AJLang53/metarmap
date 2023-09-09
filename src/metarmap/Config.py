from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

import astral.sun

from adafruit_blinka.microcontroller.generic_micropython import Pin

def is_between_sunrise_sunset(latitude: float, longitude: float, time: datetime) -> bool:
    """Returns True if the time provided at location is between sunrise and sunset"""
    observer = astral.Observer(latitude=latitude, longitude=longitude)
    sunrise = astral.sun.sunrise(observer=observer, date = datetime.date())
    sunset = astral.sun.sunset(observer=observer, date = datetime.date())
    return sunrise < time < sunset

@dataclass
class NeoPixel_Config:
    """Configuration for Neopixel interface with Raspberry Pi GPIO"""
    led_count: int      # Number of LED pixels
    pin: Pin            # GPIO pin in use
    brightness: float   # 0.0 to 1.0
    order: str          # Strip type and color ordering

class Day_Night_Dimming_Config:
    """Configuraiton for day-night dimming feature"""

    def __init__(self, day_night_dimming: bool, brightness_dim: float, use_sunrise_sunet: bool = False,
                 day_night_latitude: float | None = None, day_night_longitude: float | None = None,
                 bright_time_start: datetime | None = None, dim_time_start: datetime | None = None):
        
        self.day_night_dimming = day_night_dimming
        self.brightness_dim = brightness_dim
        self.use_sunrise_sunet = use_sunrise_sunet
        self.day_night_latitude = day_night_latitude
        self.day_night_longitude = day_night_longitude
        self.bright_time_start = bright_time_start
        self.dim_time_start = dim_time_start
        return

    @property
    def valid(self) -> bool:
        """Determine if configuration is valid"""
        if self.day_night_dimming:
            if self.use_sunrise_sunet:
                if self.day_night_latitude is None or self.day_night_longitude is None:
                    return False
                else:
                    return True
            else:
                if self.bright_time_start is None or self.dim_time_start is None:
                    return False
                else:
                    return True
    
    def use_dim(self, time: datetime) -> bool:
        """Resolve the state of the configuration at the provided time"""

        # Ignore feature if not valid
        if not self.valid:
            return False
        # Ignore feature if disabled
        elif not self.day_night_dimming:
            return False
        else:
            # Check sunrise sunset
            if self.use_sunrise_sunet:
                return not is_between_sunrise_sunset(self.day_night_latitude, self.day_night_longitude, time.now().time())
            else:
                return not (self.bright_time_start < time.now().time() < self.dim_time_start)

class METAR_COLOR_CONFIG:
    """Configuration of colors for METAR conditions"""
    def __init__(self, color_vfr: Tuple[float] = (255,0,0), color_vfr_fade: Tuple[float] = (125,0,0),
                 color_mvfr: Tuple[float] = (0,0,255), color_mvfr_fade: Tuple[float] = (0,0,125),
                 color_ifr: Tuple[float] = (0,255,0), color_ifr_fade: Tuple[float] = (0,125,0),
                 color_lifr: Tuple[float] = (0,125,125), color_lifr_fade: Tuple[float] = (0,75,75),
                 color_clear: Tuple[float] = (0,0,0),
                 color_lightning: Tuple[float] = (255,255,255),
                 color_high_winds: Tuple[float] = (255,255,0)
                 ):
        self.color_vfr = color_vfr
        self.color_vfr_fade = color_vfr_fade
        self.color_mvfr = color_mvfr
        self.color_mvfr_fade = color_mvfr_fade
        self.color_ifr = color_ifr
        self.color_ifr_fade = color_ifr_fade
        self.color_lifr = color_lifr
        self.color_lifr_fade = color_lifr_fade
        self.color_clear = color_clear
        self.color_lightning = color_lightning
        self.color_high_winds = color_high_winds
        return

class METAR_MAP_Config:
    """Configuration of the METAR MAP"""
    def __init__(self, logging_level: int = logging.INFO, station_map: dict[str, int] = {}, 
                 neopixel_config: NeoPixel_Config | None = None, 
                 metar_colors_config: METAR_COLOR_CONFIG | None = None,
                 day_night_dimming_config: Day_Night_Dimming_Config | None = None,

                 
                 ):
        
        # Basic items
        self.logging_level = logging_level
        self.station_map = station_map
        self.neopixel = neopixel_config
        self.metar_colors = metar_colors_config

        #Features
        # Day-Night Dimming
        self.day_night_dimming = day_night_dimming_config

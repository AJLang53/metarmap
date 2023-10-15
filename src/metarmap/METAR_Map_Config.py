from __future__ import annotations
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

# Module Imports
from metarmap.METAR_SOURCE import METAR_SOURCE
from metarmap.utils import is_between_sunrise_sunset
from metarmap.RGB_color import RGB_color
from LED_Control.LED_Driver import LED_DRIVER

@dataclass
class Lightning_Animation_Config:
    """Configure the lightning animation feature"""
    enabled: bool = False
    cycle_duration_min: float = 5
    cycle_duration_max: float = 8
    cycle_duty_cycle: float = 0.3
    burst_duration_min: float = 0.01
    burst_duration_max: float = 0.02
    burst_duty_cycle: float = 0.5

@dataclass
class Wind_Animation_Config:
    """Configure the wind animation feature"""
    enabled: bool = False
    blink_threshold: int = 15
    blink_duration_min: float = 5
    blink_duration_max: float = 8
    blink_duty_cycle: float = 0.2
    gust_threshold: int = 25
    gust_duration_min: float = 5
    gust_duration_max: float = 8
    gust_duty_cycle: float = 0.2


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
    def __init__(self, color_vfr: RGB_color = RGB_color(0,255,0), color_vfr_fade: RGB_color = RGB_color(0,125,0),
                 color_mvfr: RGB_color = RGB_color(0,0,255), color_mvfr_fade: RGB_color = RGB_color(0,0,125),
                 color_ifr: RGB_color = RGB_color(255,0,0), color_ifr_fade: RGB_color = RGB_color(125,0,0),
                 color_lifr: RGB_color = RGB_color(125,0,125), color_lifr_fade: RGB_color = RGB_color(75,0,75),
                 color_clear: RGB_color = RGB_color(0,0,0),
                 color_lightning: RGB_color = RGB_color(255,255,255),
                 color_high_winds: RGB_color = RGB_color(255,255,0)
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
    
    def fade(self, color: RGB_color) -> RGB_color:
        """Apply the Fade effect to a color to produce the faded version"""
        fade_color = RGB_color(r = int(color.r/2), g = int(color.g/2), b = int(color.b/2))
        return fade_color

class METAR_MAP_Config:
    """Configuration of the METAR MAP"""
    def __init__(self, name: str, 
                 metar_source: METAR_SOURCE,
                 logging_level: int = logging.INFO, 
                 station_map: dict[str, int] = {}, 
                 led_driver: LED_DRIVER | None = None, 
                 metar_colors_config: METAR_COLOR_CONFIG = METAR_COLOR_CONFIG(),     # Apply default color config if not provided
                 day_night_dimming_config: Day_Night_Dimming_Config | None = None,
                 wind_animation_config: Wind_Animation_Config | None = None,
                 lightning_animation_config: Lightning_Animation_Config | None = None
                 ):
        
        # Book-keeping items
        self.name = name
        self.logging_level = logging_level

        # Map Specifics
        self.metar_source = metar_source
        self.station_map = station_map
        self.led_driver = led_driver
        self.metar_colors = metar_colors_config

        #Features
        # Day-Night Dimming
        self.day_night_dimming = day_night_dimming_config

        # Wind Animation
        self.wind_animation = wind_animation_config

        # Lightning Animation
        self.lightning_animation = lightning_animation_config

    @property
    def led_enabled(self) -> bool:
        """led_enabled property, True if there is a valid LED_driver"""
        if self.led_driver is not None:
            return self.led_driver.is_valid
        return False
    
    @property 
    def day_night_dimming_enabled(self) -> bool:
        """day_night_dimming feature proprety, True if the configuration is present and valid"""
        if self.day_night_dimming is not None:
            return self.day_night_dimming.valid
        return False

    @property
    def wind_animation_enabled(self) -> bool:
        """wind_animation feature property, True if the configuration is present and valid"""
        if self.wind_animation is not None:
            return self.wind_animation.enabled
        return False
    
    @property
    def lightning_animation_enabled(self) -> bool:
        """wind_animation feature property, True if the configuration is present and valid"""
        if self.lightning_animation is not None:
            return self.lightning_animation.enabled
        return False
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

# Adafruit Neopixel library
from adafruit_blinka.microcontroller.generic_micropython import Pin
import neopixel

# Module imports
from LED_Control.LED_Driver import LED_DRIVER
from metarmap.RGB_color import RGB_color

@dataclass
class RPi_zero_NeoPixel_Config:

    class supported_orders(str, Enum):
        RGB = neopixel.RGB
        GRB = neopixel.GRB
        RGBW = neopixel.RGBW
        GRBW = neopixel.GRBW

    """Configuration for Neopixel interface with Raspberry Pi GPIO"""
    led_count: int                                            # Number of LED pixels
    pin: Pin                                                  # GPIO pin in use
    brightness: float                                         # 0.0 to 1.0
    order: RPi_zero_NeoPixel_Config.supported_orders          # Strip type and color ordering

class RPi_zero_NeoPixel_LED_Driver(LED_DRIVER):
    """
    LED Driver for a Raspberry Pi Zero using the Adafruit Neopixel library to drive 
    WS2811 addressable LEDs
    """
    def __init__(self, config: RPi_zero_NeoPixel_Config):
        self.config = config

        # Neopixel control object
        self._neopixel = neopixel.NeoPixel(pin = self.config.pin,
                                           n = self.config.led_count,
                                           brightness=self.config.brightness,
                                           pixel_order=self.config.order,
                                           auto_write=False)
        
    @property
    def LED_index_colors(self) -> dict[int, RGB_color]:
        """Return a dictionary of the current state of the LEDs under control by the object"""
        d: dict[int, RGB_color] = {}
        for i in range(self.config.led_count):
            if self.config.order == neopixel.GRB:
                d[i] = RGB_color(self._neopixel[i][1],self._neopixel[i][0], self._neopixel[i][2])
            else:
                raise NotImplementedError(f'Non-GRB color ordering is not implemented')
        return d

    def update_LED(self, index: int, color: RGB_color) -> None:
        """Update the LED at the index to the color provided"""
        if self.config.order == neopixel.GRB:
            self._neopixel[index] = [color.g, color.r, color.b]
        else:
            raise NotImplementedError(f'Non-GRB color ordering is not implemented')
        
    def close(self) -> None:
        """
        Release the GPIO pin and deactivate LEDs
        """
        self._neopixel.deinit()
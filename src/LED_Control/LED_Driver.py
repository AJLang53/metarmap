import typing
from metarmap.RGB_color import RGB_color

class LED_DRIVER(typing.Protocol):
    """Defines a valid LED Driver object for the METARMAP loop to push station data to"""

    @property
    def LED_index_colors(self) -> dict[int, RGB_color]:
        """Return a dictionary of the current state of the LEDs under control by the object"""

    @property
    def is_valid(self) -> bool:
        """Property, current LED_DRIVER is in a valid runnable state"""

    def update_LED(self, index: int, color: RGB_color) -> None:
        """Update the LED provided by index to the color provided by the RGB_color object"""

    def close(self) -> None:
        """Shutdown procedure for the driver, turn off the lights and release the hardware"""
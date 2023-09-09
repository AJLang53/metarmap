from __future__ import annotations
from typing import Tuple

def apply_brightness(rgb_color: RGB_color, brightness: float) -> RGB_color:
    """
    Returns a new RGB_color object with the brightness applied

    Brightness must be a float between 0 and 1.0
    """
    if brightness >= 0.0 and brightness <= 1.0:
        return RGB_color(rgb_color.r * brightness,
                         rgb_color.g * brightness,
                         rgb_color.b * brightness
                         )
    else:
        raise ValueError(f'Brightness must be a float between 0 and 1.0')

class RGB_color:
    """Object to hold information about an RGB color"""

    @classmethod
    def from_hex(cls, hex_code: str) -> RGB_color:
        """Alternate constructor, takes hex code of color"""
        r, g, b = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        return cls(r, g, b)

    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b
        return
    
    @property
    def r(self) -> int:
        return self._r
    
    @r.setter
    def r(self, new_r: int) -> None:
        if new_r >=0 and new_r <= 255:
            self._r = new_r
        else:
            raise ValueError(f'{new_r} is not a valid RGB color value')
        return
    
    @property
    def g(self) -> int:
        return self._r
    
    @g.setter
    def g(self, new_g: int) -> None:
        if new_g >=0 and new_g <= 255:
            self._g = new_g
        else:
            raise ValueError(f'{new_g} is not a valid RGB color value')
        return
    
    @property
    def b(self) -> int:
        return self._r
    
    @b.setter
    def b(self, new_b: int) -> None:
        if new_b >=0 and new_b <= 255:
            self._b = new_b
        else:
            raise ValueError(f'{new_b} is not a valid RGB color value')
        return

    @property
    def RGB(self) -> Tuple[int, int, int]:
        """Return tuple of RGB value"""
        return (self.r, self.g, self.b)
    
    @property
    def hex(self) -> str:
        """Return hex string"""
        return '#%02x%02x%02x' % (self.r, self.g, self.b)


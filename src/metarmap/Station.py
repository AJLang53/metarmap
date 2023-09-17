from __future__ import annotations
from metarmap.RGB_color import RGB_color

class Station:
    """Object to hold information about a station light on the METAR MAP"""
    def __init__(self, idx: int, id: str, pin_index: int, active_color: RGB_color | None = None):
        self.idx = idx
        self.id = id
        self.pin_index = pin_index
        self._active_color = None
        self.updated = False

        if active_color is not None:
            self.active_color = active_color
        return
    
    def __repr__(self):
        return f'{self.__class__.__name__}: idx = {self.idx}, id = {self.id}, pin_index = {self.pin_index}, color = {self._active_color}'
    
    @property
    def active_color(self):
        return self._active_color
    
    @active_color.setter
    def active_color(self, new_active_color: RGB_color):
        if self._active_color != new_active_color:
            self._active_color = new_active_color
            self.updated = True

    def __lt__(self, other: Station) -> bool:
        return self.idx < other.idx
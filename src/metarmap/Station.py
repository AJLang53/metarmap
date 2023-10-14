from __future__ import annotations
from datetime import datetime, timedelta
from dataclasses import dataclass
import typing
from random import random
from metarmap.RGB_color import RGB_color

@dataclass
class Random_Blink_Manager:
    """An object that manages a blinking item that needs to flash at a potentially random interval"""
    blink_time_min: float
    blink_time_max: float
    duty_cycle: float
    state: bool = False
    start: typing.Optional[datetime] = None
    duration: typing.Optional[timedelta] = None
    running: bool = False

    def initialize(self, start_state: bool):
        """Initialize the object for a blinking period"""
        self.state = start_state
        self.start = datetime.now()
        self.update_durations(self.get_blink_duration())
        self.running = True

    def stop(self):
        """Deinitialize the object for blink disabled"""
        self.state = False
        self.start = None
        self.duration = None
        self.running = False

    def get_blink_duration(self) -> timedelta:
        """Generate a random timedelta between blink_time_min and blink_time_max"""
        return timedelta(seconds = random()*(self.blink_time_max - self.blink_time_min)+self.blink_time_min)
    
    def update_durations(self, duration: float) -> None:
        self.up_duration = duration*self.duty_cycle
        self.down_duration = duration - self.up_duration
        return

    def blink(self):
        """
        Flip the state if the duration has expired, and set the next duration to a random value
        between the two times (seconds) in blink_time_range
        """
        # if self.state is None or self.start is None or self.duration is None:
        #     raise AttributeError(f'blink called on uninitialized {self.__class__.__name__}: {self}')
        
        if not self.running:
            self.initialize(False)

        # If the duration has elapsed, flip the state
        if self.state:
            if datetime.now() - self.start > self.up_duration:
                self.state = False
                self.start = datetime.now()
                self.update_durations(self.get_blink_duration())
        elif not self.state:
            if datetime.now() - self.start > self.down_duration:
                self.state = True
                self.start = datetime.now()
                self.update_durations(self.get_blink_duration())
        
        else:
            pass
        return

class Station:
    """Object to hold information about a station light on the METAR MAP"""
    def __init__(self, idx: int, id: str, pin_index: int, active_color: RGB_color | None = None,
                 blink_time_min: float = 1.5, blink_time_max: float = 3):
        self.idx = idx
        self.id = id
        self.pin_index = pin_index
        self._active_color = None
        self.updated = False

        self.wind_state: Random_Blink_Manager = Random_Blink_Manager(blink_time_min=blink_time_min, blink_time_max=blink_time_max, duty_cycle=0.1)
        self.high_wind_state: Random_Blink_Manager = Random_Blink_Manager(blink_time_min=blink_time_min, blink_time_max=blink_time_max, duty_cycle=0.1)
        self.lightning_state: Random_Blink_Manager = Random_Blink_Manager(blink_time_min=blink_time_min, blink_time_max=blink_time_max, duty_cycle=0.1)

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
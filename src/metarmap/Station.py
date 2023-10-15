from __future__ import annotations
from datetime import datetime, timedelta
from dataclasses import dataclass
import typing
from random import random
from metarmap.RGB_color import RGB_color

@dataclass
class Burst_Blink_Manager:
    """An object that manages a blinking item that needs to flash quickly (in a burst) periodically"""

    cycle_duration_min: float
    cycle_duration_max: float
    cycle_duty_cycle: float

    state: bool = False
    cycle_running: bool = False

    def __post_init__(self):
        self.burst: Random_Blink_Manager | None = None
        self.start: datetime | None = None
        self.active: bool = False

        self.initialize(False)

    def initialize(self, start_state: bool):
        """Initialize the object for a blinking period"""
        self.state = start_state
        self.start = datetime.now()
        self.update_durations(self.get_cycle_duration())
        self.running = True
        
    def get_cycle_duration(self) -> timedelta:
        """Generate a random timedelta between blink_time_min and blink_time_max"""
        return timedelta(seconds = random()*(self.cycle_duration_max - self.cycle_duration_min)+self.cycle_duration_min)
    
    def update_durations(self, duration: float) -> None:
        self.up_duration = duration*self.cycle_duty_cycle
        self.down_duration = duration - self.up_duration
        return

    def blink(self):
        """
        Flip the state if the duration has expired, and set the next duration to a random value
        between the two times (seconds) in blink_time_range
        """
        now = datetime.now()

        # Check if we're in the active portion of the cycle
        if self.active:
            if now - self.start < self.up_duration:
                # If there is no Burst manager, create one
                if self.burst is None:
                    self.burst = Random_Blink_Manager(0.1,0.15,0.5,False)
                
                # Otherwise, blink the burst manager and use its state in this portion
                self.state = self.burst.blink()
            # Otherwise, reset the burst to None and 
            else:
                self.burst = None
                self.active = False
                self.start = now
        elif not self.active:
            # Do nothing in the down cycle
            if now - self.start < self.down_duration:
                if self.state:
                    self.state = False
                pass
            else:
                self.active = True
                self.update_durations(self.get_cycle_duration())
                self.start = now

        return self.state

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

    def __post_init__(self):
        self.initialize(False)

    def initialize(self, start_state: bool):
        """Initialize the object for a blinking period"""
        self.state = start_state
        self.start = datetime.now()
        self.update_durations(self.get_blink_duration())
        self.running = True

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
        return self.state

class Station:
    """Object to hold information about a station light on the METAR MAP"""
    def __init__(self, idx: int, id: str, pin_index: int, active_color: RGB_color | None = None,
                 wind_blink_manager: Random_Blink_Manager | None = None, wind_gust_manager: Random_Blink_Manager | None = None,
                 lightning_cycle_manager: Burst_Blink_Manager | None = None):
        self.idx = idx
        self.id = id
        self.pin_index = pin_index
        self._active_color = None
        self.updated = False

        self.wind_state: Random_Blink_Manager | None = wind_blink_manager
        self.high_wind_state: Random_Blink_Manager | None = wind_gust_manager
        self.lightning_state: Burst_Blink_Manager | None = lightning_cycle_manager

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
    
if __name__ == '__main__':
    burst_cycle = Burst_Blink_Manager(5,5,0.5)
    while True:
        print(burst_cycle.blink())

from __future__ import annotations
import typing
from datetime import timedelta, datetime

from METAR import METAR

class METAR_SOURCE(typing.Protocol):
    """Defines a valid METAR data source for the METARMAP loop to pull data from"""

    def __init__(self, station: list[str], update_interval: timedelta, stale_data_time: timedelta):
        """Initializer takes the station list, update_interval, and stale_data_time"""

    @property
    def new_metar_data(self) -> bool:
        """new_metar_data property, signals if there is new data """

    @new_metar_data.setter
    def new_metar_data(self, state: bool) -> None:
        """new_metar_data property must be settable by the retrieving object"""

    @property
    def live_metar_data(self) -> dict[str, METAR]:
        """
        The live_metar_data property should return a dictionary with key as station ID and value as
        METAR objects
        """

    @property
    def data_is_stale(self) -> bool:
        """The data has become stale and is no longer valid, but new data could not be received"""

    @property
    def is_running(self) -> bool:
        """
        Returns if the METAR_SOURCE is still running functionally and can return valid data
        """

class Demo_METAR_Source(METAR_SOURCE):

    @classmethod
    def from_cfg(self, dict: dict[str, ]) -> Demo_METAR_Source:
        """Alternate constructor, from cfg file"""
        return Demo_METAR_Source({}, timedelta(minutes = 15))

    def __init__(self, demo_data: dict[str, METAR], update_interval: timedelta):
        self.demo_data = demo_data
        self.last_update: datetime = datetime.now()
        self.update_interval = update_interval
        self._new_metar_data: bool = True

    @property
    def live_metar_data(self) -> dict[str, METAR]:
        return self.demo_data
    
    @property
    def new_metar_data(self) -> bool:
        if datetime.now() > (self.last_update + self.update_interval):
            self._new_metar_data = True
        return self._new_metar_data
    
    @new_metar_data.setter
    def new_metar_data(self, new_state: bool) -> None:
        self._new_metar_data = new_state
        self.last_update = datetime.now()
        return
    
    @property
    def data_is_stale(self) -> bool:
        return False
    
    @property
    def is_running(self) -> bool:
        return True
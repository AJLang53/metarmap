import typing
from datetime import timedelta
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

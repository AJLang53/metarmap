from __future__ import annotations
import logging
from datetime import datetime, timedelta

# Python Threading
from threading import Thread, Lock, get_ident

# Module Imports
from METAR.aviation_weather_metar import Aviation_Weather_METAR, METAR

def get_time_delta_to_event(event_time: datetime) -> timedelta:
    '''
    Compare the current time against the event_time provided
    '''
    currentTime = datetime.now()
    time_delta = currentTime - event_time
    return time_delta

class Aviation_Weather_METAR_Thread(Aviation_Weather_METAR, Thread):
    '''
    A thread that manages stations periodically to make available station METAR data through its queues
    '''

    def __init__(self,
                stations: list[str] | None = None,
                update_interval: timedelta = timedelta(seconds = 900),        # 15 minute update default
                stale_data_time: timedelta = timedelta(seconds = 5220),        # 1 Hour, 45 minutes for stale data defaults
                wait_to_run: bool = False
                ):
        self._logger = logging.getLogger(f'{self.__class__.__name__}')
        self._stop = False      # Internal stop, used to stop loop from within thread
    
        # Set up thread-safe metar data dict and new data flag
        self._live_metar_data_lock = Lock()
        self._live_metar_data: dict[str, METAR] | None = None
        self._new_metar_data_lock = Lock()
        self._new_metar_data: bool = False
        self._data_is_stale_lock = Lock()
        self._data_is_stale: bool = False
        self._is_running_lock = Lock()
        self._is_running: bool = False

        # Initialize parent classes in order
        Aviation_Weather_METAR.__init__(self, stations = stations)
        Thread.__init__(self)

        # Set up configurable times
        self._update_interval: timedelta = update_interval        # Setup interval time for updates
        self._stale_data_time: timedelta = stale_data_time          # Setup interval time for stale data timeout

        self._last_attempt_time = datetime.now()        # Time object to synchronize updates
        self._last_success_time = None

        if not wait_to_run:
            self.daemon = True
            self.start()

    @property
    def live_metar_data(self) -> dict[str, METAR | None] | None:
        """Thread-safe method to acquire the active METAR data dictionary of the thread"""
        with self._live_metar_data_lock:
            return self._live_metar_data
        
    @live_metar_data.setter
    def live_metar_data(self, new_metar_data: dict[str, METAR | None]) -> None:
        with self._live_metar_data_lock:
            self._live_metar_data = new_metar_data
        
    @property
    def new_metar_data(self) -> bool:
        with self._new_metar_data_lock:
            return self._new_metar_data
        
    @new_metar_data.setter
    def new_metar_data(self, new_metar_data_state: bool) -> None:
        with self._new_metar_data_lock:
            self._new_metar_data = new_metar_data_state

    @property
    def data_is_stale(self) -> bool:
        with self._data_is_stale_lock:
            return self._data_is_stale
        
    @data_is_stale.setter
    def data_is_stale(self, new_data_is_stale_state: bool) -> None:
        with self._data_is_stale_lock:
            self._data_is_stale = new_data_is_stale_state

    @property
    def is_running(self) -> bool:
        """Return if the thread is running correctly"""
        with self._is_running_lock:
            return self._is_running

    def _check_update_METAR_data(self) -> bool:
        """Attempt to update the metar data in the object, return success as bool"""
        self._last_attempt_time = datetime.now()
        self._logger.debug(f'Update Attempt time: {self._last_attempt_time}')
        if self.update_METAR_data():
            self._last_success_time = datetime.now()
            self._logger.debug(f'Update Success time: {self._last_success_time}')
            return True
        else:
            self._logger.debug('Queue not updated because self.updateMETARData returned False')
            return False
    
    def _check_for_stale_data(self) -> bool:
        '''
        Compares timedelta to last attempt against the stale data time parameter
        '''
        # If there has never been a success, the data is not considered stale
        if self._last_success_time is None:
            return False
        
        # Otherwise, check if the last success was longer than the stale data time in the past
        time_delta = get_time_delta_to_event(self._last_success_time)
        if time_delta > self._stale_data_time:
            return True
        return False
    
    def _check_time_delta_against_interval(self) -> bool:
        '''
        Compares timedelta to last attempt against the update interval parameter
        '''
        time_delta = get_time_delta_to_event(self._last_attempt_time)
        if time_delta > self._update_interval:
            return True
        return False

    def _update_live_METAR(self) -> None:
        '''
        Put the newest metar data in the shared attribute
        '''
        
        # Put the metar dict onto the queue
        self.live_metar_data = self._metar_data
        self.new_metar_data = True                # Set the new data flag
        if self._data_is_stale:                   # Set the stale flag to off
            self._data_is_stale = False
        return

    def loop(self):
        '''
        The thread loop, this is where the action happens
        We want to:
            1. Check how long it has been since we last retrieved data from the internet
            2. If it's been long enough, request new data for all stations
            3. Update the internal station data dictionary
            4. Add the new data to the queue for other processes to have access to
        '''
        
        # If enough time has elapsed and the METAR data can be successfully updated, push data onto the queue
        # and update the success_time to the curren time
        if self._check_time_delta_against_interval() or self._live_metar_data is None:
            if self._check_update_METAR_data():
                self._update_live_METAR()
                self._last_success_time = datetime.now()
            
        # Check if the current data in the queue is stale
        if self._check_for_stale_data():
            self._logger.debug('Setting data_is_stale')
            self.live_metar_data = None
            self.data_is_stale = True

    def stop(self) -> None:
        """Internal stop, log action"""
        self._logger.info(f'Internally driven stop for {self}, ident: {get_ident()}')
        self._stop = True
        return

    def run(self):
        """Run loop for thread"""
        
        # Clear stop flags
        self._stop = False
        self._is_running = True
        
        # Run loop until stop flag
        while not self._stop:
            try:
                self.loop()
            except:
                self._logger.exception(f'Unhandled exception in {self.__class__.__name__}')
                self._is_running = False
                self._stop = True
        self._is_running = False
            
        self._logger.warning('ADDSMETARThread has exited the loop')
        return

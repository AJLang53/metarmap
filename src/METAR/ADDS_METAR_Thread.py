from __future__ import annotations
import logging
from datetime import datetime, timedelta

# Python Threading
from threading import Thread, Event, Lock, get_ident

# Module Imports
from METAR.ADDSMETAR import ADDSMETAR, METAR

def get_time_delta_to_event(event_time: datetime) -> timedelta:
    '''
    Compare the current time against the event_time provided
    '''
    currentTime = datetime.now()
    time_delta = currentTime - event_time
    return time_delta

class ADDSMETARThread(ADDSMETAR, Thread):
    '''
    A thread that manages stations periodically to make available station METAR data through its queues
    '''

    def __init__(self, stop_request: Event,
                stations: list[str] | None = None,
                update_interval: timedelta = timedelta(seconds = 900),        # 15 minute update default
                stale_data_time: timedelta = timedelta(seconds = 5220),        # 1 Hour, 45 minutes for stale data defaults
                ):
        self._logger = logging.getLogger(f'{self.__class__.__name__}')
        self._stop = False      # Internal stop, used to stop loop from within thread
    
        # Setup Events
        self.stop_request = stop_request                                    # stop request event that can be used to kill the thread    

        # Set up thread-safe metar data dict and new data flag
        self._live_metar_data_lock = Lock()
        self._live_metar_data: dict[str, METAR] | None = None
        self._new_metar_data_lock = Lock()
        self._new_metar_data: bool = False
        self._is_running_lock = Lock()
        self._is_running: bool = False

        # Initialize parent classes in order
        ADDSMETAR.__init__(self, stations = stations)
        Thread.__init__(self)

        # Set up configurable times
        self._update_interval: timedelta = update_interval        # Setup interval time for updates
        self._stale_data_time: timedelta = stale_data_time          # Setup interval time for stale data timeout

        # Get the First Update
        if self._check_ADDS_Server_Connection():
            if not self._check_update_METAR_data():
                self._logger.warning(f'Initial updateMETARData call in ADDSMETARThread __init__ failed to successfully update data dictionary')
            else:
                self.update_METAR_data()
        else:
            self._logger.warning('No internet connection available in initializer for ADDSMETAR Thread')

        self._last_attempt_time = datetime.now()        # Time object to synchronize updates
    
    @property
    def live_metar_data(self) -> dict[str, METAR] | None:
        """Thread-safe method to acquire the active METAR data dictionary of the thread"""
        with self._live_metar_data_lock:
            return self._live_metar_data
        
    @live_metar_data.setter
    def live_metar_data(self, new_metar_data: dict[str, METAR]) -> None:
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
        if self._check_time_delta_against_interval() and self._check_update_METAR_data():
            self._update_live_METAR()
            self._last_success_time = datetime.now()
            
        # Check if the current data in the queue is stale
        if self._check_for_stale_data():
            self._logger.debug('Setting data_is_stale')
            self.live_metar_data = None

    def stop(self) -> None:
        """Internal stop, log action"""
        self._logger.info(f'Internally driven stop for {self}, ident: {get_ident()}')
        self._stop = True
        return

    def run(self):
        """Run loop for thread"""
        
        # Clear stop flags
        self._stop = False
        self.stop_request.clear()
        self._is_running = True
        
        # Run loop until stop flag
        while not self.stop_request.is_set() and not self._stop:
            self.loop()
        self._is_running = False
            
        self._logger.warning('ADDSMETARThread has exited the loop')
        return

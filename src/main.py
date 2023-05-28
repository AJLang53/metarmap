import os
import sys
from datetime import datetime, timedelta
import threading
import queue

import argparse
import logging, logging.handlers
from ADDSMETAR.ADDSMETAR import ADDSMETARThread
import ADDSMETAR.METAR as METAR

loop_inc = 0

def initializeRotatingLog(fileLevel = logging.WARNING):
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(fileLevel)

    # Send INFO messages to the console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(ch)

    # Log files in a logs folder at the main application level. Create this directory if it does not exist
    logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','logs')
    if not os.path.exists(logDir):
        os.mkdir(logDir)

    # Log file should be a file labeled date_metarmap
    logFileName = '{}_metarmap.log'.format(datetime.now().strftime('%Y-%m-%dT%H-%M-%S'))
    LOG_FILEPATH = os.path.join(logDir,logFileName)

    # Setup a Rotating Log File with fixed size for continuous logging
    # Allocate 250mb to this task, keeps file 10mb each
    rotHandler = logging.handlers.RotatingFileHandler(LOG_FILEPATH, maxBytes=10*1024*1024, backupCount=25)
    rotHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(rotHandler)

def getStationList():
    stationList = []
    path = os.path.join('data','GB_chicago_station_list.txt')
    with open(path) as f:
        for station in f:
            station = station.strip()
            stationList.append(station)
    return stationList

class MainLoop:
    '''
    Main program loop
    '''

    def __init__(self, stationList):
        self.stationList = stationList
        self.metar_data = {}

        self._initializeAddsMetarThread()

    def _initializeAddsMetarThread(self):
        '''
        Setup the ADDS METAR thread with it's parameters and events
        '''
        self.ADDSMETAR_stop_request = threading.Event()
        self.ADDSMETAR_stop_request.clear()
        self.new_metar_data = threading.Event()
        self.new_metar_data.clear()
        self.data_is_stale = threading.Event()
        self.data_is_stale.clear()
        self.metar_queue = queue.Queue()

        self.addsmetarThread = ADDSMETARThread(stations = self.stationList,
                                               update_interval=timedelta(seconds = 5),
                                               stale_data_time=timedelta(seconds = 20),
                                               stop_request=self.ADDSMETAR_stop_request,
                                               new_metar_data=self.new_metar_data,
                                               data_is_stale=self.data_is_stale,
                                               metar_queue=self.metar_queue
                                               )
        self.addsmetarThread.daemon = True
        self.addsmetarThread.start()

    def loop(self):
        global loop_inc
        self._check_for_new_METAR_data()
        # self._check_for_stale_data()
        try:
            if self.data_is_stale.is_set():
                pass
            else:
                key = list(self.metar_data.keys())[loop_inc]
                print(self.metar_data[key])
                loop_inc += 1
                if loop_inc >= len(self.metar_data.keys()):
                    loop_inc = 0
        except KeyError:
            # print('No key for OSH yet')
            pass

    def _check_for_new_METAR_data(self):
        try:
            if self.new_metar_data.is_set():                     # If there's new data in the thread
                newMetarDict = self.metar_queue.get()       # Get it from the queue
                self.metar_data = newMetarDict              # Set the current data dict to the new data
                self.new_metar_data.clear()                 # Clear the new data flag for the thread
        except:
            raise Exception('Unhandled Exception in _check_for_new_METAR_data')
        
    def _check_for_stale_data(self):
        raise Exception('Not Implemented')
        try:
            if self.data_is_stale.is_set():
                self.run_stale_behavior.set()
            elif not self.data_is_stale.is_set() and self.run_stale_behavior.is_set():
                self.run_stale_behavior.clear()
        except:
            self.logger.exception(f'Unhandled Exception in _check_for_stale_data')

def main():
    initializeRotatingLog(fileLevel = logging.DEBUG)
    stationList = getStationList()
    # stationList = ['KCWA']
    mainloop = MainLoop(stationList)
    stop_flag = False
    try:
        while not stop_flag:
            mainloop.loop()
    except KeyboardInterrupt:
        quit()

if __name__ == '__main__':
    main()
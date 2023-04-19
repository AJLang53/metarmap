import os
import sys
from datetime import datetime

import argparse
import logging, logging.handlers
import ADDSMETAR.ADDSMETAR as ADDSMETAR
import ADDSMETAR.METAR as METAR

# Setup root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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


def main():
    addsmetar = ADDSMETAR.ADDSMETAR(stations = ['KSLE','KPDX'])
    logger.info(addsmetar.getMETARofStation('KSLE'))
    logger.info(addsmetar.getMETARofStation('KMKE'))
    logger.info(addsmetar._updateMETARData())
    logger.info(addsmetar.getMETARofStation('KPDX').__dict__)

if __name__ == '__main__':
    main()
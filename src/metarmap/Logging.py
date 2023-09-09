import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

def initialize_basic_log_stream(logger: logging.Logger, level: int) -> None:
    """Setup a basic streamhandler for the provided logger"""
    # Send INFO messages to the console
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(name)-16s :: %(levelname)-8s :: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return

@dataclass
class Rotating_File_Logger_Config:
    level: int
    output_directory: Path
    output_name: str
    max_bytes: int
    backup_count: int

def initialize_rotating_file_log(logger: logging.Logger, 
                                 output_directory: Path, output_name: str, 
                                 fileLevel = logging.DEBUG,
                                 maxBytes: int = 10485760,      # Default 10 mb
                                 backupCount: int = 25,          # Default 250mb log
                                 manage_directory: bool = False,
                                 cycles_count: int = 8
                                ) -> None:
    """
    Set up a rotating log file for the logger provided using the input parameters
    
    Default parameters are 25, 10 Mb file for a total of 250mb stored log

    If manage_directory is set, then the system will first check how many unique .log items are in the directory
    If there are more than the cycles_count parameter, it will delete them starting with the oldest
    """

    # Setup root logger
    logger.setLevel(fileLevel)

    # Log files in a logs folder at the main application level. Create this directory if it does not exist
    log_dir = output_directory
    if not log_dir.exists():
        Path.mkdir(log_dir)

    # Log file should be a file labeled date_metarmap
    log_file_name = f'{datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}_{output_name}.log'
    # LOG_FILEPATH = os.path.join(logDir,logFileName)
    LOG_FILEPATH = log_dir / log_file_name

    # Setup a Rotating Log File with fixed size for continuous logging
    # Allocate 250mb to this task, keeps file 10mb each
    rotHandler = RotatingFileHandler(LOG_FILEPATH, maxBytes = maxBytes, backupCount = backupCount)
    formatter = logging.Formatter('[%(asctime)s] %(name)-16s :: %(levelname)-8s :: %(message)s')
    rotHandler.setFormatter(formatter)
    logger.addHandler(rotHandler)
    return
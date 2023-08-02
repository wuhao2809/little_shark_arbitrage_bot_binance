import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
import time
import datetime
from remote_logger.remote_logger_handler import RemoteLoggerHandler

def config_logging():

    logger = logging.getLogger('log_little_shark_v_1')
    logger.setLevel(logging.INFO)
    
    # google_client = google.cloud.logging.Client(project="little-shark-pair-binance")
    # google_handler = CloudLoggingHandler(google_client)

    fh = logging.FileHandler('log_little_shark.log')
    fh.setLevel(logging.INFO)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)


    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    
    # logger.addHandler(google_handler)

    return logger

logger = config_logging()


        


import logging
import time
import datetime
import sentry_sdk
from remote_logger.clients.sentry_logger_client import SentryLoggerClient
from remote_logger.remote_logger_handler import RemoteLoggerHandler

def config_logging():

    logger = logging.getLogger('log_little_shark_v_1')
    logger.setLevel(logging.INFO)


    fh = logging.FileHandler(f'log_little_shark_v_1.log')
    fh.setLevel(logging.INFO)


    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)


    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

# Remote logger
    # sentry_sdk.init(
    # dsn="https://c5ed4d21b1904955a365da0c8944394b@o4505479078412288.ingest.sentry.io/4505479080640512",

    # # Set traces_sample_rate to 1.0 to capture 100%
    # # of transactions for performance monitoring.
    # # We recommend adjusting this value in production.
    # traces_sample_rate=1.0
    # )
    # dsn = "https://c5ed4d21b1904955a365da0c8944394b@o4505479078412288.ingest.sentry.io/4505479080640512"
    # sentry_client = SentryLoggerClient(dsn=dsn)
    # sentry_handler = RemoteLoggerHandler(client=sentry_client)
    # sentry_handler.setLevel(logging.INFO)

    logger.addHandler(fh)
    logger.addHandler(ch)
    # logger.addHandler(sentry_handler)

    
    return logger

logger = config_logging()
        


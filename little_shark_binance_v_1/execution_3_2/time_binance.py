import datetime

def get_current_date_time_binance():
    current_time = datetime.datetime.now()
    return current_time

def get_current_time_timestamp_binance():
    return int(get_current_date_time_binance().timestamp() * 1000)

def transform_datetime_to_binance(time: datetime):
    return time

def transform_datetime_to_binance_timestamp(time: datetime):
    return int(time.timestamp() * 1000)

def transform_timestamp_to_datetime(timestamp: int):
    return datetime.datetime.fromtimestamp(int(timestamp)/1000)

    


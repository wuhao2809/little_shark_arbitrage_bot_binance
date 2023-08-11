from config import session_public
from time_binance import transform_timestamp_to_datetime

time = session_public.time()["serverTime"]
datetime = transform_timestamp_to_datetime(time)
print(datetime)
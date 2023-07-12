from config import api_key, api_secret
import time
import logging
from binance.um_futures import UMFutures
from binance.cm_futures import CMFutures
from binance.lib.utils import config_logging


from time_binance import transform_timestamp_to_datetime, get_current_time_timestamp_binance

# um_futures_client = UMFutures()
# print(um_futures_client.time())


# Get account information

um_futures_client = UMFutures()

# config_logging(logging, logging.DEBUG)

# get server time
# print(transform_timestamp_to_datetime(um_futures_client.time()["serverTime"]))

def find_symbols_binance():
    symbol_list = []
    symbols = um_futures_client.exchange_info()["symbols"]
    for symbol in symbols:
        if symbol["status"] == "TRADING" and symbol["quoteAsset"] == "USDT" and symbol["contractType"] == "PERPETUAL":
            symbol_list.append(symbol["symbol"])
            # symbol_list.append(symbol["onboardDate"])
    return len(symbol_list)

def get_499_price_15m():
    return len(um_futures_client.klines("BTCUSDT", "15m",limit = 499))

"""Note: binance get price from the past to present, meaning that [-1] should be the current time"""
# print(find_symbols_binance())
# print(find_symbols_binance())
# print(get_499_price_15m())
# print(transform_timestamp_to_datetime(1688481899999))
# print(um_futures_client.exchange_info()["symbols"])
print(um_futures_client.ticker_24hr_price_change("BTCUSDT"))
print(transform_timestamp_to_datetime(1688934509786))
    

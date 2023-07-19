"""This is the file used to store all the functions related to get target symbols"""

from experiment_config import onboard_time_threshod, trading_volume_threshod, interval, num_interval_limit, trigger_z_score_threshod
from binance_market_observer import binance_get_exchange_symbols, binance_get_24h_trading_volume_usdt, binance_get_recent_close_price
from time_binance import transform_timestamp_to_datetime
from config_logger import logger
import pandas as pd
import numpy as np
import json
import time

# get all the tradeable symbols from binance
def get_tradeable_symbols_dynamic() -> list:
    """Get tradeable symbols from the Binance, and return the list of 
    symbols and the number of tradeable pairs
    
    Only trade on USDT
    Only trade the coins that are on board for a certain time period

    Args:
       None

    Returns:
        sym_list(list): the list contains all the tradeable symbols
        count(int): the size of the list
    """
    count = 0
    sym_list = []
    BTCUSDT_trading_volume = binance_get_24h_trading_volume_usdt("BTCUSDT")
    
    symbols = binance_get_exchange_symbols()
    for symbol in symbols:
        if (symbol["quoteAsset"] == "USDT" and symbol["status"]=="TRADING"
            and transform_timestamp_to_datetime(symbol["onboardDate"]) <= onboard_time_threshod # coins onboard should not be later than this time
            and binance_get_24h_trading_volume_usdt(symbol["symbol"]) >= trading_volume_threshod * BTCUSDT_trading_volume): # trading volume
            
            sym_list.append(symbol["symbol"])
            count += 1
            time.sleep(0.1)
    logger.info(f"{count} pairs found")

    # return all the tradeable symbol and the size of the list
    return sym_list


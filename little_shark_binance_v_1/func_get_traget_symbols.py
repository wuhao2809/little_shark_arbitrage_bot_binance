"""This is the file used to store all the functions related to get target symbols"""

from config import onboard_time_threshod, trading_volume_threshod, interval, num_interval_limit, trigger_z_score_threshod
from binance_market_observer import binance_get_exchange_symbols, binance_get_24h_trading_volume_usdt, binance_get_recent_close_price
from time_binance import transform_timestamp_to_datetime
from func_calculation_static import calculate_cointegration_static, calculate_spread_static, calculate_zscore_static, calculate_trading_estimated_oppotunities_return
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




# Store price histry for all available pairs
def store_price_history_static(symbols: list) -> str:
    """
    Store the price history for the given symbols and return the filename of the stored data.

    Args:
        symbols (list): List of symbols for which price history needs to be stored.

    Returns:
        str: Filename of the stored data.
    """
    
    # Get prices and store in DataFrame
    counts = 0
    price_history_dict = {}
    for sym in symbols:
        price_history = binance_get_recent_close_price(sym, interval=interval, limit=num_interval_limit)
        if len(price_history) == num_interval_limit: # make sure that each symbol has the same amount of data
            price_history_dict[sym] = price_history
            counts += 1
    logger.info (f"{counts} items stored, {len(symbols)-counts}items not stored")
    
    # Output prices to JSON
    if len(price_history_dict) > 0:
        filename = f"{interval}_price_list.json"
        with open(filename, "w") as fp:
            json.dump(price_history_dict, fp, indent=4)
        logger.info("Prices saved successfully.")

    # Return output
    return filename


def get_cointegrated_pairs(prices, num_wave=0) -> str:

    # Loop through coins and check for co-integration
    coint_pair_list = []
    
    found_pair_list = list(prices.keys())
    loop_count = 0
    for sym_1 in found_pair_list:
        loop_count += 1
        # Check each coin against the first (sym_1)
        for sym_2 in found_pair_list[loop_count:]:
            
            # Get close prices
            series_1 = prices[sym_1]
            series_2 = prices[sym_2]

            # Check for cointegration and add cointegrated pair
            coint_flag, p_value, hedge_ratio, initial_intercept = calculate_cointegration_static(series_1, series_2)
            
            
            current_z_score = calculate_zscore_static(calculate_spread_static(series_1, series_2, hedge_ratio))[-1] # In binance, the last price is the latest price
            trading_oppotunities, estimated_return = calculate_trading_estimated_oppotunities_return(series_1, series_2, hedge_ratio, initial_intercept, trigger_z_score_threshod)
            if coint_flag == 1:
                coint_pair_list.append({
                    "sym_1": sym_1,
                    "sym_2": sym_2,
                    "p_value": p_value,
                    "hedge_ratio": hedge_ratio,
                    "initial_intercept": initial_intercept,
                    "trading_oppotunities": trading_oppotunities,
                    "estimated_return": estimated_return,
                    "current_z_score": current_z_score,
                })

    # Output results and rank all the trading pairs
    df_coint = pd.DataFrame(coint_pair_list)
    # add the total score column
    df_coint["total_score"] = df_coint["estimated_return"]
    df_coint = df_coint.sort_values("estimated_return", ascending=False)
    filename = f"{num_wave}_cointegrated_pairs.csv"
    df_coint.to_csv(filename)
    return filename
    
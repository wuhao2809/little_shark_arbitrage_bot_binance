"""This is the file used to store all the functions related to get target symbols"""

from config import ONBOARD_TIME_THRESHOD, TRADING_VOLUME_THRESHOD_RATE, INTERVAL, NUM_INTERVAL_LIMIT, TRIGGER_Z_SCORE_THRESHOD, Z_SCORE_WINDOW, TRADING_TIMES_THRESHOD, INVESTIBLE_CAPITAL_EACH_TIME, TRADING_FEE_RATE, WIN_RATE_THRESHOD, EXTREME_VALUE_MEAN_RATE_THRESHOD, STOP_LOSS_RATIO, TRADING_TIME_LIMIT_INTERVALS, ACCOUNT_BALANCE_INVESTABLE
from binance_market_observer import binance_get_exchange_symbols, binance_get_24h_trading_volume_usdt, binance_get_recent_close_price, binance_get_latest_price, binance_get_min_trading_qty
from time_binance import transform_timestamp_to_datetime
from func_calculation_static import calculate_cointegration_static, calculate_spread_static, calculate_z_score_window, calculate_std_spread, calculate_spread_hedge_ratio_window
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
            and transform_timestamp_to_datetime(symbol["onboardDate"]) <= ONBOARD_TIME_THRESHOD # coins onboard should not be later than this time
            and binance_get_24h_trading_volume_usdt(symbol["symbol"]) >= TRADING_VOLUME_THRESHOD_RATE * BTCUSDT_trading_volume): # trading volume
            
            sym_list.append(symbol["symbol"])
            count += 1
            time.sleep(0.1)
    logger.info(f"{count} pairs found")

    # return all the tradeable symbol and the size of the list
    return sym_list

# syms = get_tradeable_symbols_dynamic()
# print(syms)


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
        price_history = binance_get_recent_close_price(sym, interval=INTERVAL, limit=NUM_INTERVAL_LIMIT + Z_SCORE_WINDOW)
        if len(price_history) == NUM_INTERVAL_LIMIT + Z_SCORE_WINDOW: # make sure that each symbol has the same amount of data
            price_history_dict[sym] = price_history
            counts += 1
    logger.info (f"{counts} items stored, {len(symbols)-counts}items not stored")
    
    # Output prices to JSON
    if len(price_history_dict) > 0:
        filename = f"{INTERVAL}_price_list.json"
        with open(filename, "w") as fp:
            json.dump(price_history_dict, fp, indent=4)
        logger.info("Prices saved successfully.")

    # Return output
    return filename

def check_differnet_signal(a,b):
    return abs(a + b) != abs(a) + abs(b)

def get_backtesting_properties(series_1: list, series_2: list, hedge_ratio: float, zscore_series: list):
    trade_oppotunities = 0
    last_value = 0.00
    enter_market_signal = False
    
    cumulative_return = 0
    cumulative_trading_qty = 0
    count_entering_time = 0
    
    open_long_price_list = []
    open_short_price_list = []
    
    win_times = 0
    peak_loss = 0
    
    
    for index, value in enumerate(zscore_series):
        if abs(value) >= abs(TRIGGER_Z_SCORE_THRESHOD) and not check_differnet_signal(value, last_value):
            
            enter_market_signal = True
            
            if value >= TRIGGER_Z_SCORE_THRESHOD:
                direction = "sell"
            elif value <= -TRIGGER_Z_SCORE_THRESHOD:
                direction = "buy"
            
            if count_entering_time < TRADING_TIMES_THRESHOD:
                cumulative_trading_qty += (INVESTIBLE_CAPITAL_EACH_TIME / (series_1[index] + hedge_ratio * series_2[index]))  # qty for each symbol
                if direction == "buy":
                    open_long_price_list.append(series_1[index])
                    open_short_price_list.append(series_2[index])
                elif direction == "sell":
                    open_short_price_list.append(series_1[index])
                    open_long_price_list.append(series_2[index])
                    
                count_entering_time += 1

        # Calculate the peak loss during the trade
        if enter_market_signal:
            if direction == "buy":
                long_profit = (series_1[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty
                short_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_2[index]) * cumulative_trading_qty * hedge_ratio
            elif direction == "sell":
                long_profit = (series_2[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty * hedge_ratio
                short_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_1[index]) * cumulative_trading_qty
            current_revenue = long_profit + short_profit
            peak_loss = min(peak_loss, current_revenue)
        
        # Calculate the returns when exiting the market
        if enter_market_signal and check_differnet_signal(value, last_value):
            trade_oppotunities += 1
            exiting_profit = current_revenue - INVESTIBLE_CAPITAL_EACH_TIME * count_entering_time * TRADING_FEE_RATE # revenue for all symbols
            
            # calculate the win rate
            if exiting_profit > 0:
                win_times += 1

            # Cumulate the return
            cumulative_return += exiting_profit
            
            # Reset
            enter_market_signal = False
            cumulative_trading_qty = 0
            count_entering_time = 0
            direction = ""
            open_long_price_list = []
            open_short_price_list = []
        
        last_value = value
    
    if trade_oppotunities > 0:
        win_rate = win_times / trade_oppotunities
    else:
        win_rate = 0
    
    # Calculate the recent trade qty
    recent_trade_qty = (INVESTIBLE_CAPITAL_EACH_TIME / (series_1[-1] + hedge_ratio * series_2[-1]))
    
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss

def get_backtesting_properties_dynamic(series_1: list, series_2: list, hedge_ratio_list: float, zscore_series: list, TRIGGER_Z_SCORE_THRESHOD: float):
    trade_oppotunities = 0
    last_value = 0.00
    enter_market_signal = False
    
    cumulative_return = 0
    cumulative_trading_qty = 0
    count_entering_time = 0
    
    open_long_price_list = []
    open_short_price_list = []
    
    win_times = 0
    peak_loss = 0
    
    
    for index, value in enumerate(zscore_series):
        if abs(value) >= abs(TRIGGER_Z_SCORE_THRESHOD) and not check_differnet_signal(value, last_value):
            
            enter_market_signal = True
            
            if value >= TRIGGER_Z_SCORE_THRESHOD:
                direction = "sell"
            elif value <= -TRIGGER_Z_SCORE_THRESHOD:
                direction = "buy"
            
            if count_entering_time < TRADING_TIMES_THRESHOD:
                cumulative_trading_qty += (INVESTIBLE_CAPITAL_EACH_TIME / (series_1[index] + hedge_ratio_list[index] * series_2[index]))  # qty for each symbol
                if direction == "buy":
                    open_long_price_list.append(series_1[index])
                    open_short_price_list.append(series_2[index])
                elif direction == "sell":
                    open_short_price_list.append(series_1[index])
                    open_long_price_list.append(series_2[index])
                    
                count_entering_time += 1

        # Calculate the peak loss during the trade
        if enter_market_signal:
            if direction == "buy":
                long_profit = (series_1[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty
                short_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_2[index]) * cumulative_trading_qty * hedge_ratio_list[index]
            elif direction == "sell":
                long_profit = (series_2[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty * hedge_ratio_list[index]
                short_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_1[index]) * cumulative_trading_qty
            current_revenue = long_profit + short_profit
            peak_loss = min(peak_loss, current_revenue)
        
        # Calculate the returns when exiting the market
        if enter_market_signal and check_differnet_signal(value, last_value):
            trade_oppotunities += 1
            exiting_profit = current_revenue - INVESTIBLE_CAPITAL_EACH_TIME * count_entering_time * TRADING_FEE_RATE # revenue for all symbols
            
            # calculate the win rate
            if exiting_profit > 0:
                win_times += 1

            # Cumulate the return
            cumulative_return += exiting_profit
            
            # Reset
            enter_market_signal = False
            cumulative_trading_qty = 0
            count_entering_time = 0
            direction = ""
            open_long_price_list = []
            open_short_price_list = []
        
        last_value = value
    
    if trade_oppotunities > 0:
        win_rate = win_times / trade_oppotunities
    else:
        win_rate = 0
    
    return trade_oppotunities, cumulative_return, win_rate, peak_loss


def calculate_pairs_trading_result(series_1, series_2, hedge_ratio: float, num_window: int) -> tuple:
    
    spread = calculate_spread_static(series_1, series_2, hedge_ratio)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    std = calculate_std_spread(spread)
    
    # Get recent z score
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss = get_backtesting_properties(series_1, series_2, hedge_ratio, zscore_series)
        
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, recent_z_score, peak_loss, std

def calculate_pairs_trading_result_dynamic(series_1, series_2, num_window: int, z_score_threshod: float) -> tuple:
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1, series_2, window=num_window)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, peak_loss = get_backtesting_properties_dynamic(series_1, series_2, hedge_ratio_list, zscore_series, z_score_threshod)
    
    return trade_oppotunities, cumulative_return, win_rate, recent_z_score, peak_loss

def get_trade_qty_each_time(symbol_1: str, symbol_2: str, hedge_ratio):
    estimated_trade_qty_symbol_1 = INVESTIBLE_CAPITAL_EACH_TIME / (binance_get_latest_price(symbol_1) + hedge_ratio * binance_get_latest_price(symbol_2))
    estimated_trade_qty_symbol_2 = (estimated_trade_qty_symbol_1 * hedge_ratio)
    
    return estimated_trade_qty_symbol_1, estimated_trade_qty_symbol_2
    
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
            
            # Get recent NUM_LIMITS prices.
            series_1_coint_test = prices[sym_1][Z_SCORE_WINDOW:]
            series_2_coint_test = prices[sym_2][Z_SCORE_WINDOW:]

            # Check for cointegration and add cointegrated pair
            coint_flag, p_value, hedge_ratio, initial_intercept = calculate_cointegration_static(series_1_coint_test, series_2_coint_test)
            

            
            if (coint_flag == 1) and (hedge_ratio > 0.001) and (hedge_ratio < 1000):
                trade_oppotunities, cumulative_returns, win_rate, recent_trade_qty, _, _, std = calculate_pairs_trading_result(series_1,
                                                                                                                                              series_2,
                                                                                                                                              hedge_ratio,
                                                                                                                                              Z_SCORE_WINDOW)
                if cumulative_returns > 0 and win_rate > WIN_RATE_THRESHOD:
                    min_trading_qty_symbol_1 = binance_get_min_trading_qty(sym_1)
                    min_trading_qty_symbol_2 = binance_get_min_trading_qty(sym_2)
                    
                    estimated_trade_qty_symbol_1, estimated_trade_qty_symbol_2 = get_trade_qty_each_time(sym_1, sym_2, hedge_ratio)
                    
                    symbol_1_current_price = binance_get_latest_price(sym_1)
                    symbol_2_current_price = binance_get_latest_price(sym_2)
                    
                    estimated_trade_value_symbol_1 = estimated_trade_qty_symbol_1 * symbol_1_current_price
                    estimated_trade_value_symbol_2 = estimated_trade_qty_symbol_2 * symbol_2_current_price
                    
                    series_1_performance_test = series_1[len(series_1) -1 - TRADING_TIME_LIMIT_INTERVALS - 2 * Z_SCORE_WINDOW:]
                    series_2_performance_test = series_2[len(series_2) -1 - TRADING_TIME_LIMIT_INTERVALS - 2 * Z_SCORE_WINDOW:]
                    trade_oppotunities_performance, cumulative_returns_performance, win_rate_performance, recent_z_score, peak_loss_performace= calculate_pairs_trading_result_dynamic(series_1_performance_test,
                                                                                                                                                series_2_performance_test,
                                                                                                                                                Z_SCORE_WINDOW,
                                                                                                                                                TRIGGER_Z_SCORE_THRESHOD)
                    
                    coint_pair_list.append({
                        "sym_1": sym_1,
                        "sym_2": sym_2,
                        "min_trading_qty_symbol_1": min_trading_qty_symbol_1,
                        "min_trading_qty_symbol_2": min_trading_qty_symbol_2,
                        "estimated_trade_qty_symbol_1": estimated_trade_qty_symbol_1,
                        "estimated_trade_qty_symbol_2": estimated_trade_qty_symbol_2,
                        "estimated_trade_value_symbol_1": estimated_trade_value_symbol_1,
                        "estimated_trade_value_symbol_2": estimated_trade_value_symbol_2,
                        "std":std,
                        "each_z_score_revenue": estimated_trade_qty_symbol_1 * std,
                        "p_value": p_value,
                        "hedge_ratio": hedge_ratio,
                        "initial_intercept": initial_intercept,
                        "trade_oppotunities_performance": trade_oppotunities_performance,
                        "cumulative_returns_performance": cumulative_returns_performance,
                        "win_rate_performance": win_rate_performance,
                        "recent_trade_qty": recent_trade_qty,
                        "peak_loss_performace": peak_loss_performace,
                        "recent_z_score": recent_z_score,
                    })

    # Output results and rank all the trading pairs
    df_coint = pd.DataFrame(coint_pair_list)
    # add the total score column
    df_coint = df_coint.sort_values("cumulative_returns_performance", ascending=False)
    filename = f"{num_wave}_cointegrated_pairs.csv"
    df_coint.to_csv(filename)
    return df_coint

def choose_best_trading_pair_static(df_coint: pd.DataFrame) ->tuple:
    # filter out pairs based on min_trading_value
    df_coint = df_coint.loc[df_coint["estimated_trade_qty_symbol_1"] > df_coint["min_trading_qty_symbol_1"]]
    df_coint = df_coint.loc[df_coint["estimated_trade_qty_symbol_2"] > df_coint["min_trading_qty_symbol_2"]]
    df_coint = df_coint[df_coint["estimated_trade_value_symbol_1"] > 6]
    df_coint = df_coint[df_coint["estimated_trade_value_symbol_2"] > 6]
    
    # filter the top 1/2 based on returns
    df_coint = df_coint[df_coint["cumulative_returns_performance"] > 0]
    df_coint = df_coint.sort_values("cumulative_returns_performance", ascending=False).head(int(df_coint.shape[0]/2))
    
    # filter based on win rate
    df_coint = df_coint[df_coint["win_rate_performance"] >= WIN_RATE_THRESHOD]
    
    
    # filter out extreme values based on estimated returns
    mean = df_coint["cumulative_returns_performance"].mean()
    df_coint = df_coint[df_coint["cumulative_returns_performance"] < EXTREME_VALUE_MEAN_RATE_THRESHOD * mean]
    
    # filter out pairs have a high loss during the trade
    df_coint = df_coint[abs(df_coint["peak_loss_performace"]) < ACCOUNT_BALANCE_INVESTABLE * STOP_LOSS_RATIO]
    
    # rank them based on returns
    df_coint = df_coint.sort_values("cumulative_returns_performance", ascending=False)
    
    # choose the one with a tradeable z-score
    for i in range(df_coint.shape[0]):
        if abs(df_coint["recent_z_score"].values[i]) > TRIGGER_Z_SCORE_THRESHOD:
            symbol_1 = df_coint["sym_1"].values[i]
            symbol_2 = df_coint["sym_2"].values[i]

            return True, symbol_1, symbol_2
    
    return False, 0, 0
    
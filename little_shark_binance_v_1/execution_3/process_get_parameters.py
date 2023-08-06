from binance.um_futures import UMFutures
from statsmodels.regression.rolling import RollingOLS
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import scipy.stats as stats
import pandas as pd
import numpy as np
import datetime
import time
import json

from config import TRADING_TIMES_THRESHOD, INVESTIBLE_CAPITAL_EACH_TIME, TRADING_FEE_RATE
from config_logger import logger
from func_get_traget_symbols import get_tradeable_symbols_dynamic, get_trade_qty_each_time, check_differnet_signal
from func_calculation_static import calculate_cointegration_static, calculate_spread_hedge_ratio_window, calculate_z_score_window, calculate_std_spread, calculate_spread_static, calculate_zscore_static
from binance_market_observer import binance_get_24h_trading_volume_usdt, binance_get_exchange_symbols, binance_get_recent_close_price, binance_get_latest_price
from time_binance import transform_timestamp_to_datetime

# Set config
SET_INTERVALS = ["15m"]

# SET_TRAINNING_PERIODS = [200, 300, 400, 500, 600, 800]
# SET_Z_SCORE_WINDOW = [20, 40, 60, 80, 120, 160, 200]
# SET_TRIGGER_Z_SCORE_THRESHOD = [0.8, 1.2, 1.6, 2.0]

SET_TRAINNING_PERIODS = [200, 400]
SET_SPREAD_WINDOW = [20, 40, 80, 120]
SET_Z_SCORE_WINDOW = [20, 40, 80, 120]
SET_TRIGGER_Z_SCORE_THRESHOD = [1.2, 1.6]

session_public = UMFutures()


# Store price histry for all available pairs
def store_price_history_static(symbols: list, interval) -> str:
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
        price_history = binance_get_recent_close_price(sym, interval=interval, limit=1500)
        if len(price_history) == 1500: # make sure that each symbol has the same amount of data
            price_history_dict[sym] = price_history
            counts += 1
    logger.info(f"{counts} items stored, {len(symbols)-counts}items not stored")
    
    # Output prices to JSON
    if len(price_history_dict) > 0:
        filename = f"{interval}_price_list.json"
        with open(filename, "w") as fp:
            json.dump(price_history_dict, fp, indent=4)
        logger.info("Prices saved successfully.")
    time.sleep(5)


def get_backtesting_properties(series_1: list, series_2: list, hedge_ratio_list: float, zscore_series: list, TRIGGER_Z_SCORE_THRESHOD: float):
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
    peak_profit = 0
    
    
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
            peak_profit = max(peak_profit, current_revenue)
        
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
    recent_trade_qty = (INVESTIBLE_CAPITAL_EACH_TIME / (series_1[-1] + hedge_ratio_list[-1] * series_2[-1]))
    
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss, peak_profit

def get_backtesting_properties_static(series_1: list, series_2: list, hedge_ratio: float, zscore_series: list, TRIGGER_Z_SCORE_THRESHOD: float):
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

def calculate_pairs_trading_result_dynamic(series_1, series_2, spread_window, num_window: int, z_score_threshod: float) -> tuple:
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1, series_2, window=spread_window)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    std = calculate_std_spread(spread)
    # print(zscore_series)
    
    # Get recent z score
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss, peak_profit = get_backtesting_properties(series_1[-50:], series_2[-50:], hedge_ratio_list[-50:], zscore_series[-50:], z_score_threshod)
        
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, recent_z_score, peak_profit, peak_loss, std


def calculate_pairs_trading_result_static(series_1, series_2, hedge_ratio: float, num_window: int, z_score_threshod) -> tuple:
    
    spread = calculate_spread_static(series_1, series_2, hedge_ratio)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    std = calculate_std_spread(spread)
    
    # Get recent z score
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss = get_backtesting_properties_static(series_1, series_2, hedge_ratio, zscore_series,z_score_threshod)
        
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, recent_z_score, peak_loss, std
    
def get_cointegrated_pairs(prices, interval, trainning_period, spread_window, z_score_window, z_score_threshod) -> str:

    # Loop through coins and check for co-integration
    coint_pair_list = []
    
    found_pair_list = list(prices.keys())
    loop_count = 0
    for sym_1 in found_pair_list:
        loop_count += 1
        # Check each coin against the first (sym_1)
        for sym_2 in found_pair_list[loop_count:]:

            # Get close prices not the last 50 intervals
            series_1 = prices[sym_1]
            series_2 = prices[sym_2]
            
            series_1 = series_1[:len(series_1) - 50]
            series_2 = series_2[:len(series_2) - 50]
            
            # Get recent NUM_LIMITS prices.
            series_1_coint_test = series_1[len(series_1) - trainning_period:]
            series_2_coint_test = series_2[len(series_2) - trainning_period:]

            # Check for cointegration and add cointegrated pair
            coint_flag, p_value, hedge_ratio, initial_intercept = calculate_cointegration_static(series_1_coint_test, series_2_coint_test)
            # Stage 1 complete
            
            if (coint_flag == 1) and (hedge_ratio > 0.001) and (hedge_ratio < 1000):
                
                series_1_train_test = series_1[-(trainning_period + z_score_window):]
                series_2_train_test = series_2[-(trainning_period + z_score_window):]
                trade_oppotunities, cumulative_returns, win_rate, recent_trade_qty, recent_z_score, peak_loss, std = calculate_pairs_trading_result_static(series_1_train_test,
                                                                                                                                              series_2_train_test,
                                                                                                                                              hedge_ratio,
                                                                                                                                              z_score_window,
                                                                                                                                              z_score_threshod)
                if cumulative_returns > 0 and win_rate > 0.7 and abs(peak_loss) < 100:
                    series_1_real_test = series_1[-(50 + spread_window + z_score_window):]
                    series_2_real_test = series_2[-(50 + spread_window + z_score_window):]
                    
                    trade_oppotunities_performance, cumulative_returns_performance, win_rate_performance, _, _, peak_profit, peak_loss_performace, _ = calculate_pairs_trading_result_dynamic(series_1_real_test,
                                                                                                                                                series_2_real_test,
                                                                                                                                                spread_window,
                                                                                                                                                z_score_window,
                                                                                                                                                z_score_threshod)
                    
                    
                    series_1_examine_test = prices[sym_1][-(50 + spread_window + z_score_window):]
                    series_2_examine_test = prices[sym_2][-(50 + spread_window + z_score_window):]
                    examine_trade_oppotunities, examine_returns, examine_win_rate, _, _, examine_peak_profit, examine_peak_loss, _ = calculate_pairs_trading_result_dynamic(series_1_examine_test, series_2_examine_test, spread_window, z_score_window, z_score_threshod)
                    
                    coint_pair_list.append({
                        "sym_1": sym_1,
                        "sym_2": sym_2,
                        "hedge_ratio": hedge_ratio,
                        "std":std,
                        "p_value": p_value,
                        "trade_oppotunities_performance": trade_oppotunities_performance,
                        "cumulative_returns_performance": cumulative_returns_performance,
                        "win_rate_performance": win_rate_performance,
                        "peak_loss_performace": peak_loss_performace,
                        "recent_z_score": recent_z_score,
                        "examine_trade_oppotunities": examine_trade_oppotunities,
                        "examine_returns": examine_returns,
                        "examine_win_rate": examine_win_rate,
                        "examine_peak_profit": examine_peak_profit,
                        "examine_peak_loss": examine_peak_loss,
                    })

    df_coint = pd.DataFrame(coint_pair_list)
    # add the total score column
    if df_coint.shape[0] == 0:
        coint_pair_list.append({
                        "sym_1": 0,
                        "sym_2": 0,
                        "hedge_ratio": 0,
                        "std":0,
                        "p_value": 0,
                        "trade_oppotunities_performance": 0,
                        "cumulative_returns_performance": 0,
                        "win_rate_performance": 0,
                        "peak_loss_performace": 0,
                        "recent_z_score": 0,
                        "examine_trade_oppotunities": 0,
                        "examine_returns": 0,
                        "examine_win_rate": 0,
                        "examine_peak_profit": 0,
                        "examine_peak_loss": 0,
                    })
        df_coint = pd.DataFrame(coint_pair_list)
        # Output results and rank all the trading pairs
   
    df_coint = df_coint.sort_values("examine_returns", ascending=False)
    # choose positive hedge ratio
    df_coint = df_coint[df_coint["hedge_ratio"] > 0]
    # filename = f"{interval}_{trainning_period}_{spread_window}_{z_score_window}_{z_score_threshod}_cointegrated_pairs.csv"
    # df_coint.to_csv(filename)
    logger.info(f"{interval}_{trainning_period}_{spread_window}_{z_score_window}_{z_score_threshod} has been completed")
    return df_coint


def test_parameters(interval, trainning_period, spread_window, z_score_window, z_score_threshod):
    with open (f"{interval}_price_list.json") as json_file:
        price_data = json.load(json_file)
        df_coint = get_cointegrated_pairs(price_data, interval, trainning_period, spread_window, z_score_window, z_score_threshod)
        return df_coint

def get_trainning_result(df_coint: pd.DataFrame):
    # pick the best pair
    df_coint = df_coint[df_coint["cumulative_returns_performance"] > 0].head(10)
    df_coint = df_coint[abs(df_coint["peak_loss_performace"]) < 0.12 * INVESTIBLE_CAPITAL_EACH_TIME * TRADING_TIMES_THRESHOD]
    df_coint = df_coint[df_coint["win_rate_performance"] > 0.7]
    
    # pick smallest 2/3 based on peak loss
    df_coint = df_coint.sort_values("peak_loss_performace", ascending=True).head(int(df_coint.shape[0] * (2/3)) + 1)
    # pick top 2/3 based on win rate
    df_coint = df_coint.sort_values("win_rate_performance", ascending=False).head(int(df_coint.shape[0] * (2/3)) + 1)
    # pick top 2/3 based on trade oppotunities
    df_coint = df_coint.sort_values("trade_oppotunities_performance", ascending=False).head(int(df_coint.shape[0] * (2/3)) + 1)

    # examine the trading pair
    average_return = df_coint["examine_returns"].mean()
    average_loss = df_coint[df_coint["examine_returns"] < 0]["examine_returns"].mean()
    average_win_rate = df_coint["examine_win_rate"].mean()
    
    # if df_coint.shape[0] != 0:
    #     win_rate = (df_coint[df_coint["examine_returns"] > 0].shape[0] / df_coint.shape[0])
    # else: win_rate = 0

    if df_coint[df_coint["examine_returns"] > 0].shape[0] > 0:
        tradeable_num = df_coint[df_coint["examine_returns"] > 0].shape[0]
    else: tradeable_num = 0
    return average_return, average_win_rate, average_loss, tradeable_num, df_coint

def select_parameters(df: pd.DataFrame):
    dict = {}
    
    df = df[df["test_average_returns"] > 0]
    df = df[df["test_win_rate"] > 0.7]
    df = df.sort_values("test_average_returns", ascending=False)
    trainning_period = int(df["trainning_period"].values[0])
    spread_window = int(df["spread_window"].values[0])
    z_score_window = int(df["z_score_window"].values[0])
    z_score_threshod = float(df["z_score_threshod"].values[0])
    
    dict = {"trainning_period": trainning_period, "spread_window": spread_window, "z_score_window": z_score_window, "z_score_threshod": z_score_threshod}
    logger.critical(f"Parameters found, {dict}")
    with open ("parameters.json", "w") as json_file:
        json.dump(dict, json_file, indent=4)

def process_get_parameters():
    tradeable_symbols = get_tradeable_symbols_dynamic()
    for interval in SET_INTERVALS:
        store_price_history_static(tradeable_symbols, interval)
    logger.info("price saved")

    result_list = []

    for interval in SET_INTERVALS:
        for trainning_period in SET_TRAINNING_PERIODS:
            for spread_window in SET_SPREAD_WINDOW:
                for z_score_window in SET_Z_SCORE_WINDOW:
                    for z_score_threshod in SET_TRIGGER_Z_SCORE_THRESHOD:
                        df_coint = test_parameters(interval, trainning_period, spread_window, z_score_window, z_score_threshod)
                        average_return, win_rate, average_loss, tradeable_num, selected_pairs_pd = get_trainning_result(df_coint)
                        
                        # print(average_return, win_rate, average_loss, tradeable_num)
                        temp_dict = {"interval":interval, "trainning_period": trainning_period, "spread_window": spread_window,"z_score_window": z_score_window,
                                    "z_score_threshod": z_score_threshod, "test_average_returns": average_return, "test_win_rate":win_rate,
                                    "test_ave_loss": average_loss, "tradeable_num": tradeable_num}
                        # selected_pairs_pd.to_csv(f"{interval}_{trainning_period}_{spread_window}_{z_score_window}_{z_score_threshod}_selected_pairs.csv")
                        result_list.append(temp_dict)
    df_result = pd.DataFrame(result_list)
    df_result.to_csv("parameters_result_list.csv")
    analysis_result = pd.read_csv("parameters_result_list.csv")
    result = select_parameters(analysis_result)

# process_get_parameters()
    


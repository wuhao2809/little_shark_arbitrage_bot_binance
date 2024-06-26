"""This is the file used to store all the functions related to get target symbols"""

from config import config, ONBOARD_TIME_THRESHOD, TRADING_VOLUME_THRESHOD_RATE, TRADING_TIMES_THRESHOD, INVESTIBLE_CAPITAL_EACH_TIME, TRADING_FEE_RATE, BACKTEST_INTERVAL, WIN_RATE_THRESHOD_DYNAMIC, STOP_LOSS_VALUE
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
    """
    Get tradeable symbols from Binance and return the list of symbols and the number of tradeable pairs.
    
    Only trade on USDT.
    Only trade the coins that are onboard for a certain time period.

    Returns:
        sym_list (list): The list contains all the tradeable symbols.
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
        filename (str): Filename of the stored data.
    """
    
    # Get prices and store in DataFrame
    counts = 0
    price_history_dict = {}
    for sym in symbols:
        price_history = binance_get_recent_close_price(sym, interval=config.INTERVAL, limit=config.NUM_INTERVAL_LIMIT +config.SPREAD_WINDOW + config.Z_SCORE_WINDOW)
        if len(price_history) == config.NUM_INTERVAL_LIMIT + config.SPREAD_WINDOW + config.Z_SCORE_WINDOW: # make sure that each symbol has the same amount of data
            price_history_dict[sym] = price_history
            counts += 1
    logger.info (f"{counts} items stored, {len(symbols)-counts}items not stored")
    
    # Output prices to JSON
    if len(price_history_dict) > 0:
        filename = f"{config.INTERVAL}_price_list.json"
        with open(filename, "w") as fp:
            json.dump(price_history_dict, fp, indent=4)
        logger.info("Prices saved successfully.")

    # Return output
    return filename

def check_differnet_signal(a,b):
    """
    Check if the two values have different signs.

    Args:
        a, b: Numeric values to check for different signs.

    Returns:
        bool: True if the two values have different signs, False otherwise.
    """
    return abs(a + b) != abs(a) + abs(b)

def get_backtesting_properties(series_1: list, series_2: list, hedge_ratio: float, zscore_series: list):
    """
    Calculate backtesting properties for the given series and z-score values.

    Args:
        series_1 (list): Time series data for the first symbol.
        series_2 (list): Time series data for the second symbol.
        hedge_ratio (float): The hedge ratio between the two symbols.
        zscore_series (list): The z-score values.

    Returns:
        tuple: A tuple containing the following properties:
        - trade_oppotunities (int): Number of trade opportunities found during backtesting.
        - cumulative_return (float): Cumulative returns from all trades during backtesting.
        - win_rate (float): Win rate of trades during backtesting.
        - recent_trade_qty (float): Recent trade quantity based on investible capital and latest prices.
        - peak_loss (float): The minimum revenue observed during the trade.
    """
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
        if abs(value) >= abs(config.TRIGGER_Z_SCORE_THRESHOD) and not check_differnet_signal(value, last_value):
            
            enter_market_signal = True
            
            if value >= config.TRIGGER_Z_SCORE_THRESHOD:
                direction = "sell"
            elif value <= - config.TRIGGER_Z_SCORE_THRESHOD:
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

    

def calculate_pairs_trading_result(series_1, series_2, hedge_ratio: float, num_window: int) -> tuple:
    """
    Calculate pairs trading results for the given series and hedge ratio.

    Args:
        series_1 (list): Time series data for the first symbol.
        series_2 (list): Time series data for the second symbol.
        hedge_ratio (float): The hedge ratio between the two symbols.
        num_window (int): The window size for calculating spread and z-score.

    Returns:
        tuple: A tuple containing the following results:
        - trade_oppotunities (int): Number of trade opportunities found during backtesting.
        - cumulative_return (float): Cumulative returns from all trades during backtesting.
        - win_rate (float): Win rate of trades during backtesting.
        - recent_trade_qty (float): Recent trade quantity based on investible capital and latest prices.
        - recent_z_score (float): The z-score value of the most recent interval.
        - peak_loss (float): The minimum revenue observed during the trade.
        - std (float): Standard deviation of the spread.
    """
    spread = calculate_spread_static(series_1, series_2, hedge_ratio)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    std = calculate_std_spread(spread)
    
    # Get recent z score
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss = get_backtesting_properties(series_1, series_2, hedge_ratio, zscore_series)
        
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, recent_z_score, peak_loss, std

def get_trade_qty_each_time(symbol_1: str, symbol_2: str, hedge_ratio):
    """
    Calculate the estimated trade quantity for each symbol based on investible capital and latest prices.

    Args:
        symbol_1 (str): Symbol of the first asset.
        symbol_2 (str): Symbol of the second asset.
        hedge_ratio (float): The hedge ratio between the two symbols.

    Returns:
        tuple: A tuple containing the estimated trade quantity for each symbol:
        - estimated_trade_qty_symbol_1 (float): Estimated trade quantity for the first symbol.
        - estimated_trade_qty_symbol_2 (float): Estimated trade quantity for the second symbol.
    """
    estimated_trade_qty_symbol_1 = INVESTIBLE_CAPITAL_EACH_TIME / (binance_get_latest_price(symbol_1) + hedge_ratio * binance_get_latest_price(symbol_2))
    estimated_trade_qty_symbol_2 = (estimated_trade_qty_symbol_1 * hedge_ratio)
    
    return estimated_trade_qty_symbol_1, estimated_trade_qty_symbol_2
    
def get_cointegrated_pairs(prices, num_wave=0) -> str:
    """
    Find cointegrated pairs from the given prices and backtest them.

    Args:
        prices: Dictionary containing price series for different symbols.
        num_wave (int): Wave number for categorizing backtesting results.

    Returns:
        str: Filename of the stored backtesting results.
    """
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
            series_1_coint_test = series_1[- config.NUM_INTERVAL_LIMIT:]
            series_2_coint_test = series_2[- config.NUM_INTERVAL_LIMIT:]

            # Check for cointegration and add cointegrated pair
            coint_flag, p_value, hedge_ratio, initial_intercept = calculate_cointegration_static(series_1_coint_test, series_2_coint_test)
            

            
            if (coint_flag == 1) and (hedge_ratio > 0):
                series_1_train_test = series_1[-(config.NUM_INTERVAL_LIMIT + config.Z_SCORE_WINDOW):]
                series_2_train_test = series_2[-(config.NUM_INTERVAL_LIMIT + config.Z_SCORE_WINDOW):]
                trade_oppotunities, cumulative_returns, win_rate, recent_trade_qty, recent_z_score, peak_loss, std = calculate_pairs_trading_result(series_1_train_test,
                                                                                                                                              series_2_train_test,
                                                                                                                                              hedge_ratio,
                                                                                                                                              config.Z_SCORE_WINDOW)
                min_trading_qty_symbol_1 = binance_get_min_trading_qty(sym_1)
                min_trading_qty_symbol_2 = binance_get_min_trading_qty(sym_2)
                
                estimated_trade_qty_symbol_1, estimated_trade_qty_symbol_2 = get_trade_qty_each_time(sym_1, sym_2, hedge_ratio)
                
                symbol_1_current_price = binance_get_latest_price(sym_1)
                symbol_2_current_price = binance_get_latest_price(sym_2)
                
                estimated_trade_value_symbol_1 = estimated_trade_qty_symbol_1 * symbol_1_current_price
                estimated_trade_value_symbol_2 = estimated_trade_qty_symbol_2 * symbol_2_current_price
                
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
                    "trading_oppotunities": trade_oppotunities,
                    "estimated_returns": cumulative_returns,
                    "win_rate": win_rate,
                    "recent_trade_qty": recent_trade_qty,
                    "peak_loss": peak_loss,
                    "recent_z_score": recent_z_score,
                })

    # Output results and rank all the trading pairs
    df_coint = pd.DataFrame(coint_pair_list)
    filename = f"{num_wave}_static_backtesting_cointegrated_pairs.csv"

    # choose the positive estimated_returns
    df_coint = df_coint[df_coint["estimated_returns"] > 0]
    # export to csv
    df_coint.to_csv(filename)
    return df_coint

def choose_best_trading_pair_static(df_coint: pd.DataFrame) ->pd.DataFrame:
    """
    Choose the best trading pairs from the static backtesting results.

    Args:
        df_coint (pd.DataFrame): DataFrame containing static backtesting results.

    Returns:
        pd.DataFrame: DataFrame containing the best trading pairs based on defined criteria.
    """
    # filter out pairs based on min_trading_value
    df_coint = df_coint.loc[df_coint["estimated_trade_qty_symbol_1"] > df_coint["min_trading_qty_symbol_1"]]
    df_coint = df_coint.loc[df_coint["estimated_trade_qty_symbol_2"] > df_coint["min_trading_qty_symbol_2"]]
    df_coint = df_coint[df_coint["estimated_trade_value_symbol_1"] > 7]
    df_coint = df_coint[df_coint["estimated_trade_value_symbol_2"] > 7]
    
    # filter based on win rate
    # UPDATE: 3_2 no need to judge the win_rate
    # df_coint = df_coint[df_coint["win_rate"] >= WIN_RATE_THRESHOD]

    # filter the top 1/2 based on returns
    # UPDATE: 3_2 no need to judge the estimated_returns
    # df_coint = df_coint.sort_values("estimated_returns", ascending=False).head(int(df_coint.shape[0]/2) + 1)
    
    
    # filter out pairs have a high loss during the trade
    df_coint = df_coint[df_coint["peak_loss"] > -STOP_LOSS_VALUE]
    
    
    # rank them based on returns
    df_coint = df_coint.sort_values("estimated_returns", ascending=False)
    
    # return the pandaDataframe
    return df_coint

"""V2: Dynamic hedge-ratio backtesting"""

def get_backtesting_properties_dynamic(series_1: list, series_2: list, hedge_ratio_list: list, zscore_series: list):
    """
    Calculate backtesting properties for a dynamic hedge-ratio pairs trading strategy.

    Args:
        series_1 (list): Time series data for the first symbol.
        series_2 (list): Time series data for the second symbol.
        hedge_ratio_list (list): List of dynamic hedge ratios.
        zscore_series (list): Z-score series calculated from the spread of the two symbols.

    Returns:
        tuple: Trade opportunities, cumulative return, win rate, expected return, peak loss.
    """
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
        if abs(value) >= abs(config.TRIGGER_Z_SCORE_THRESHOD) and not check_differnet_signal(value, last_value):
            
            enter_market_signal = True
            
            if value >= config.TRIGGER_Z_SCORE_THRESHOD:
                direction = "sell"
            elif value <= -config.TRIGGER_Z_SCORE_THRESHOD:
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
    
    # Calculate the expected return
    recent_trade_qty = (INVESTIBLE_CAPITAL_EACH_TIME / (series_1[-1] + hedge_ratio_list[-1] * series_2[-1]))
    std = np.std(zscore_series)
    expected_return = std * recent_trade_qty * zscore_series[-1]
    
    return trade_oppotunities, cumulative_return, win_rate, expected_return, peak_loss, peak_profit

def get_cointegrated_pairs_dynamic(prices, df_coint_static, num_wave=0):
    """
    Find and analyze cointegrated pairs for dynamic hedge-ratio pairs trading strategy.

    Args:
        prices: Dictionary containing time series data for different symbols.
        df_coint_static (pd.DataFrame): DataFrame containing cointegration analysis results for static strategy.
        num_wave (int, optional): Wave number for labeling results.

    Returns:
        pd.DataFrame: DataFrame containing cointegration analysis results for dynamic strategy.
    """
    result_list = []

    # Loop through coins and check for co-integration
    sym_1_list = df_coint_static["sym_1"].values.tolist()
    sym_2_list = df_coint_static["sym_2"].values.tolist()
    
    for i in range(len(sym_1_list)):

        # Get close prices
        series_1 = prices[sym_1_list[i]]
        series_2 = prices[sym_2_list[i]]
        
        
        # Get recent prices for spread test, the length should be BACKTEST_INTERVAL + SPREAD_WINDOW + Z_SCORE_WINDOW
        series_1_spread_test = series_1[- (BACKTEST_INTERVAL + config.SPREAD_WINDOW + config.Z_SCORE_WINDOW):]
        series_2_spread_test = series_2[- (BACKTEST_INTERVAL + config.SPREAD_WINDOW + config.Z_SCORE_WINDOW):]
        
        # derive the dynamic_hedge_ratio_spread length is 2 * z_score_window + BACKTEST_INTERVAL
        spread_list, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1_spread_test, series_2_spread_test, config.SPREAD_WINDOW)
        
        # derive the dynamic_z_score list, length is z_score_window
        z_score_list = calculate_z_score_window(spread_list, config.Z_SCORE_WINDOW)
        z_score_list = z_score_list[-(BACKTEST_INTERVAL):]
        
        spread_list = spread_list[-(BACKTEST_INTERVAL):]
        hedge_ratio_list = hedge_ratio_list[-(BACKTEST_INTERVAL):]
        
        # Get recent prices for backtesting, the length should be equal to BACKTEST_INTERVAL
        series_1_backtest = series_1[ -(BACKTEST_INTERVAL):]
        series_2_backtest = series_2[ -(BACKTEST_INTERVAL):]
        
        # backtesting the result for 50 intervals
        trade_oppotunities, cumulative_return, win_rate, expected_return, peak_loss, peak_profit = get_backtesting_properties_dynamic(series_1_backtest, series_2_backtest, hedge_ratio_list, z_score_list)
            
        result_list.append({
            "sym_1": sym_1_list[i],
            "sym_2": sym_2_list[i],
            "expected_return": expected_return,
            "backtest_trading_oppotunities": trade_oppotunities,
            "backtest_returns": cumulative_return,
            "backtest_win_rate": win_rate,
            "backtest_peak_loss": peak_loss,
            "backtest_peak_profit": peak_profit,
            "recent_z_score": z_score_list[-1],
        })

    # Output results and rank all the trading pairs
    df_coint = pd.DataFrame(result_list)
    # export to csv
    filename = f"{num_wave}_dynamic_backtesting_cointegrated_pairs.csv"
    df_coint.to_csv(filename)
    # choose positive returns
    df_coint = df_coint[df_coint["backtest_returns"] > 0]
    df_coint.to_csv(filename)
    
    return df_coint

def choose_best_trading_pair_dynamic(df_coint: pd.DataFrame) ->pd.DataFrame:
    """
    Choose the best trading pair based on dynamic hedge-ratio pairs trading strategy.

    Args:
        df_coint (pd.DataFrame): DataFrame containing cointegration analysis results for dynamic strategy.

    Returns:
        tuple: True if a suitable trading pair is found, False otherwise. If True, also returns the symbols of the best trading pair.
    """
    # select positive returns
    df_coint = df_coint[df_coint["backtest_returns"] > 0]
    
    # select stable loss
    df_coint = df_coint[df_coint["backtest_peak_loss"] > -STOP_LOSS_VALUE]
    
    # select win rate
    df_coint = df_coint[df_coint["backtest_win_rate"] >= WIN_RATE_THRESHOD_DYNAMIC]
    
    # pick smallest 3/4 based on peak loss
    df_coint = df_coint.sort_values("backtest_peak_loss", ascending=True).head(int(df_coint.shape[0] * (3/4)) + 1)
    # pick top 3/4 based on win rate
    df_coint = df_coint.sort_values("backtest_win_rate", ascending=False).head(int(df_coint.shape[0] * (3/4)) + 1)
    # pick top 3/4 based on trade oppotunities
    df_coint = df_coint.sort_values("backtest_trading_oppotunities", ascending=False).head(int(df_coint.shape[0] * (3/4)) + 1)


    # choose the one with a tradeable z-score
    for i in range(df_coint.shape[0]):
        if abs(df_coint["recent_z_score"].values[i]) > config.TRIGGER_Z_SCORE_THRESHOD:
            symbol_1 = df_coint["sym_1"].values[i]
            symbol_2 = df_coint["sym_2"].values[i]
            return True, symbol_1, symbol_2
    
    return False, 0, 0

    
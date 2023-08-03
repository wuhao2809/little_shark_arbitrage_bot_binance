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


# Set config
SET_INTERVALS = ["5m", "15m", "30m", "1h"]

# SET_TRAINNING_PERIODS = [200, 300, 400, 500, 600, 800]
# SET_Z_SCORE_WINDOW = [20, 40, 60, 80, 120, 160, 200]
# SET_TRIGGER_Z_SCORE_THRESHOD = [0.8, 1.2, 1.6, 2.0]

SET_TRAINNING_PERIODS = [200, 300, 400, 600]
SET_Z_SCORE_WINDOW = [20, 40, 60, 80, 120, 160, 200]
SET_TRIGGER_Z_SCORE_THRESHOD = [0.8, 1.2, 1.6, 2.0]
TRADING_TIMES_THRESHOD = 5

ONBOARD_TIME_THRESHOD = datetime.datetime(2023, 1, 6)
TRADING_VOLUME_THRESHOD_RATE = 1 / 150

INVESTIBLE_CAPITAL_EACH_TIME = 400

TRADING_FEE_RATE = 0.0004

session_public = UMFutures()


def binance_get_24h_trading_volume_usdt(symbol: str) -> float:
    """get the 24h trading volume in usdt

    Args:
        symbol (str): symbol name

    Returns:
        float: the trading volume in usdt
    """
    return float(session_public.ticker_24hr_price_change(symbol)["quoteVolume"])


def binance_get_exchange_symbols():
    """get the exchange symbols from the binance

    Returns:
        _type_: a dict with all the symbols information in it
    
    See: https://binance-docs.github.io/apidocs/futures/en/#exchange-information
    """
    return session_public.exchange_info()["symbols"]

def transform_timestamp_to_datetime(timestamp: int):
    return datetime.datetime.fromtimestamp(int(timestamp)/1000)

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
    print(f"{count} pairs found")

    # return all the tradeable symbol and the size of the list
    return sym_list

def binance_get_recent_close_price(symbol: str, interval: str, limit: int) ->list:
    """get the recent close price list from binace with the related interval

    Args:
        symbol (_type_): the name of the symbol

    Returns:
        _type_: list
    """
    price_list = []
    prices = session_public.klines(symbol=symbol, interval=interval,limit = limit)
    for price in prices:
        price_list.append(float(price[4])) # change str to float
    if len(price_list) == limit:
        return price_list
    else: return

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
    print(f"{counts} items stored, {len(symbols)-counts}items not stored")
    
    # Output prices to JSON
    if len(price_history_dict) > 0:
        filename = f"{interval}_price_list.json"
        with open(filename, "w") as fp:
            json.dump(price_history_dict, fp, indent=4)
        print("Prices saved successfully.")
    time.sleep(5)

def binance_get_latest_price(symbol: str) -> float:
    """
    Retrieves the latest price for a given symbol from the Binance API.

    Args:
        symbol (str): The symbol for which to retrieve the latest price.

    Returns:
        float: The latest price for the specified symbol.
    """
    return float(session_public.ticker_price(symbol)["price"])

def get_trade_qty_each_time(symbol_1: str, symbol_2: str, hedge_ratio):
    estimated_trade_qty_symbol_1 = INVESTIBLE_CAPITAL_EACH_TIME / (binance_get_latest_price(symbol_1) + hedge_ratio * binance_get_latest_price(symbol_2))
    estimated_trade_qty_symbol_2 = (estimated_trade_qty_symbol_1 * hedge_ratio)
    
    return estimated_trade_qty_symbol_1, estimated_trade_qty_symbol_2


def calculate_cointegration_static(series_1, series_2):
    """
    Calculate the cointegration between two series and return cointegration flag,
    hedge ratio, and initial intercept.

    Args:
        series_1 (array like): First series for cointegration analysis.
        series_2 (array like): Second series for cointegration analysis.

    Returns:
        tuple: A tuple containing cointegration flag, hedge ratio, and initial intercept.

    Notes:
        - The series should have the same length.
        - Cointegration tests the long-term relationship between two time series.
        - The cointegration flag indicates if the two series are cointegrated.
        - The hedge ratio represents the relationship between the two series.
        - The initial intercept is the intercept of the linear regression model.

    Raises:
        ValueError: If the input series have different lengths.

    """
    
    coint_flag = 0
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]
    
    
    # get initial intercept and hedge_ration of the model
    series_2 = sm.add_constant(series_2)
    model = sm.OLS(series_1, series_2).fit()
    initial_intercept = model.params[0]
    hedge_ratio = model.params[1]

    if (p_value < 0.03) and (coint_t < critical_value):
        coint_flag = 1
    return coint_flag, p_value, hedge_ratio, initial_intercept


def calculate_spread_hedge_ratio_window(series_1: list, series_2: list, window: int):
    """
    Calculates the spread between two series using a given hedge ratio.

    Args:
        series_1 (list): A list of values representing the first series.
        series_2 (list): A list of values representing the second series.
        hedge_ratio (float): The hedge ratio to be applied.

    Returns:
        list: A list containing the calculated spread.
    """
    data_series_1 = pd.DataFrame(series_1)
    data_series_2 = pd.DataFrame(series_2)
    
    endog = data_series_1
    exog = sm.add_constant(data_series_2)
    rols = RollingOLS(endog, exog, window=window)
    rres = rols.fit()
    params = rres.params.replace(np.nan, 0)
    hedge_ratio = params.iloc[:, 1].tolist()
    
    spread = pd.Series(series_1) - (pd.Series(series_2) * hedge_ratio)
    spread[:window-1] = 0
    return spread.tolist(), hedge_ratio

def calculate_z_score_window(spread: list, window: int) -> list:
    """
    Calculates the Z-Score of a given spread.

    Args:
        spread (list): A list of values representing the spread.

    Returns:
        list: A list containing the Z-Score values.
    """
    data = pd.DataFrame(spread)
    rolling = data.rolling(window=window)
    m = rolling.mean()
    s = rolling.std()
    z_score = (data - m) / s
    
    # assign the first num of window z-score to be 0
    z_score[0][:(window-1)] = 0

    return z_score[0].tolist()



def calculate_std_spread(spread: list):
    """
    Calculates the std of a given spread.

    Args:
        spread (list): A list of values representing the spread.

    Returns:
        std: float
    """
    data = pd.DataFrame(spread)
    return data.std().values[0]

def check_differnet_signal(a,b):
    return abs(a + b) != abs(a) + abs(b)

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
    
    # Calculate the recent trade qty
    recent_trade_qty = (INVESTIBLE_CAPITAL_EACH_TIME / (series_1[-1] + hedge_ratio_list[-1] * series_2[-1]))
    
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss

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

def calculate_pairs_trading_result_dynamic(series_1, series_2, num_window: int, z_score_threshod: float) -> tuple:
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1, series_2, window=num_window)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    std = calculate_std_spread(spread)
    
    # Get recent z score
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss = get_backtesting_properties(series_1[-50:], series_2[-50:], hedge_ratio_list[-50:], zscore_series[-50:], z_score_threshod)
        
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, recent_z_score, peak_loss, std


def calculate_pairs_one_time_trading_result(series_1_real_test, series_2_real_test, z_score_window, z_score_threshod):
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1_real_test, series_2_real_test, window=z_score_window)
    zscore_series = calculate_z_score_window(spread, window=z_score_window)
    
    trade_oppotunities = 0
    last_value = 0.00
    enter_market_signal = False
    
    cumulative_return = 0
    cumulative_trading_qty = 0
    count_entering_time = 0
    
    open_long_price_list = []
    open_short_price_list = []
    
    peak_loss = 0
    
    
    for index, value in enumerate(zscore_series):
        if abs(value) >= abs(z_score_threshod) and not check_differnet_signal(value, last_value):
            
            enter_market_signal = True
            
            if value >= z_score_threshod:
                direction = "sell"
            elif value <= -z_score_threshod:
                direction = "buy"
            
            if count_entering_time < TRADING_TIMES_THRESHOD:
                cumulative_trading_qty += (INVESTIBLE_CAPITAL_EACH_TIME / (series_1_real_test[index] + hedge_ratio_list[index] * series_2_real_test[index]))  # qty for each symbol
                if direction == "buy":
                    open_long_price_list.append(series_1_real_test[index])
                    open_short_price_list.append(series_2_real_test[index])
                elif direction == "sell":
                    open_short_price_list.append(series_1_real_test[index])
                    open_long_price_list.append(series_2_real_test[index])
                    
                count_entering_time += 1

        # Calculate the peak loss during the trade
        if enter_market_signal:
            if direction == "buy":
                long_profit = (series_1_real_test[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty
                short_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_2_real_test[index]) * cumulative_trading_qty * hedge_ratio_list[index]
            elif direction == "sell":
                long_profit = (series_2_real_test[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty * hedge_ratio_list[index]
                short_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_1_real_test[index]) * cumulative_trading_qty
            current_revenue = long_profit + short_profit
            peak_loss = min(peak_loss, current_revenue)
        
        # Calculate the returns when exiting the market
        if enter_market_signal and check_differnet_signal(value, last_value):
            trade_oppotunities += 1
            exiting_profit = current_revenue - INVESTIBLE_CAPITAL_EACH_TIME * count_entering_time * TRADING_FEE_RATE # revenue for all symbols
            
            # Cumulate the return
            cumulative_return += exiting_profit
            return trade_oppotunities, cumulative_return, peak_loss
        
        last_value = value
    
    return trade_oppotunities, cumulative_return, peak_loss
def calculate_spread_static(series_1: list, series_2: list, hedge_ratio):
    """
    Calculates the spread between two series using a given hedge ratio.

    Args:
        series_1 (list): A list of values representing the first series.
        series_2 (list): A list of values representing the second series.
        hedge_ratio (float): The hedge ratio to be applied.

    Returns:
        list: A list containing the calculated spread.
    """
    
    spread = pd.Series(series_1) - (pd.Series(series_2) * hedge_ratio)
    return spread.tolist()


def calculate_pairs_trading_result_static(series_1, series_2, hedge_ratio: float, num_window: int, z_score_threshod) -> tuple:
    
    spread = calculate_spread_static(series_1, series_2, hedge_ratio)
    zscore_series = calculate_z_score_window(spread, window=num_window)
    std = calculate_std_spread(spread)
    
    # Get recent z score
    recent_z_score = zscore_series[-1]
    
    trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss = get_backtesting_properties_static(series_1, series_2, hedge_ratio, zscore_series,z_score_threshod)
        
    return trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, recent_z_score, peak_loss, std
    
def get_cointegrated_pairs(prices, interval, trainning_period, z_score_window, z_score_threshod) -> str:

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
                if cumulative_returns > 0 and win_rate > 0.8 and abs(peak_loss) < 100:
                    series_1_real_test = series_1[-(50 + 3 * z_score_window):]
                    series_2_real_test = series_2[-(50 + 3 * z_score_window):]
                    
                    trade_oppotunities_performance, cumulative_returns_performance, win_rate_performance, _, _, peak_loss_performace, _ = calculate_pairs_trading_result_dynamic(series_1_real_test,
                                                                                                                                                series_2_real_test,
                                                                                                                                                z_score_window,
                                                                                                                                                z_score_threshod)
                    
                    series_1_examine_test = prices[sym_1][-(50 + 3 * z_score_window):]
                    series_2_examine_test = prices[sym_2][-(50 + 3 * z_score_window):]
                    examine_trade_oppotunities, examine_returns, examine_win_rate, _, _, examine_peak_loss, _ = calculate_pairs_trading_result_dynamic(series_1_examine_test, series_2_examine_test, z_score_window, z_score_threshod)
                    
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
                        "examine_peak_loss": examine_peak_loss,
                    })

    # Output results and rank all the trading pairs
    df_coint = pd.DataFrame(coint_pair_list)
    # add the total score column
    df_coint = df_coint.sort_values("examine_returns", ascending=False)
    filename = f"{interval}_{trainning_period}_{z_score_window}_{z_score_threshod}_cointegrated_pairs.csv"
    # choose positive hedge ratio
    df_coint = df_coint[df_coint["hedge_ratio"] > 0]
    df_coint.to_csv(filename)
    
    print(f"{interval}_{trainning_period}_{z_score_window}_cointegrated_pairs.csv has been completed")
    return df_coint


def test_parameters(interval, trainning_period, z_score_window, z_score_threshod):
    with open (f"{interval}_price_list.json") as json_file:
        price_data = json.load(json_file)
        df_coint = get_cointegrated_pairs(price_data, interval, trainning_period, z_score_window, z_score_threshod)
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



def main():
    tradeable_symbols = get_tradeable_symbols_dynamic()
    for interval in SET_INTERVALS:
        store_price_history_static(tradeable_symbols, interval)
    print("price saved")
    
    result_list = []
    
    for interval in SET_INTERVALS:
        for trainning_period in SET_TRAINNING_PERIODS:
            for z_score_window in SET_Z_SCORE_WINDOW:
                for z_score_threshod in SET_TRIGGER_Z_SCORE_THRESHOD:
                    df_coint = test_parameters(interval, trainning_period, z_score_window, z_score_threshod)
                    average_return, win_rate, average_loss, tradeable_num, selected_pairs_pd = get_trainning_result(df_coint)
                    
                    # print(average_return, win_rate, average_loss, tradeable_num)
                    temp_dict = {"interval":interval, "trainning_period": trainning_period, "z_score_window": z_score_window,
                                "z_score_threshod": z_score_threshod, "test_average_returns": average_return, "test_win_rate":win_rate,
                                "test_ave_loss": average_loss, "tradeable_num": tradeable_num}
                    selected_pairs_pd.to_csv(f"{interval}_{trainning_period}_{z_score_window}_{z_score_threshod}_selected_pairs.csv")
                    result_list.append(temp_dict)
                    df_result = pd.DataFrame(result_list)
                    df_result.to_csv("analysis.csv")

if __name__ == "__main__":
    main()


from experiment_config import trigger_z_score_threshod, trading_times_threshod, investable_capital_each_time, estimated_trading_fee_rate
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import scipy.stats as stats
import pandas as pd
import numpy as np
import time

pd.set_option("display.precision", 15)

# Calculate Z-Score
def calculate_zscore_static(spread: list) -> list:
    """
    Calculates the Z-Score of a given spread.

    Args:
        spread (list): A list of values representing the spread.

    Returns:
        list: A list containing the Z-Score values.
    """
    data = np.array(spread)
    return stats.zscore(data)


# Calculate spread
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


# Calculate co-integration
def calculate_cointegration_static(series_1, series_2):
    """
    Calculate the cointegration between two series and return cointegration flag,
    hedge ratio, and initial intercept.

    Args:
        series_1 (np.ndarray): First series for cointegration analysis.
        series_2 (np.ndarray): Second series for cointegration analysis.

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

    if p_value < 0.5 and coint_t < critical_value:
        coint_flag = 1
    return coint_flag, p_value, hedge_ratio, initial_intercept


def check_differnet_signal(a,b):
    return a + b != abs(a) + abs(b)

def calculate_trading_estimated_oppotunities_return(series_1, series_2, hedge_ratio: float, initial_intercept: float, threshod: float) -> int:
    enter_market_signal = False
    spread = calculate_spread_static(series_1, series_2, hedge_ratio)
    
    zscore_series = calculate_zscore_static(spread)
    
    trade_oppotunities = 0
    last_value = 0.01
    
    cumulative_return = 0
    cumulative_trading_qty = 0
    count_entering_time = 0
    
    open_long_price_list = []
    open_short_price_list = []
    
    for index, value in enumerate(zscore_series):
        if abs(value) >= abs(threshod) and not check_differnet_signal(value, last_value):
            enter_market_signal = True
            
            if value >= threshod:
                direction = "sell"
            elif value <= -threshod:
                direction = "buy"
            
            if count_entering_time < trading_times_threshod:
                cumulative_trading_qty += (investable_capital_each_time / (series_1[index] + hedge_ratio * series_2[index]))  # qty for each symbol
                if direction == "buy":
                    open_long_price_list.append(series_1[index])
                    open_short_price_list.append(series_2[index])
                elif direction == "sell":
                    open_short_price_list.append(series_1[index])
                    open_long_price_list.append(series_2[index])
                    
                count_entering_time += 1
                
        elif enter_market_signal and check_differnet_signal(value, last_value):
            trade_oppotunities += 1
            
            # calculate the exiting_revenue of the symbols
            if direction == "buy":
                buy_side_profit = (series_1[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty
                sell_side_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_2[index]) * cumulative_trading_qty
            elif direction == "sell":
                buy_side_profit = (series_2[index] - sum(open_long_price_list)/len(open_long_price_list)) * cumulative_trading_qty
                sell_side_profit = (sum(open_short_price_list)/len(open_short_price_list) - series_1[index]) * cumulative_trading_qty
                
            exiting_profit = buy_side_profit + sell_side_profit - investable_capital_each_time * count_entering_time * estimated_trading_fee_rate # revenue for all symbols

            
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

        
    return trade_oppotunities, cumulative_return
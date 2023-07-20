from config import TRIGGER_Z_SCORE_THRESHOD, TRADING_TIMES_THRESHOD, INVESTIBLE_CAPITAL_EACH_TIME, TRADING_FEE_RATE, INTERVAL, NUM_INTERVAL_LIMIT
from statsmodels.tsa.stattools import coint
from binance_market_observer import binance_get_recent_close_price
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

# test


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

# a= [1,2,3,4,5]
# print(calculate_std_spread(a))

# Calculate co-integration
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

# Calculate co-integration
def check_cointegration_quick(symbol_1: str, symbol_2: str):
    """
    Calculate the cointegration between two series and return cointegration flag,
    hedge ratio, and initial intercept.

    Args:
        series_1 (array like): First series for cointegration analysis.
        series_2 (array like): Second series for cointegration analysis.

    Returns:
        True or False

    Notes:
        - The series should have the same length.
        - Cointegration tests the long-term relationship between two time series.
        - The cointegration flag indicates if the two series are cointegrated.

    Raises:
        ValueError: If the input series have different lengths.

    """
    series_1 = binance_get_recent_close_price(symbol_1, INTERVAL, NUM_INTERVAL_LIMIT)
    series_2 = binance_get_recent_close_price(symbol_2, INTERVAL, NUM_INTERVAL_LIMIT)
    
    
    coint_flag = 0
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]
    if p_value < 0.05: # Don't need to be that strict for check during execution, and coint_t < critical_value:
        return True
    
    return False

# print(check_cointegration_quick("NEARUSDT", "1000SHIBUSDT"))
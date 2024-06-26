from config import config
from statsmodels.tsa.stattools import coint
from binance_market_observer import binance_get_recent_close_price
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS
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
    Calculates the Z-Score of a given spread using a rolling window.

    Args:
        spread (list): A list of values representing the spread.
        window (int): The size of the rolling window.

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
    
    z_score_list = z_score[0].tolist()

    return z_score_list[window-1:]

# test
# random_normal = np.random.normal(0, 0.1, 100)
# print(len(calculate_z_score_window(random_normal, 50)))

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
    p-value, hedge ratio, and initial intercept.

    Args:
        series_1 (array like): First series for cointegration analysis.
        series_2 (array like): Second series for cointegration analysis.

    Returns:
        tuple: A tuple containing cointegration flag, p-value, hedge ratio, and initial intercept.

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
    Check if two trading pairs have cointegration.

    Args:
        symbol_1 (str): The first trading pair symbol.
        symbol_2 (str): The second trading pair symbol.

    Returns:
        bool: True if cointegrated, False otherwise.
    """
    series_1 = binance_get_recent_close_price(symbol_1, config.INTERVAL, config.NUM_INTERVAL_LIMIT)
    series_2 = binance_get_recent_close_price(symbol_2, config.INTERVAL, config.NUM_INTERVAL_LIMIT)
    
    
    coint_flag = 0
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]
    if p_value < 0.05: # Don't need to be that strict for check during execution, and coint_t < critical_value:
        return True
    
    return False

# print(check_cointegration_quick("NEARUSDT", "1000SHIBUSDT"))

def calculate_spread_hedge_ratio_window(series_1: list, series_2: list, window: int):
    """
    Calculates the spread between two series using a rolling hedge ratio.

    Args:
        series_1 (list): A list of values representing the first series.
        series_2 (list): A list of values representing the second series.
        window (int): The rolling window size for the calculation.

    Returns:
        tuple: A tuple containing two elements:
            - A list containing the calculated spread.
            - A list containing the calculated rolling hedge ratios for each window.
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
    return spread.tolist()[window-1:], hedge_ratio[window-1:]
# test
# a = np.random.normal(0.1,0.1, 50)
# b = np.random.normal(2,0.1, 50)
# window = 3
# print(len(calculate_spread_hedge_ratio_window(a,b,window)[1]))
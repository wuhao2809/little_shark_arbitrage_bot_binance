# # from config import api_key, api_secret
# # import time
# # import logging
# # from binance.um_futures import UMFutures
# # from binance.cm_futures import CMFutures
# # from binance.lib.utils import config_logging


# # from time_binance import transform_timestamp_to_datetime, get_current_time_timestamp_binance

# # # um_futures_client = UMFutures()
# # # print(um_futures_client.time())


# # # Get account information

# # um_futures_client = UMFutures()

# # # config_logging(logging, logging.DEBUG)

# # # get server time
# # # print(transform_timestamp_to_datetime(um_futures_client.time()["serverTime"]))

# # def find_symbols_binance():
# #     symbol_list = []
# #     symbols = um_futures_client.exchange_info()["symbols"]
# #     for symbol in symbols:
# #         if symbol["status"] == "TRADING" and symbol["quoteAsset"] == "USDT" and symbol["contractType"] == "PERPETUAL":
# #             symbol_list.append(symbol["symbol"])
# #             # symbol_list.append(symbol["onboardDate"])
# #     return len(symbol_list)

# # def get_499_price_15m():
# #     return len(um_futures_client.klines("BTCUSDT", "15m",limit = 499))

# # """Note: binance get price from the past to present, meaning that [-1] should be the current time"""
# # # print(find_symbols_binance())
# # # print(find_symbols_binance())
# # # print(get_499_price_15m())
# # # print(transform_timestamp_to_datetime(1688481899999))
# # # print(um_futures_client.exchange_info()["symbols"])
# # print(um_futures_client.ticker_24hr_price_change("BTCUSDT"))
# # print(transform_timestamp_to_datetime(1688934509786))
    
# from func_get_traget_symbols import get_backtesting_properties, calculate_z_score_window, calculate_spread_static
# import json
# with open("15m_price_list.json", "r")as price_data:
#     data = json.load(price_data)
#     price_symbol_1 = data["XLMUSDT"]
#     price_symbol_2 = data["LDOUSDT"]
# hedge_ratio = 0.007635503
# spread = calculate_spread_static(price_symbol_1, price_symbol_2, hedge_ratio)
# zscore_series = calculate_z_score_window(spread, window=46)
# trade_oppotunities, cumulative_return, win_rate, recent_trade_qty, peak_loss = get_backtesting_properties(price_symbol_1, price_symbol_2, hedge_ratio, zscore_series)
# print(trade_oppotunities)

import pykalman
import numpy as np
kf = pykalman.KalmanFilter(transition_matrices = [[1, 1], [0, 1]], observation_matrices = [[0.1, 0.5], [-0.3, 0.0]])
measurements = np.asarray([[1,0], [0,0], [0,1]])  # 3 observations
(filtered_state_means, filtered_state_covariances) = kf.filter(measurements)
print (filtered_state_means)
from binance.um_futures import UMFutures
import datetime
import json

# set the mode
##### IMPORTANT!!!!!!!!!!!
##### ARE YOU SURE YOU ARE GOING TO TRADE?
##### CHECK LEVERAGE
mode = "real"


# API KEY REAL
api_key = "6URzPphTVbT0xY7yb9OhC0dF76Vv5vZu5iHpKENqYj3W7QC5aRe1wXE5ojlQ24qw"
api_secret = "ZqIaRfDuTEOzzamBoxup5VfvpW1fjhxd0WRSha5oWmQnn1kVPx9CPHj9uUqf0uMn"

# API KEY TEST
api_key_test = "299b33afbbab635571177ca956140c233e5a940477aeca80349ca9bb544c4ee4"
api_secret_test = "6252e61aa79693e57e65cd1fced6eba5c980659dbcf0e97d79fe095ced7089e6"

# USD M Client
session_public = UMFutures()
if mode == "real":
    session_private = UMFutures(key = api_key, secret= api_secret)
    session_public = UMFutures()

    # Overall configurations
    # INTERVAL = "15m" # 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
    

    LEVERAGE = 6
    # NUM_INTERVAL_LIMIT = 200
    # TRIGGER_Z_SCORE_THRESHOD = 1.6

    TRADING_TIMES_THRESHOD = 8
    
    class Config:
        def __init__(self):
            self._load_parameters()

        def _load_parameters(self):
            with open("parameters.json") as json_file:
                parameters_data = json.load(json_file)
                self._parameters_data = parameters_data
                self._INTERVAL_INT = int(parameters_data["interval"][:-1])

        @property
        def NUM_INTERVAL_LIMIT(self):
            self._load_parameters()
            return self._parameters_data["trainning_period"]

        @property
        def SPREAD_WINDOW(self):
            self._load_parameters()
            return self._parameters_data["spread_window"]

        @property
        def Z_SCORE_WINDOW(self):
            self._load_parameters()
            return self._parameters_data["z_score_window"]

        @property
        def TRIGGER_Z_SCORE_THRESHOD(self):
            self._load_parameters()
            return self._parameters_data["z_score_threshod"]

        @property
        def ACCOUNT_BALANCE_INVESTABLE(self):
            self._load_parameters()
            return int(self._parameters_data["current_balance"]) * 0.9

        @property
        def INTERVAL(self):
            self._load_parameters()
            return self._parameters_data["interval"]

        @property
        def INTERVAL_INT(self):
            self._load_parameters()
            return self._INTERVAL_INT

    config = Config()
    
    # ACCOUNT_BALANCE_INVESTABLE = 500
    TOTAL_INVESTABLE_VALUE = config.ACCOUNT_BALANCE_INVESTABLE * LEVERAGE * 0.8
    INVESTIBLE_CAPITAL_EACH_TIME = TOTAL_INVESTABLE_VALUE / TRADING_TIMES_THRESHOD

    WAVE_LIMIT = 3

    # SPREAD_WINDOW = 20
    # Z_SCORE_WINDOW = 120

    """Configurations in Process"""

    # threshod for get target symbols
    ONBOARD_TIME_THRESHOD = datetime.datetime(2023, 1, 6) # the coins being traded should not be onboard later than this date

    TRADING_VOLUME_THRESHOD_RATE = (1 / 150) # trading volume threshod, representeed as percentage of BTCUSDT 24h trading volume in USDT

    WAIT_SEARCH_BEST_PAIR = 300
    TIMES_SEARCH_BEST_PAIR = 5
    
    WIN_RATE_THRESHOD = 0.70
    WIN_RATE_THRESHOD_DYNAMIC = 0.7
    
    TRADING_FEE_RATE = 0.0004
    EXTREME_VALUE_MEAN_RATE_THRESHOD = 15
    
    BACKTEST_INTERVAL = 50

    # threshod for trading
    TRADING_TIME_LIMIT_INTERVALS = 50

    TAKE_PROFIT_RATIO = 0.015 * LEVERAGE
    STOP_LOSS_RATIO = 0.02 * LEVERAGE

    TAKE_PROFIT_VALUE = TAKE_PROFIT_RATIO * config.ACCOUNT_BALANCE_INVESTABLE 
    STOP_LOSS_VALUE = STOP_LOSS_RATIO * config.ACCOUNT_BALANCE_INVESTABLE 

    INVESTED_VALUE_BIAS_RATIO = 0.90

    WAITING_INTERVAL = int(config.INTERVAL_INT * 10) + 1 # seconds to wait for the z-score cross the zero line
    
    NOT_INVESTING_TRADING_INTERVAL_LIMIT = 4 # The maximum number of intervals for the program to wait to have a trading oppotunities

    SECONDS_WAIT_LIMIT_CLOSE = 60 # seconds to wait for the closing limit order
    SECONDS_WAIT_MARKET_CLOSE = 30 # seconds to wait for the closing market order

    SECONDS_WAIT_LIMIT_OPEN = 60 # seconds to wait for the opening limit order
    SECONDS_WAIT_MARKET_OPEN = 30 # seconds to wait for the opening limit order

# print(INTERVAL_INT)
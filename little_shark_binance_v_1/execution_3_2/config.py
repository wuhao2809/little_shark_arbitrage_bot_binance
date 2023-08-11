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

if mode == "test":
    session_private = UMFutures(key = api_key_test, secret= api_secret_test, base_url="https://testnet.binancefuture.com")
    session_public = UMFutures(base_url="https://testnet.binancefuture.com")

# Overall configurations
    INTERVAL = "30m" # 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
    INTERVAL_INT = 30

    LEVERAGE = 2
    NUM_INTERVAL_LIMIT = 300
    TRIGGER_Z_SCORE_THRESHOD = 1.6

    TRADING_TIMES_THRESHOD = 5
    
    ACCOUNT_BALANCE_INVESTABLE = 400
    TOTAL_INVESTABLE_VALUE = ACCOUNT_BALANCE_INVESTABLE * LEVERAGE * 0.9
    INVESTIBLE_CAPITAL_EACH_TIME = TOTAL_INVESTABLE_VALUE / TRADING_TIMES_THRESHOD

    WAVE_LIMIT = 5

    Z_SCORE_WINDOW = 40

    """Configurations in Process"""

    # threshod for get target symbols
    ONBOARD_TIME_THRESHOD = datetime.datetime(2023, 1, 6) # the coins being traded should not be onboard later than this date

    TRADING_VOLUME_THRESHOD_RATE = (1 / 200) # trading volume threshod, representeed as percentage of BTCUSDT 24h trading volume in USDT

    WAIT_SEARCH_BEST_PAIR = 60
    
    WIN_RATE_THRESHOD = 0.88
    TRADING_FEE_RATE = 0.0004
    EXTREME_VALUE_MEAN_RATE_THRESHOD = 15
    
    BACKTEST_INTERVAL = 50

    # threshod for trading
    TRADING_TIME_LIMIT_INTERVALS = 50

    TAKE_PROFIT_RATIO = 0.01 * LEVERAGE
    STOP_LOSS_RATIO = 0.03 * LEVERAGE

    TAKE_PROFIT_VALUE = TAKE_PROFIT_RATIO * TOTAL_INVESTABLE_VALUE
    STOP_LOSS_VALUE = STOP_LOSS_RATIO * TOTAL_INVESTABLE_VALUE

    INVESTED_VALUE_BIAS_RATIO = 0.90

    WAITING_INTERVAL = 301 # seconds to wait for the z-score cross the zero line

    SECONDS_WAIT_LIMIT_CLOSE = 60 # seconds to wait for the closing limit order
    SECONDS_WAIT_MARKET_CLOSE = 30 # seconds to wait for the closing market order

    SECONDS_WAIT_LIMIT_OPEN = 60 # seconds to wait for the opening limit order
    SECONDS_WAIT_MARKET_OPEN = 30 # seconds to wait for the opening limit order

  
elif mode == "real":
    session_private = UMFutures(key = api_key, secret= api_secret)
    session_public = UMFutures()

    # Overall configurations
    # INTERVAL = "15m" # 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
    

    LEVERAGE = 5
    # NUM_INTERVAL_LIMIT = 200
    # TRIGGER_Z_SCORE_THRESHOD = 1.6

    TRADING_TIMES_THRESHOD = 8
    
    with open ("parameters.json") as json_file:
        parameters_data = json.load(json_file)
        NUM_INTERVAL_LIMIT = parameters_data["trainning_period"]
        SPREAD_WINDOW = parameters_data["spread_window"]
        Z_SCORE_WINDOW = parameters_data["z_score_window"]
        TRIGGER_Z_SCORE_THRESHOD = parameters_data["z_score_threshod"]
        ACCOUNT_BALANCE_INVESTABLE = int(parameters_data["current_balance"]) * 0.9
        INTERVAL = parameters_data["interval"]
    
    if INTERVAL[-1] == "m":
        INTERVAL_INT = int(INTERVAL[:-1])
    elif INTERVAL[-1] == "h":
        INTERVAL_INT = int(INTERVAL[:-1]) * 60
    elif INTERVAL[-1] == "d":
        INTERVAL_INT = int(INTERVAL[:-1]) * 60 * 24
    
    # ACCOUNT_BALANCE_INVESTABLE = 500
    TOTAL_INVESTABLE_VALUE = ACCOUNT_BALANCE_INVESTABLE * LEVERAGE * 0.9
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
    STOP_LOSS_RATIO = 0.03 * LEVERAGE

    TAKE_PROFIT_VALUE = TAKE_PROFIT_RATIO * ACCOUNT_BALANCE_INVESTABLE
    STOP_LOSS_VALUE = STOP_LOSS_RATIO * ACCOUNT_BALANCE_INVESTABLE

    INVESTED_VALUE_BIAS_RATIO = 0.90

    WAITING_INTERVAL = int(INTERVAL_INT * 10) + 1 # seconds to wait for the z-score cross the zero line
    
    NOT_INVESTING_TRADING_INTERVAL_LIMIT = 4 # The maximum number of intervals for the program to wait to have a trading oppotunities

    SECONDS_WAIT_LIMIT_CLOSE = 60 # seconds to wait for the closing limit order
    SECONDS_WAIT_MARKET_CLOSE = 30 # seconds to wait for the closing market order

    SECONDS_WAIT_LIMIT_OPEN = 60 # seconds to wait for the opening limit order
    SECONDS_WAIT_MARKET_OPEN = 30 # seconds to wait for the opening limit order
from binance.um_futures import UMFutures
import datetime


# API KEY REAL
api_key = "6URzPphTVbT0xY7yb9OhC0dF76Vv5vZu5iHpKENqYj3W7QC5aRe1wXE5ojlQ24qw"
api_secret = "ZqIaRfDuTEOzzamBoxup5VfvpW1fjhxd0WRSha5oWmQnn1kVPx9CPHj9uUqf0uMn"

# USD M Client
session_public = UMFutures()
session_private = UMFutures(key = api_key, secret= api_secret)

# Overall configurations
interval = "15m" # 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
num_interval_limit = 350 + 100 + 46
trigger_z_score_threshod = 0.8
trading_times_threshod = 5
investable_capital_each_time = 100

"""Configurations in Process"""

# threshod for get target symbols
onboard_time_threshod = datetime.datetime(2023, 1, 6) # the coins being traded should not be onboard later than this date
trading_volume_threshod = 1 / 200 # trading volume threshod, representeed as percentage of BTCUSDT 24h trading volume in USDT

# chosing target symbols
estimated_trading_fee_rate = 0.0004

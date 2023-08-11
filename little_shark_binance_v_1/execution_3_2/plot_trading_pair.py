from func_calculation_static import calculate_cointegration_static, calculate_spread_static, calculate_z_score_window, calculate_spread_hedge_ratio_window
from binance_market_observer import binance_get_recent_close_price
import pandas as pd
from config import TRIGGER_Z_SCORE_THRESHOD, Z_SCORE_WINDOW, INTERVAL, TRADING_TIME_LIMIT_INTERVALS, BACKTEST_INTERVAL, SPREAD_WINDOW, NUM_INTERVAL_LIMIT
import matplotlib.pyplot as plt
import json

def plot_reference(sym_1, sym_2, num_wave=0):
    """
    Plot the price, spread, and Z-score of two given symbols against each other.

    Parameters:
        sym_1 (str): The first trading symbol.
        sym_2 (str): The second trading symbol.
        num_wave (int, optional): The number of waves (used for saving the graph with a unique name). Default is 0.
    """
    with open(f"{INTERVAL}_price_list.json", "r")as price_data:
        data = json.load(price_data)
        price_symbol_1 = data[sym_1]
        price_symbol_2 = data[sym_2]
    
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(price_symbol_1, price_symbol_2, SPREAD_WINDOW)
    z_score = calculate_z_score_window(spread, Z_SCORE_WINDOW)
    
    # Make the starting point of the graph SPREAD_WINDOW + Z_SCORE_WINDOW
    price_symbol_1 = price_symbol_1[-NUM_INTERVAL_LIMIT:]
    price_symbol_2 = price_symbol_2[-NUM_INTERVAL_LIMIT:]
    
    spread = spread[-NUM_INTERVAL_LIMIT:]
    z_score = z_score[-NUM_INTERVAL_LIMIT:]
    
    # Calculate percentage changes
    df = pd.DataFrame(columns=[sym_1, sym_2])
    df[sym_1] = price_symbol_1
    df[sym_2] = price_symbol_2
    df[f"{sym_1}_pct"] = df[sym_1] / price_symbol_1[0]
    df[f"{sym_2}_pct"] = df[sym_2] / price_symbol_2[0]
    series_1 = df[f"{sym_1}_pct"].astype(float).values
    series_2 = df[f"{sym_2}_pct"].astype(float).values
    
    fig, axs = plt.subplots(3, figsize = (16, 8))
    fig.suptitle(f"Price, Spread and Z_score - {sym_1} vs {sym_2}")
    axs[0].plot(series_1, label = f"{sym_1}")
    axs[0].plot(series_2, label = f"{sym_2}")
    axs[0].title.set_text("Price percentage change")
    axs[0].legend()
    axs[1].plot(spread)
    axs[1].title.set_text("Spread")
    axs[2].plot(z_score)
    axs[2].axhline(y=TRIGGER_Z_SCORE_THRESHOD, color='r', linestyle='dotted')
    axs[2].axhline(y=-TRIGGER_Z_SCORE_THRESHOD, color='r', linestyle='dotted')
    axs[2].axhline(y=0, color='g', linestyle='-')
    axs[2].title.set_text("Z score")
    plt.savefig(f"{num_wave}_wave_trading_pair_history_graph.png")

# plot_reference("FILUSDT", "CRVUSDT")
# with open("15m_price_list.json", "r")as price_data:
#     print(price_data["BTCUSDT"])


def plot_reference_trading(symbol_1, symbol_2, num_wave=0):
    """
    Plot the price, spread, and Z-score of two given symbols against each other for trading data.

    Parameters:
        symbol_1 (str): The first trading symbol.
        symbol_2 (str): The second trading symbol.
        num_wave (int, optional): The number of waves (used for saving the graph with a unique name). Default is 0.
    """
    price_symbol_1 = binance_get_recent_close_price(symbol_1, INTERVAL, SPREAD_WINDOW + Z_SCORE_WINDOW + BACKTEST_INTERVAL)
    price_symbol_2 = binance_get_recent_close_price(symbol_2, INTERVAL, SPREAD_WINDOW + Z_SCORE_WINDOW + BACKTEST_INTERVAL)
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(price_symbol_1, price_symbol_2, SPREAD_WINDOW)
    z_score = calculate_z_score_window(spread, Z_SCORE_WINDOW)
    
    spread = spread[-BACKTEST_INTERVAL:]
    z_score = z_score[-BACKTEST_INTERVAL:]
    price_symbol_1 = price_symbol_1[-BACKTEST_INTERVAL:]
    price_symbol_2 = price_symbol_2[-BACKTEST_INTERVAL:]
    
    # Calculate percentage changes
    df = pd.DataFrame(columns=[symbol_1, symbol_2])
    df[symbol_1] = price_symbol_1
    df[symbol_2] = price_symbol_2
    df[f"{symbol_1}_pct"] = df[symbol_1] / price_symbol_1[0]
    df[f"{symbol_2}_pct"] = df[symbol_2] / price_symbol_2[0]
    series_1 = df[f"{symbol_1}_pct"].astype(float).values
    series_2 = df[f"{symbol_2}_pct"].astype(float).values
    
    fig, axs = plt.subplots(3, figsize = (16, 8))
    fig.suptitle(f"Price, Spread and Z_score - {symbol_1} vs {symbol_2}")
    axs[0].plot(series_1, label = f"{symbol_1}")
    axs[0].plot(series_2, label = f"{symbol_2}")
    axs[0].title.set_text("Price percentage change")
    axs[0].legend()
    axs[1].plot(spread)
    axs[1].title.set_text("Spread")
    axs[2].plot(z_score)
    axs[2].axhline(y=TRIGGER_Z_SCORE_THRESHOD, color='r', linestyle='dotted')
    axs[2].axhline(y=-TRIGGER_Z_SCORE_THRESHOD, color='r', linestyle='dotted')
    axs[2].axhline(y=0, color='g', linestyle='-')
    axs[2].title.set_text("Z score")
    plt.savefig(f"{num_wave}_wave_trading_pair_trading_graph.png")

# plot_reference_trading("FILUSDT", "CRVUSDT", num_wave=0)
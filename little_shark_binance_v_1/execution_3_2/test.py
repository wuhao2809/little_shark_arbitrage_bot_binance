import json
import numpy as np
from filterpy.kalman import KalmanFilter

with open("15m_price_list.json", "r")as price_data:
        data = json.load(price_data)
        price_symbol_1 = data["FILUSDT"]
        price_symbol_2 = data["CRVUSDT"]

import numpy as np
from filterpy.kalman import KalmanFilter

def calculate_spread_hedge_ratio_kalman(series_1: list, series_2: list, window: int):
    """
    Calculates the spread between two series using a Kalman filter for hedge ratio estimation.
    
    Args:
        series_1 (list): A list of values representing the first series.
        series_2 (list): A list of values representing the second series.
        window (int): The rolling window size for the calculation.
        
    Returns:
        tuple: A tuple containing two elements:
            - A list containing the calculated spread.
            - A list containing the calculated rolling hedge ratios for each window.
    """
    spread = []
    hedge_ratios = []
    
    for i in range(window, len(series_1) + 1):
        obs = np.array([series_1[i - window: i], series_2[i - window: i]])
        
        kf = KalmanFilter(dim_x=2, dim_z=2)
        
        kf.F = np.array([[1, 1],
                         [0, 1]])
        kf.H = np.array([[0.1, 0.5],
                         [-0.3, 0.0]])
        
        kf.P *= 1e6  # set initial state covariance
        
        # Process noise covariance matrix Q
        kf.Q = np.eye(2) * 0.13
        
        # Measurement noise covariance matrix R
        kf.R = np.eye(2)
        
        # Initial state
        kf.x = np.array([0, 0])
        
        # Perform Kalman filter prediction and update
        kf.predict()
        kf.update(obs)
        
        # Extract the hedge ratio from the state estimate
        hedge_ratio = kf.x[0] / kf.x[1]
        hedge_ratios.append(hedge_ratio)
        
        # Calculate the spread using the estimated hedge ratio
        spread_value = series_1[i - 1] - hedge_ratio * series_2[i - 1]
        spread.append(spread_value)
    
    return spread, hedge_ratios



spread, hedge_ratios = calculate_spread_hedge_ratio_kalman(price_symbol_1, price_symbol_2,40)
print(hedge_ratios)

# def plot_reference(sym_1, sym_2, num_wave=0):
#     """
#     Plot the price, spread, and Z-score of two given symbols against each other.

#     Parameters:
#         sym_1 (str): The first trading symbol.
#         sym_2 (str): The second trading symbol.
#         num_wave (int, optional): The number of waves (used for saving the graph with a unique name). Default is 0.
#     """
#     with open("15m_price_list.json", "r")as price_data:
#         data = json.load(price_data)
#         price_symbol_1 = data[sym_1]
#         price_symbol_2 = data[sym_2]
    
    
#     spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(price_symbol_1, price_symbol_2, 40)
#     z_score = calculate_z_score_window(spread, 40)
    
#     # Make the starting point of the graph SPREAD_WINDOW + Z_SCORE_WINDOW
#     price_symbol_1 = price_symbol_1[-50:]
#     price_symbol_2 = price_symbol_2[-50:]
    
#     spread = spread[-50:]
#     z_score = z_score[-50:]
    
#     # Calculate percentage changes
#     df = pd.DataFrame(columns=[sym_1, sym_2])
#     df[sym_1] = price_symbol_1
#     df[sym_2] = price_symbol_2
#     df[f"{sym_1}_pct"] = df[sym_1] / price_symbol_1[0]
#     df[f"{sym_2}_pct"] = df[sym_2] / price_symbol_2[0]
#     series_1 = df[f"{sym_1}_pct"].astype(float).values
#     series_2 = df[f"{sym_2}_pct"].astype(float).values
    
#     fig, axs = plt.subplots(4, figsize = (16, 8))
#     fig.suptitle(f"Price, Spread and Z_score - {sym_1} vs {sym_2}")
#     axs[0].plot(series_1, label = f"{sym_1}")
#     axs[0].plot(series_2, label = f"{sym_2}")
#     axs[0].title.set_text("Price percentage change")
#     axs[0].legend()
#     axs[1].plot(spread)
#     axs[1].title.set_text("Spread")
#     axs[2].plot(z_score)
#     axs[2].axhline(y=1.2, color='r', linestyle='dotted')
#     axs[2].axhline(y=-1.2, color='r', linestyle='dotted')
#     axs[2].axhline(y=0, color='g', linestyle='-')
#     axs[2].title.set_text("Z score")
#     axs[3].plot(hedge_ratio_list)
#     axs[2].title.set_text("Hedge Ratio")
#     plt.savefig(f"{num_wave}_wave_trading_pair_history_graph.png")

# plot_reference("FILUSDT", "CRVUSDT")
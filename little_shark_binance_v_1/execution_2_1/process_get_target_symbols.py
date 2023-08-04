"""Process of getting target trading symbols"""
from config import INTERVAL, NUM_INTERVAL_LIMIT, WAIT_SEARCH_BEST_PAIR
from config_logger import logger
from func_get_traget_symbols import get_tradeable_symbols_dynamic, store_price_history_static, get_cointegrated_pairs, choose_best_trading_pair_static, get_cointegrated_pairs_dynamic, choose_best_trading_pair_dynamic
from plot_trading_pair import plot_reference
import json
import pandas as pd
import time

def process_get_target_symbols_dynamic(num_wave:int) -> tuple:
    """
    Process of getting target trading symbols using dynamic hedge-ratio backtesting.

    This function follows a step-by-step process to obtain and rank trading pairs based on cointegration,
    then filters them using both static and dynamic hedge-ratio backtesting. It repeats the process until
    it finds a suitable tradable pair or waits for a specific time if no pair is found.

    Parameters:
        num_wave (int): The number of waves used for saving the graph with a unique name.

    Returns:
        tuple: A tuple containing the selected tradable symbols. If a tradable pair is found, the tuple
        will contain two strings representing the symbols. Otherwise, the tuple will be empty.

    Note:
        - The function expects the configuration parameters to be set before execution.
        - It uses external functions for data retrieval, backtesting, and plotting.
        - The function logs the execution progress using the configured logger.
        - The function may enter an infinite loop if no tradable pair is found.
          The WAIT_SEARCH_BEST_PAIR parameter controls the waiting time between attempts.
          Make sure to set a reasonable value for this parameter in the config file.
    """
    while True:
        # STEP 1: Get all the tradable symbols
        logger.info("Getting tradable symbols from Binance.")
        tradeable_symbols = get_tradeable_symbols_dynamic()
        
        # STEP 2: Store the prices in Json
        logger.info(f"Deriving recent price, with the interval of {INTERVAL} and num of interval limit {NUM_INTERVAL_LIMIT}")
        
        # Get the price data used for trainning, the number of data would be NUM_INTERVAL_LIMIT +Z_SCORE_WINDOW
        price_filename = store_price_history_static(tradeable_symbols)

        # STEP 3: Get cointegrated pairs and rank them
        logger.info("Obtaining co-integrated pairs")
        with open(f"{price_filename}") as json_file:
            price_data = json.load(json_file)
            if len(price_data) > 0:
                df_coint = get_cointegrated_pairs(price_data, num_wave)
        logger.info("Obtaining co-integrated pairs complete.")

        # Step 4: Filtering trading pairs based on static hedge-ratio backtesting
        logger.info("Filtering trading pairs based on static hedge-ratio backtesting")
        df_coint_static = choose_best_trading_pair_static(df_coint)

        # Step 5: Filtering trading pairs based on dynamic hedge-ratio backtesting
        logger.info("Get trading pairs based on dynamic hedge-ratio backtesting")
        df_coint_dynamic = get_cointegrated_pairs_dynamic(price_data, df_coint_static, num_wave)
        
        # Step 6: Filtering trading pairs based on dynamic hedge-ratio backtesting
        logger.info("Filtering trading pairs based on dynamic hedge-ratio backtesting")
        flag, symbol_1, symbol_2 = choose_best_trading_pair_dynamic(df_coint_dynamic)
        
        if flag:
            logger.critical(f"Tradable symbols found {symbol_1} and {symbol_2}")
            # plot the reference graph
            plot_reference(symbol_1, symbol_2, num_wave)
            return symbol_1, symbol_2
        else:
            logger.critical(f"Tradable symbols NOT found. Wait for {WAIT_SEARCH_BEST_PAIR}s and search again")
            time.sleep(WAIT_SEARCH_BEST_PAIR)

# print(process_get_target_symbols_dynamic(0))

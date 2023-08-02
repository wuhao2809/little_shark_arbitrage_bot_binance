"""Process of getting target trading symbols"""
from config import INTERVAL, NUM_INTERVAL_LIMIT, WAIT_SEARCH_BEST_PAIR
from config_logger import logger
from func_get_traget_symbols import get_tradeable_symbols_dynamic, store_price_history_static, get_cointegrated_pairs, choose_best_trading_pair_static
from plot_trading_pair import plot_reference
import json
import pandas as pd
import time

def process_get_target_symbols_dynamic(num_wave:int) -> tuple:
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
        with open(f"{price_filename}") as json_file: #
            price_data = json.load(json_file)
            if len(price_data) > 0:
                df_coint = get_cointegrated_pairs(price_data, num_wave)
        logger.info("Obtaining co-integrated pairs complete.")

        # Step 4: Choose the best trading pairs
        logger.info("Chooing the best trading pair")
        flag, symbol_1, symbol_2 = choose_best_trading_pair_static(df_coint)

        if flag:
            logger.critical(f"Tradable symbols found {symbol_1} and {symbol_2}")
            # plot the reference graph
            plot_reference(symbol_1, symbol_2, num_wave)
            return symbol_1, symbol_2
        else:
            logger.critical(f"Tradable symbols NOT found. Wait for {WAIT_SEARCH_BEST_PAIR}s and search again")
            time.sleep(WAIT_SEARCH_BEST_PAIR)

print(process_get_target_symbols_dynamic(0))
    
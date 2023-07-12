"""Process of getting target trading symbols"""
from config import interval, num_interval_limit
from config_logger import logger
from func_get_traget_symbols import get_tradeable_symbols_dynamic, store_price_history_static, get_cointegrated_pairs
import json

def process_get_target_symbols_dynamic() -> tuple:
    
    # # STEP 1: Get all the tradable symbols
    # logger.info("Getting tradable symbols from Binance.")
    # tradeable_symbols = get_tradeable_symbols_dynamic()
    
    # # STEP 2: Store the prices in Json
    # logger.info(f"Deriving recent price, with the interval of{interval} and num of interval limit{num_interval_limit}")
    # price_filename = store_price_history_static(tradeable_symbols)

    # STEP 3: Get cointegrated pairs and rank them
    logger.info("Obtaining co-integrated pairs")
    with open("15m_price_list.json") as json_file:
        price_data = json.load(json_file)
        if len(price_data) > 0:
            filename = get_cointegrated_pairs(price_data, 6)
    return filename

process_get_target_symbols_dynamic()
    
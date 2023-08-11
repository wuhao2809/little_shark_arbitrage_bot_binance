from config import WAVE_LIMIT, LEVERAGE
from config_logger import logger
from process_get_target_symbols import process_get_target_symbols_dynamic
from process_trading import process_trading
from process_summarize import process_summarize
from func_trading import get_current_z_score_dynamic, cancel_all_orders_dynamic
from binance_market_observer import binance_get_min_trading_qty_for_symbols
from binance_trader import set_leverage
from binance_account_observer import get_current_balance_USDT_dynamic
from process_get_parameters import process_get_parameters

import time
import datetime

def main():
    """
    Little Shark v2.1 - Automated Trading Strategy Main Function.

    This function is the entry point for running the Little Shark v2.1 automated trading strategy.
    It manages the process of searching for the best trading pairs, executing the trading waves, and summarizing
    the results for each wave. The function runs in a loop for a specified number of waves (WAVE_LIMIT).

    Note:
        - The function imports necessary configurations, modules, and helper functions.
        - It initializes the logger and sets up necessary configurations before starting the trading process.
        - The trading process includes the following steps for each wave:
            - Step 1: Searching for the best trading pairs (process_get_target_symbols_dynamic).
            - Step 2: Executing the trading wave (process_trading).
            - Step 3: Summarizing the results of the trading wave (process_summarize).
        - The process may encounter errors, and it logs any exceptions that occur during the execution.
        - If an error occurs, the process waits for one minute and attempts to resume the execution.

    Returns:
        None
    """
    # Initialization
    logger.critical("Little Shark v3.1 start!!!")

    num_wave = 1
    status = "Selecting Parameters"

    # Creat the trading_min_qty_file
    binance_get_min_trading_qty_for_symbols()
    cancel_all_orders_dynamic()
    logger.critical("Initialization complete!")

    while(num_wave <= WAVE_LIMIT):
        try:
            # Step 0: Find the best parameters
            if status == "Selecting Parameters":
                logger.critical(f"Starting to select best parameters for wave {num_wave}")
                process_get_parameters()
                # update status
                status = "Searching Trading Pairs"
            
            # Step 1: Find the best trading pairs
            if status == "Searching Trading Pairs":
                logger.critical(f"Starting to search best trading pairs for wave {num_wave}")
                
                # get the best trading pairs
                target_flag, symbol_1, symbol_2 = process_get_target_symbols_dynamic(num_wave)
                if target_flag:
                    logger.critical(f"Best trading pairs found, {symbol_1} and {symbol_2}")
                    
                    # get original z score
                    original_z_score = get_current_z_score_dynamic(symbol_1, symbol_2)
                    
                    # Set leverage
                    logger.info("Setting leverage.")
                    set_leverage(symbol_1, LEVERAGE)
                    set_leverage(symbol_2, LEVERAGE)
                    
                    # update status
                    status = "Trading"

                else:
                    # return to the previous status
                    status = "Selecting Parameters"
            # Step2: Trading
            if status == "Trading":
                logger.critical(f"Start trading with symbol_1 {symbol_1} and symbol_2 {symbol_2}")
                logger.critical(f"Original z_score is {original_z_score}")

                # Get wave start balance
                wave_start_balance = get_current_balance_USDT_dynamic()
                wave_start_time = datetime.datetime.now()
                
                total_invested_value, exit_z_score = process_trading(symbol_1, symbol_2, original_z_score, num_wave)
                logger.critical("Trading process complete.")
                
                # update status
                status = "Summary"
            
            if status == "Summary":
                logger.critical(f"Start summarize the trading result for symbol_1 {symbol_1} and symbol_2 {symbol_2}")
                
                # Get the information of the wave
                wave_end_balance = get_current_balance_USDT_dynamic()
                wave_profit = wave_end_balance - wave_start_balance
                wave_end_time = datetime.datetime.now()
                
                
                # Process the summarize
                process_summarize(num_wave, symbol_1, symbol_2, wave_start_balance, wave_end_balance, 
                                  wave_profit, total_invested_value, original_z_score, 
                                  exit_z_score, wave_start_time, wave_end_time)
                logger.critical("Wave process complete.")
                
                # update status
                status = "Selecting Parameters"
                num_wave += 1
        
        except Exception as er:
            logger.critical(f"Errors occur!!!")
            logger.critical(f"Error messages: {er}")
            logger.info("Wait for one minute and try to resume the process.")
            time.sleep(60)
            
if __name__ == "__main__":
    main()
from config import INTERVAL_INT, TRADING_TIME_LIMIT_INTERVALS
from config_logger import logger
from func_trading import check_trading_status, wait_trade_oppotunity, close_all_positions_dynamic, quick_open_positions, quick_open_positions_market, get_current_z_score_dynamic, get_current_hedge_ratio_dynamic
from binance_account_observer import get_current_positions_info
from plot_trading_pair import plot_reference_trading
import datetime
import time

def process_trading(symbol_1: str, symbol_2: str, original_z_score: float, num_wave: int):
    """
    Process the trading wave for a given pair of symbols.

    This function follows a step-by-step process to execute the trading wave for a specified pair of symbols.
    It checks the trading status, enters the market, waits for trading opportunities, and closes the positions
    when appropriate. The function also plots the reference graph for the trading pair.

    Parameters:
        symbol_1 (str): The first trading symbol in the pair.
        symbol_2 (str): The second trading symbol in the pair.
        original_z_score (float): The Z-score at the start of the trading wave.
        num_wave (int): The number of the trading wave.

    Returns:
        tuple: A tuple containing the total invested value and the exit Z-score for the trading wave.

    Note:
        - The function expects the configuration parameters to be set before execution.
        - It uses external functions for checking trading status, opening and closing positions,
          waiting for trading opportunities, and getting dynamic Z-score and hedge ratio.
        - The function logs the execution progress using the configured logger.
        - The function may enter a loop until the trading wave is complete, based on trading opportunities.
          The limit time for the wave is calculated based on the configuration parameters and the
          initial start time.
          Make sure to set a reasonable value for the TRADING_TIME_LIMIT_INTERVALS parameter in the config file.
        - The function also plots the reference graph using the plot_reference_trading function from
          the plot_trading_pair module.
    """
    
    # Initialization
    start_time = datetime.datetime.now()
    
    limit_end_trading_time = start_time + datetime.timedelta(minutes=INTERVAL_INT * TRADING_TIME_LIMIT_INTERVALS)
    logger.info(f"The limit time for this wave is {limit_end_trading_time}")
    
    exit_flag = False
    
    while not exit_flag:
    
        trading_flag = check_trading_status(symbol_1, symbol_2, original_z_score, limit_end_trading_time)
        time.sleep(1)
        
        # enter the market
        if trading_flag == "enter":
            current_hedge_ratio = get_current_hedge_ratio_dynamic(symbol_1, symbol_2)
            trading_flag = quick_open_positions_market(symbol_1, symbol_2, current_hedge_ratio, original_z_score)
        
        # wait for trading oppotunities
        if trading_flag == "wait":
            trading_flag = wait_trade_oppotunity(symbol_1, symbol_2, original_z_score)

        # close the positions
        if trading_flag == "exit":
            _, _, symbol_1_invested_value, _, _, symbol_2_invested_value = get_current_positions_info(symbol_1, symbol_2)
            total_invested_value = symbol_1_invested_value + symbol_2_invested_value
            exit_flag = close_all_positions_dynamic()
            exit_z_score = get_current_z_score_dynamic(symbol_1, symbol_2)
            
        # Plot the reference graph
        plot_reference_trading(symbol_1, symbol_2, num_wave)

    return total_invested_value, exit_z_score
        
        
        
        
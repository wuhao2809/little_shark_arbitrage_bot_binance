from config import INTERVAL_INT, TRADING_TIME_LIMIT_INTERVALS
from config_logger import logger
from func_trading import check_trading_status, wait_trade_oppotunity, close_all_positions_dynamic, quick_open_positions, quick_open_positions_market, get_current_z_score_dynamic, get_current_hedge_ratio_dynamic
from binance_account_observer import get_current_positions_info
from plot_trading_pair import plot_reference_trading
import datetime
import time

def process_trading(symbol_1: str, symbol_2: str, original_z_score: float, num_wave: int):
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
        
        
        
        
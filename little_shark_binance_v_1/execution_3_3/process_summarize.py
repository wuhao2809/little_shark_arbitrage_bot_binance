from config_logger import logger
from config import config
import csv
import datetime

def process_summarize(wave_num, symbol_1, symbol_2, wave_start_balance, wave_end_balance, wave_profit, total_invested_value, original_z_score, exit_z_score, wave_start_time, wave_end_time):
    """
    Process and summarize the results of a trading wave.

    This function writes the summary of a trading wave to a CSV file and logs the summary using the configured logger.

    Parameters:
        wave_num (int): The number of the trading wave.
        symbol_1 (str): The first trading symbol in the pair.
        symbol_2 (str): The second trading symbol in the pair.
        wave_start_balance (float): The balance at the start of the trading wave.
        wave_end_balance (float): The balance at the end of the trading wave.
        wave_profit (float): The profit earned during the trading wave.
        total_invested_value (float): The total value invested during the trading wave.
        original_z_score (float): The Z-score at the start of the trading wave.
        exit_z_score (float): The Z-score at the end of the trading wave.
        wave_start_time (datetime): The start time of the trading wave.
        wave_end_time (datetime): The end time of the trading wave.

    Note:
        - The function appends the trading wave summary to a CSV file named 'Little_Shark_Binance_V_2_1_Running_Summary.csv'.
        - It uses the csv.DictWriter class to write the summary in CSV format.
        - If it is the first wave (wave_num == 1), the function writes the CSV header.
        - The function logs the summary using the configured logger.
        - The logger must be set up before calling this function to ensure proper logging.
    """
    status_dict = {"wave_num" : wave_num, "symbol_1": symbol_1, "symbol_2": symbol_2,
                   "interval": config.INTERVAL, "trainning_period": config.NUM_INTERVAL_LIMIT, "spread_window": config.SPREAD_WINDOW,
                   "z_score_window": config.Z_SCORE_WINDOW, "trigger_z_score_window": config.TRIGGER_Z_SCORE_THRESHOD, "current_account_balance": config.ACCOUNT_BALANCE_INVESTABLE,
                   "wave_start_balance": wave_start_balance, "wave_end_balance": wave_end_balance,
                   "wave_profit": wave_profit, "total_invested_value": total_invested_value, 
                   "original_z_score": original_z_score, "exit_z_score": exit_z_score, "wave_start_time": wave_start_time, "wave_end_time": wave_end_time}
    
    with open('Little_Shark_Binance_V_2_1_Running_Summary.csv', 'a') as status:
        writer = csv.DictWriter(status, status_dict.keys())
        if wave_num == 1:
            writer.writeheader()
        writer.writerow(status_dict)
        
    logger.info(f"Summary as follows: ")
    logger.info(f"{status_dict}")
from config_logger import logger
import csv
import datetime

def process_summarize(wave_num, symbol_1, symbol_2, wave_start_balance, wave_end_balance, wave_profit, total_invested_value, hedge_ratio, original_z_score, exit_z_score, wave_start_time, wave_end_time):
    
    status_dict = {"wave_num" : wave_num, "symbol_1": symbol_1, "symbol_2": symbol_2, 
                   "wave_start_balance": wave_start_balance, "wave_end_balance": wave_end_balance,
                   "wave_profit": wave_profit, "total_invested_value": total_invested_value, "hedge_ratio": hedge_ratio, 
                   "original_z_score": original_z_score, "exit_z_score": exit_z_score, "wave_start_time": wave_start_time, "wave_end_time": wave_end_time}
    
    with open('Little_Shark_Binance_V_1_Running_Summary.csv', 'a') as status:
        writer = csv.DictWriter(status, status_dict.keys())
        if wave_num == 1:
            writer.writeheader()
        writer.writerow(status_dict)
        
    logger.info(f"Summary as follows: ")
    logger.info(f"{status_dict}")
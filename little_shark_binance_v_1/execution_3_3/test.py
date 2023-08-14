import json
from config import config

print(config.NUM_INTERVAL_LIMIT, config.SPREAD_WINDOW, config.Z_SCORE_WINDOW, config.TRIGGER_Z_SCORE_THRESHOD, config.ACCOUNT_BALANCE_INVESTABLE, config.INTERVAL, config.INTERVAL_INT)
# modify the json file
dict = {"interval": "15m", "trainning_period": 200, 
        "spread_window": 20, "z_score_window": 120, 
        "z_score_threshod": 1.2,
        "current_balance": 500}
with open ("parameters.json", "w") as json_file:
    json.dump(dict, json_file, indent=4)

print(config.NUM_INTERVAL_LIMIT, config.SPREAD_WINDOW, config.Z_SCORE_WINDOW, config.TRIGGER_Z_SCORE_THRESHOD, config.ACCOUNT_BALANCE_INVESTABLE, config.INTERVAL, config.INTERVAL_INT)
print(f"Current parameters, please check: interval: {config.INTERVAL}, training_period: {config.NUM_INTERVAL_LIMIT}\n"
    f"spread_window: {config.SPREAD_WINDOW}, z_score_window: {config.Z_SCORE_WINDOW}, trigger_z_score:{config.TRIGGER_Z_SCORE_THRESHOD}, account_balance: {config.ACCOUNT_BALANCE_INVESTABLE}")
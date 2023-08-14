import json
from config import NUM_INTERVAL_LIMIT, SPREAD_WINDOW, Z_SCORE_WINDOW, TRIGGER_Z_SCORE_THRESHOD, ACCOUNT_BALANCE_INVESTABLE, INTERVAL, INTERVAL_INT

print(NUM_INTERVAL_LIMIT, SPREAD_WINDOW, Z_SCORE_WINDOW, TRIGGER_Z_SCORE_THRESHOD, ACCOUNT_BALANCE_INVESTABLE, INTERVAL, INTERVAL_INT)
dict = {"interval": "30m", "trainning_period": 200, 
        "spread_window": 10, "z_score_window": 10, 
        "z_score_threshod": 1.3,
        "current_balance": 300}
with open ("parameters.json", "w") as json_file:
    json.dump(dict, json_file, indent=4)

print(NUM_INTERVAL_LIMIT, SPREAD_WINDOW, Z_SCORE_WINDOW, TRIGGER_Z_SCORE_THRESHOD, ACCOUNT_BALANCE_INVESTABLE, INTERVAL, INTERVAL_INT)
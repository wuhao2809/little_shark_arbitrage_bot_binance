from config import (Z_SCORE_WINDOW, INTERVAL, NUM_INTERVAL_LIMIT, STOP_LOSS_VALUE, TAKE_PROFIT_VALUE, TOTAL_INVESTABLE_VALUE, 
                    INVESTIBLE_CAPITAL_EACH_TIME, INVESTED_VALUE_BIAS_RATIO, INTERVAL_INT, WAITING_INTERVAL, TRIGGER_Z_SCORE_THRESHOD,
                    SECONDS_WAIT_LIMIT_CLOSE, SECONDS_WAIT_MARKET_CLOSE, SECONDS_WAIT_LIMIT_OPEN, SECONDS_WAIT_MARKET_OPEN, SPREAD_WINDOW,
                    NOT_INVESTING_TRADING_INTERVAL_LIMIT)
from func_calculation_static import calculate_spread_static, calculate_z_score_window, check_cointegration_quick, calculate_spread_hedge_ratio_window
from binance_market_observer import binance_get_recent_close_price, binance_get_min_trading_qty
from func_get_traget_symbols import calculate_cointegration_static, check_differnet_signal
from binance_account_observer import get_current_positions_info, get_current_positions_dynamic, check_position_num, get_current_position_qty
from binance_trader import cancel_all_orders_dynamic, get_order_book_best_price, place_limit_order, place_market_order
from config_logger import logger
import datetime
import time
import sys

def get_current_z_score_dynamic(symbol_1: str, symbol_2: str):
    """
    Calculates the current z-score for a pair of symbols based on recent close prices.

    Parameters:
        symbol_1 (str): The first symbol of the pair.
        symbol_2 (str): The second symbol of the pair.

    Returns:
        float: The current z-score for the symbol pair.
    """
    
    series_1 = binance_get_recent_close_price(symbol=symbol_1, interval=INTERVAL, limit=SPREAD_WINDOW + Z_SCORE_WINDOW + 1)
    series_2 = binance_get_recent_close_price(symbol=symbol_2, interval=INTERVAL, limit=SPREAD_WINDOW + Z_SCORE_WINDOW + 1)
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1, series_2, SPREAD_WINDOW)
    zscore_series = calculate_z_score_window(spread, window=Z_SCORE_WINDOW)
    
    current_z_score = zscore_series[-1]
    return float(current_z_score)

# print(get_current_z_score_dynamic('LTCUSDT', 'TRXUSDT'))

def get_current_hedge_ratio_dynamic(symbol_1: str, symbol_2: str):
    """
    Calculates the current hedge ratio for a pair of symbols based on recent close prices.
    
    Parameters:
        symbol_1 (str): The first symbol of the pair.
        symbol_2 (str): The second symbol of the pair.
    
    Returns:
        float: The current hedge ratio for the symbol pair.
    """
    series_1 = binance_get_recent_close_price(symbol=symbol_1, interval=INTERVAL, limit=SPREAD_WINDOW + 1)
    series_2 = binance_get_recent_close_price(symbol=symbol_2, interval=INTERVAL, limit=SPREAD_WINDOW + 1)
    
    spread, hedge_ratio_list = calculate_spread_hedge_ratio_window(series_1, series_2, SPREAD_WINDOW)
    
    current_hedge_ratio = hedge_ratio_list[-1]
    return float(current_hedge_ratio)

# print(get_current_hedge_ratio_dynamic('LTCUSDT', 'TRXUSDT'))

def check_trading_status(symbol_1, symbol_2, original_z_score, limit_end_trading_time, trading_interval_count):
    """Checks the trading status of a symbol pair in a trading strategy.
    
    Args:
        symbol_1 (str): The first symbol in the trading pair.
        symbol_2 (str): The second symbol in the trading pair.
        original_z_score (float): The original z-score for the pair.
        limit_end_trading_time (datetime): The time limit for trading.
        trading_interval_count(int): the trading interval currently.
    
    Returns:
        str: The trading status, which can be one of the following:
            - "enter": Indicates entering the market.
            - "wait": Indicates waiting for an exit opportunity.
            - "exit": Indicates exiting the market.
    """
    logger.critical("Checking trading status...")
    
    (symbol_1_position_qty, 
     symbol_1_position_unrealized_profit, 
     symbol_1_invested_value,
     symbol_2_position_qty, 
     symbol_2_position_unrealized_profit,
     symbol_2_invested_value) = get_current_positions_info(symbol_1, symbol_2)
    
    total_unrealized_profit = symbol_1_position_unrealized_profit + symbol_2_position_unrealized_profit
    total_invested_value = symbol_1_invested_value + symbol_2_invested_value
    
    # logging
    logger.info(f"Current symbol_1 qty is {symbol_1_position_qty}, profit {symbol_1_position_unrealized_profit}")
    logger.info(f"Current symbol_2 qty is {symbol_2_position_qty}, profit {symbol_2_position_unrealized_profit}")
    logger.info(f"Total profit is {total_unrealized_profit}")
    logger.info(f"Total invested value is {total_invested_value}")
    
    # EXIT
    # check stop loss and take profit
    if total_unrealized_profit > TAKE_PROFIT_VALUE:
        logger.info("Take profit threshod triggered.  Close all the positions and exit the market.")
        return "exit"
    if total_unrealized_profit < -STOP_LOSS_VALUE:
        logger.info("Stop lose threshod triggered.  Close all the positions and exit the market.")
        return "exit"
    
    # check z score
    if check_differnet_signal(original_z_score, current_z_score:=get_current_z_score_dynamic(symbol_1, symbol_2)):
        logger.info(f"Z score crossed. Current z score is {current_z_score}, original_z_score is {original_z_score}.")
        return "exit"
    logger.info(f"Current z-score is {current_z_score}")
    
    # check time
    if limit_end_trading_time < datetime.datetime.now():
        logger.info("Trading time limit reached. Exit the market")
        return "exit"
    
    # check tradeable or not:
    if total_invested_value == 0 and trading_interval_count > NOT_INVESTING_TRADING_INTERVAL_LIMIT:
        logger.info(f"Current trading interval is {trading_interval_count} but still no investing value. Exit the market")
        return "exit"
    
    # WAIT
    # Do not check the cointegration for this version
    # # check cointegration
    # if not check_cointegration_quick(symbol_1, symbol_2):
    #     logger.info("This pair is not cointergrated. Close all the positions and exit the market.")
    #     return "wait"
    
    # check invested value
    if INVESTIBLE_CAPITAL_EACH_TIME * INVESTED_VALUE_BIAS_RATIO > TOTAL_INVESTABLE_VALUE - total_invested_value:
        logger.info(f"Current invested value is {total_invested_value}, threshod reached. Waiting for exit oppotunity.")
        return "wait"
    
    # ENTER
    if (abs(current_z_score) > TRIGGER_Z_SCORE_THRESHOD) and (abs(current_z_score + original_z_score) == abs(current_z_score) + abs(original_z_score)):
        return "enter"
    
    return "wait"
    

# print(check_trading_status("AXSUSDT", "SANDUSDT", 1, datetime.datetime.now()+ datetime.timedelta(hours=1)))

def wait_trade_oppotunity(symbol_1: str, symbol_2: str, original_z_score: float):
    """Processes a waiting trade opportunity for a symbol pair.
    
    Args:
        symbol_1 (str): The first symbol in the trading pair.
        symbol_2 (str): The second symbol in the trading pair.
        original_z_score (float): The original z-score for the pair.
    
    Returns:
        str: The trading status, which can be one of the following:
            - "wait": Indicates waiting for an exit opportunity.
            - "exit": Indicates exiting the market.
    """
    
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=INTERVAL_INT)
    
    while (datetime.datetime.now() < end_time):
        current_z_score = get_current_z_score_dynamic(symbol_1, symbol_2)
        
        # NOTE: Judge the cointergration in the check status period
        # # check cointegration
        # if not check_cointegration_quick(symbol_1, symbol_2):
        #     logger.info("This pair is not cointergrated. Close all the positions and exit the market.")
        #     return "exit"
        
        logger.info(f"Current z score is {current_z_score}, original_z_score is {original_z_score}.")
        
        # check trdae oppotunities
        if(check_differnet_signal(current_z_score, original_z_score)):
            logger.info(f"Z score crossed. Current z score is {current_z_score}, original_z_score is {original_z_score}. Break waiting.")
            return "check"
        
        logger.info(f"Current z score is {current_z_score}, original_z_score is {original_z_score}.")
        logger.info(f"Waiting for next inspection time for {WAITING_INTERVAL}s.")
        
        time.sleep(WAITING_INTERVAL)
        
    return "wait"
        
# print(process_wait_trade_oppotunity("XRPUSDT", "EOSUSDT", 1, -1))
def close_position_limit_order(symbol: str, qty: float, position_direction: str):
    """
    Closes a position using a limit order.
    
    Args:
        symbol (str): The trading symbol.
        qty (float): The quantity to be closed.
        position_direction (str): The direction of the position ("LONG" or "SHORT").
    """
    if position_direction == "LONG":
        order_direction = "SHORT"
        price = get_order_book_best_price(symbol, order_direction)
        place_limit_order(symbol=symbol, qty=qty, price=price, direction="SELL", reduceOnly="TRUE")
    
    elif position_direction == "SHORT":
        order_direction = "LONG"
        price = get_order_book_best_price(symbol, order_direction)
        place_limit_order(symbol=symbol, qty=qty, price=price, direction="BUY", reduceOnly="TRUE")
    
    else: 
        logger.error("No such direction when conducting close_position_limit_order")
        raise KeyError("No such direction when conducting close_position_limit_order")

def open_position_limit_order(symbol: str, qty: float, price: float, order_direction: str):
    """
    Opens a position using a limit order.
    
    Args:
        symbol (str): The trading symbol.
        qty (float): The quantity to be opened.
        price (float): The price at which the order will be placed.
        order_direction (str): The direction of the order ("LONG" or "SHORT").
    """
    if order_direction == "LONG":
        place_limit_order(symbol=symbol, qty=qty, price=price, direction="BUY")
    
    elif order_direction == "SHORT":
        place_limit_order(symbol=symbol, qty=qty, price=price, direction="SELL")
    
    else: 
        logger.error("No such direction when conducting close_position_limit_order")
        raise KeyError("No such direction when conducting close_position_limit_order")


def close_position_market_order(symbol: str, qty: float, position_direction: str):
    """
    Closes a position using a market order.
    
    Args:
        symbol (str): The trading symbol.
        qty (float): The quantity to be closed.
        position_direction (str): The direction of the position ("LONG" or "SHORT").
    """
    if position_direction == "LONG":
        place_market_order(symbol=symbol, qty=qty, direction="SELL", reduceOnly="TRUE")
    
    elif position_direction == "SHORT":
        place_market_order(symbol=symbol, qty=qty, direction="BUY", reduceOnly="TRUE")
    
    else: 
        logger.error("No such direction when conducting close_position_market_order")
        raise KeyError("No such direction when conducting close_position_market_order")

def open_position_market_order(symbol: str, qty: float, order_direction: str):
    """
    Opens a position using a market order.
    
    Args:
        symbol (str): The trading symbol.
        qty (float): The quantity to be opened.
        order_direction (str): The direction of the order ("LONG" or "SHORT").
    """
    if order_direction == "LONG":
        place_market_order(symbol=symbol, qty=qty, direction="BUY")
    
    elif order_direction == "SHORT":
        place_market_order(symbol=symbol, qty=qty, direction="SELL")
    
    else: 
        logger.error("No such direction when conducting open_position_market_order")
        raise KeyError("No such direction when conducting open_position_market_order")

def close_all_positions_limit_dynamic():
    """
    Closes all positions using limit orders.
    """
    positions = get_current_positions_dynamic()
    
    if len(positions) == 0:
        return True
    
    for position in positions:
        symbol = position["symbol"]
        qty = abs(float(position["positionAmt"]))
        if float(position["positionAmt"]) > 0:
            position_side = "LONG"
        elif float(position["positionAmt"]) < 0:
            position_side = "SHORT"

        close_position_limit_order(symbol=symbol, qty=qty, position_direction=position_side)

# close_all_positions_limit_dynamic()
# cancel_all_orders_dynamic()

def close_all_positions_market_dynamic():
    """
    Closes all positions using market orders.
    """
    positions = get_current_positions_dynamic()
    
    if len(positions) == 0:
        return True
    
    for position in positions:
        symbol = position["symbol"]
        qty = abs(float(position["positionAmt"]))
        if float(position["positionAmt"]) > 0:
            position_side = "LONG"
        elif float(position["positionAmt"]) < 0:
            position_side = "SHORT"

        close_position_market_order(symbol=symbol, qty=qty, position_direction=position_side)

def close_all_positions_dynamic():
    """
    Closes all positions dynamically using a combination of limit and market orders.
    """
    # cancel all orders
    cancel_all_orders_dynamic()
    
    # Currently, all the orders are excuated by market order
    
    # # place limit order and wait for 1 minute
    # logger.info("Placing limit orders to close positions")
    # close_all_positions_limit_dynamic()
    
    # logger.info("Waiting for limit orders to be filled")
    # time.sleep(SECONDS_WAIT_LIMIT_CLOSE)
    # cancel_all_orders_dynamic()
    
    if check_position_num() == 0:
        logger.info("All positions have been closed.")
        return True
    
    # place market order and get the position
    logger.info("Placing market orders to close positions")
    close_all_positions_market_dynamic()
    
    logger.info("Waiting for market orders to be filled")
    time.sleep(SECONDS_WAIT_MARKET_CLOSE)
    cancel_all_orders_dynamic()
    
    # Check if all the positions are closed
    if check_position_num() == 0:
        logger.info("All positions have been closed.")
        return True

    else:
        cancel_all_orders_dynamic()
        logger.error("Positions fail to close after market order.")
        return True

# close_all_positions_dynamic()
# close_position_limit_order(symbol="BCHUSDT", qty=1, position_direction="LONG")
# place_limit_order(symbol="BCHUSDT", qty=1, price=257.92, direction="SELL", reduceOnly="TRUE")
# print(get_order_book_best_price("BCHUSDT", "SHORT"))

def get_float_precision(num: float):
    """
    Gets the precision of a floating-point number.
    
    Args:
        num (float): The floating-point number.
    
    Returns:
        int: The precision of the number.
    """
    if num % 1 != 0:
        str_num = str(num)
        return int(str_num[::-1].find("."))
    else: 
        return 0
        
# NOTE: Currently not used
def quick_open_positions(symbol_1: str, symbol_2: str, hedge_ratio: float, original_z_score: float):

    # get the direction for each symbol
    if original_z_score < 0:
        symbol_1_order_direction = "LONG"
        symbol_2_order_direction = "SHORT"
    elif original_z_score > 0:
        symbol_1_order_direction = "SHORT"
        symbol_2_order_direction = "LONG"
    
    # get the orderbook price
    symbol_1_price = get_order_book_best_price(symbol_1, symbol_1_order_direction)
    symbol_2_price = get_order_book_best_price(symbol_2, symbol_2_order_direction)
    
    # get min qty of symbols
    symbol_1_min_qty = binance_get_min_trading_qty(symbol_1)
    symbol_2_min_qty = binance_get_min_trading_qty(symbol_2)
    
    # get the precision of the qty
    symbol_1_qty_precision = get_float_precision(symbol_1_min_qty)
    symbol_2_qty_precision = get_float_precision(symbol_2_min_qty)
    
    # get the qty for each symbol
    symbol_1_qty = round(INVESTIBLE_CAPITAL_EACH_TIME / (symbol_1_price + hedge_ratio * symbol_2_price), symbol_1_qty_precision)
    symbol_2_qty = round(hedge_ratio * symbol_1_qty, symbol_2_qty_precision)
    
    # NOTE
    # Currently, all the orders are placed through market order.
    
    # place limit order for 1min
    logger.info(f"Placing limit open order for {symbol_1}, qty {symbol_1_qty}, price {symbol_1_price}, {symbol_1_order_direction}")
    open_position_limit_order(symbol_1, symbol_1_qty, symbol_1_price, symbol_1_order_direction)
    
    logger.info(f"Placing limit open order for {symbol_2}, qty {symbol_2_qty}, price {symbol_2_price}, {symbol_2_order_direction}")
    open_position_limit_order(symbol_2, symbol_2_qty, symbol_2_price, symbol_2_order_direction)
    
    
    time.sleep(SECONDS_WAIT_LIMIT_OPEN)
    cancel_all_orders_dynamic()
    
    # check how much have left
    symbol_1_position_qty, _, _, symbol_2_position_qty, _, _ = get_current_positions_info(symbol_1, symbol_2)
    symbol_1_remain_position_qty = symbol_1_qty - symbol_1_position_qty
    symbol_2_remain_position_qty = symbol_2_qty - symbol_2_position_qty
    
    # place market order for the rest
    if symbol_1_remain_position_qty > symbol_1_min_qty:
        logger.info(f"Placing market open order for {symbol_1}")
        open_position_market_order(symbol_1, symbol_1_remain_position_qty, symbol_1_order_direction)
        
    if symbol_2_remain_position_qty > symbol_2_min_qty:
        logger.info(f"Placing market open order for {symbol_2}")
        open_position_market_order(symbol_2, symbol_2_remain_position_qty, symbol_2_order_direction)
    time.sleep(SECONDS_WAIT_MARKET_OPEN)
    cancel_all_orders_dynamic()
    
    # check position
    symbol_1_final_position_qty, _, _, symbol_2_final_position_qty, _, _ = get_current_positions_info(symbol_1, symbol_2)
    if symbol_1_final_position_qty > 0.9 * symbol_1_qty and symbol_2_final_position_qty > 0.9 * symbol_2_qty:
        logger.info("All positions have been opened.")
    else: logger.critical("Positions have NOT been fully opened.")
    
    return "wait"

# quick_open_positions("BCHUSDT", "LTCUSDT", 0.1, -1)

def match_open_position_qty_market(symbol_1, symbol_2, hedge_ratio, original_z_score):
    """
    Matches the open position quantities for a symbol pair using market orders.
    
    Args:
        symbol_1 (str): The first symbol in the trading pair.
        symbol_2 (str): The second symbol in the trading pair.
        hedge_ratio (float): The hedge ratio between the symbols.
        original_z_score (float): The original z-score for the pair.
    """
    if original_z_score < 0:
        symbol_1_order_direction = "LONG"
        symbol_2_order_direction = "SHORT"
        
    elif original_z_score > 0:
        symbol_1_order_direction = "SHORT"
        symbol_2_order_direction = "LONG"
    
    symbol_1_current_position_qty = get_current_position_qty(symbol_1)
    symbol_2_current_position_qty = get_current_position_qty(symbol_2)
    
    # get min qty of symbols
    symbol_1_min_qty = binance_get_min_trading_qty(symbol_1)
    symbol_2_min_qty = binance_get_min_trading_qty(symbol_2)
    
    # get the precision of the qty
    symbol_1_qty_precision = get_float_precision(symbol_1_min_qty)
    symbol_2_qty_precision = get_float_precision(symbol_2_min_qty)
    
    gap_symbol_2_qty = round((symbol_1_current_position_qty / hedge_ratio) - symbol_2_current_position_qty, symbol_2_qty_precision)
    gap_symbol_1_qty = round(symbol_2_current_position_qty * hedge_ratio - symbol_1_current_position_qty, symbol_1_qty_precision)
    
    if gap_symbol_2_qty > symbol_2_min_qty:
        logger.info(f"Matching the qty for symbols. Placing market order for {symbol_2} with qty {gap_symbol_2_qty}.")
        open_position_market_order(symbol_2, gap_symbol_2_qty, symbol_2_order_direction)
        time.sleep(30)
    elif gap_symbol_1_qty > symbol_1_min_qty:
        logger.info(f"Matching the qty for symbols. Placing market order for {symbol_1} with qty {gap_symbol_1_qty}.")
        open_position_market_order(symbol_1, gap_symbol_1_qty, symbol_1_order_direction)
        time.sleep(30)
    
    cancel_all_orders_dynamic()
    
# print(get_current_position_qty("BTCUSDT"))

def quick_open_positions_market(symbol_1: str, symbol_2: str, hedge_ratio: float, original_z_score: float):
    """
    Quickly opens positions for a symbol pair using market orders.
    
    Args:
        symbol_1 (str): The first symbol in the trading pair.
        symbol_2 (str): The second symbol in the trading pair.
        hedge_ratio (float): The hedge ratio between the symbols.
        original_z_score (float): The original z-score for the pair.
    """
    # get the direction for each symbol
    
    # In the market order case, when you go long, you are buying the ask price.
    if original_z_score < 0:
        symbol_1_order_direction = "LONG"
        symbol_1_orderbook_direction = "SHORT"
        symbol_2_order_direction = "SHORT"
        symbol_2_orderbook_direction = "LONG"
    elif original_z_score > 0:
        symbol_1_order_direction = "SHORT"
        symbol_1_orderbook_direction = "LONG"
        symbol_2_order_direction = "LONG"
        symbol_2_orderbook_direction = "SHORT"
    
    # get the orderbook price
    
    symbol_1_price = get_order_book_best_price(symbol_1, symbol_1_orderbook_direction)
    symbol_2_price = get_order_book_best_price(symbol_2, symbol_2_orderbook_direction)
    
    # get min qty of symbols
    symbol_1_min_qty = binance_get_min_trading_qty(symbol_1)
    symbol_2_min_qty = binance_get_min_trading_qty(symbol_2)
    
    # get the precision of the qty
    symbol_1_qty_precision = get_float_precision(symbol_1_min_qty)
    symbol_2_qty_precision = get_float_precision(symbol_2_min_qty)
    
    # get the qty for each symbol
    symbol_1_qty = round(INVESTIBLE_CAPITAL_EACH_TIME / (symbol_1_price + hedge_ratio * symbol_2_price), symbol_1_qty_precision)
    symbol_2_qty = round(hedge_ratio * symbol_1_qty, symbol_2_qty_precision)
    
    cancel_all_orders_dynamic()
    # place market order for the rest
    if (symbol_1_qty > symbol_1_min_qty) and (symbol_2_qty > symbol_2_min_qty):
        logger.info(f"Placing market open order for {symbol_1}")
        open_position_market_order(symbol_1, symbol_1_qty, symbol_1_order_direction)
    
        logger.info(f"Placing market open order for {symbol_2}")
        open_position_market_order(symbol_2, symbol_2_qty, symbol_2_order_direction)
        time.sleep(SECONDS_WAIT_MARKET_OPEN)
    else:
        logger.critical(f"Cannot place market order, the qty of sym1 and sym2 don't exceed the min.")
    cancel_all_orders_dynamic()
    
    # NOTE
    # # match the current position
    # match_open_position_qty_market(symbol_1, symbol_2, hedge_ratio, original_z_score)
    # cancel_all_orders_dynamic()
    
    # check position
    logger.info("All positions have been opened.")
    return "wait"

    
    
    
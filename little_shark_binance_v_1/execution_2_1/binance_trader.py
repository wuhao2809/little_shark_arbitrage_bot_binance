from config import session_private, session_public
from config_logger import logger
from binance_account_observer import get_current_positions_dynamic



"""ORDER BOOK"""


def get_order_book_best_price(symbol: str, direction: str):
    """Retrieves the best price from the order book for a symbol and direction.
    
    Args:
        symbol (str): The symbol for the order book.
        direction (str): The direction of the order book, either "buy"/"LONG" or "sell"/"SHORT".
    
    Returns:
        float: The best price from the order book based on the specified direction.
    
    Raises:
        KeyError: If an invalid direction is provided.
    """
    
    info = session_public.book_ticker(symbol)
    bid_price = float(info["bidPrice"])
    ask_price = float(info["askPrice"])
    
    if direction == "buy" or direction == "LONG":
        return bid_price
    
    elif direction == "sell" or direction == "SHORT":
        return ask_price

    else:
        raise KeyError("Wrong direction")

# print(get_order_book_best_price("BCHUSDT", "buy"))

"""EXIT"""
def get_all_order_symbols_dynamic():
    """Get all the symbols with an open order in Binance"""
    symbol_list = []
    orders = session_private.get_orders()
    for order in orders:
        if order["symbol"] not in symbol_list:
            symbol_list.append(order["symbol"])
    
    return symbol_list
    
    
def cancel_all_orders_dynamic():
    """Cancel all the open orders in Binance
    """
    
    symbol_list = get_all_order_symbols_dynamic()
    if len(symbol_list) == 0:
        return
    for symbol in symbol_list:
        session_private.cancel_open_orders(symbol)

# print(session_private.cancel_open_orders("BTCUSDT"))
# cancel_all_orders_dynamic()


def place_limit_order(symbol: str, qty: float, price: float, direction: str, reduceOnly="False"):
    response = session_private.new_order(
        symbol=symbol,
        side=direction,
        type="LIMIT",
        timeInForce = "GTX",
        quantity = qty,
        reduceOnly=reduceOnly,
        price=price,
    )
    logger.info(response)


def place_market_order(symbol: str, qty: float, direction: str, reduceOnly="False"):
    response = session_private.new_order(
        symbol=symbol,
        side=direction,
        type="MARKET",
        quantity = qty,
        reduceOnly=reduceOnly,
    )
    logger.info(response)

def set_leverage(symbol: str, leverage: int):
    response = session_private.change_leverage(
        symbol=symbol,
        leverage=leverage,
        recvWindow=5000,
    )
    logger.info(response)




    
    
        
    
    

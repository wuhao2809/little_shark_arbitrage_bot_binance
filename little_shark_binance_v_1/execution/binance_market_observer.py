from config import session_public
from config_logger import logger
import json

def binance_get_exchange_symbols():
    """get the exchange symbols from the binance

    Returns:
        _type_: a dict with all the symbols information in it
    
    See: https://binance-docs.github.io/apidocs/futures/en/#exchange-information
    """
    return session_public.exchange_info()["symbols"]

# a = binance_get_exchange_symbols()
# with open ("test.json", "w") as json_file:
#     json.dump(a, json_file, indent=4)

def binance_get_recent_close_price(symbol: str, interval: str, limit: int) ->list:
    """get the recent close price list from binace with the related interval

    Args:
        symbol (_type_): the name of the symbol

    Returns:
        _type_: list
    """
    price_list = []
    prices = session_public.klines(symbol=symbol, interval=interval,limit = limit)
    for price in prices:
        price_list.append(float(price[4])) # change str to float
    if len(price_list) == limit:
        return price_list
    else: return

# Not used
def binance_get_open_interest(symbol: str) -> float:
    """return the open interest of the coin at current

    Args:
        symbol (str): symbol name

    Returns:
        float: the current
    """
    return (float(session_public.open_interest(symbol)))

def binance_get_24h_trading_volume_usdt(symbol: str) -> float:
    """get the 24h trading volume in usdt

    Args:
        symbol (str): symbol name

    Returns:
        float: the trading volume in usdt
    """
    return float(session_public.ticker_24hr_price_change(symbol)["quoteVolume"])

# test
# print(binance_get_24h_trading_volume_usdt("BTCUSDT"))

def binance_get_min_trading_qty_for_symbols():
    """
    Retrieves the minimum trading quantity for each symbol on Binance exchange and saves the information in a JSON file.

    Returns:
        None

    Raises:
        Any exceptions that might occur during the API request or file writing process.

    """
    result_dict = {}
    symbols_info = binance_get_exchange_symbols()
    for symbol_info in symbols_info:
        symbol = symbol_info["symbol"]
        min_qty = float(symbol_info["filters"][2]["minQty"])
        result_dict[f"{symbol}"] = min_qty
    with open ("trading_min_qty.json", "w") as jf:
        json.dump(result_dict, jf, indent=4)
        logger.info("The trading_min_qty.json file has been completed.")
    
def binance_get_min_trading_qty(symbol: str):
    """
    Retrieves the minimum trading quantity for a given symbol from the 'trading_min_qty.json' file.
    
    Args:
        symbol (str): The symbol for which to retrieve the minimum trading quantity.
        
    Returns:
        float: The minimum trading quantity for the specified symbol.
    """
    with open("trading_min_qty.json", "r") as file:
        data = json.load(file)
    return data[f"{symbol}"]

def binance_get_latest_price(symbol: str) -> float:
    """
    Retrieves the latest price for a given symbol from the Binance API.

    Args:
        symbol (str): The symbol for which to retrieve the latest price.

    Returns:
        float: The latest price for the specified symbol.
    """
    return float(session_public.ticker_price(symbol)["price"])


# print(binance_get_min_trading_qty("SOLUSDT"))

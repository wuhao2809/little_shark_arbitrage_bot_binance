from config import session_public

def binance_get_exchange_symbols():
    """get the exchange symbols from the binance

    Returns:
        _type_: a dict with all the symbols information in it
    
    See: https://binance-docs.github.io/apidocs/futures/en/#exchange-information
    """
    return session_public.exchange_info()["symbols"]


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

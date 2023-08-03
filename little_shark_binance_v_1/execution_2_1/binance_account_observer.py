from config import session_private
from config_logger import logger

def get_current_positions_dynamic() -> list:
    """
    Fetches the current positions with non-zero position amounts.

    Returns:
        list: A list of positions with non-zero position amounts.
    """
    position_list = []
    positions = session_private.get_position_risk()
    
    for position in positions:
        if float(position["positionAmt"]) != 0:
            position_list.append(position)
    return position_list

# print(get_current_positions_dynamic())

def check_position_num():
    """
    Calculates the number of current positions with non-zero position amounts.

    Returns:
        int: The number of current positions.
    """
    list = get_current_positions_dynamic()
    return len(list)

def get_current_positions_info(symbol_1: str, symbol_2: str):
    """
    Fetches information about the current positions for the given symbols.

    Args:
        symbol_1 (str): The first symbol.
        symbol_2 (str): The second symbol.

    Returns:
        tuple: A tuple containing the following elements:
            - symbol_1_position_qty (float): Absolute quantity of the first symbol's position.
            - symbol_1_position_unrealized_profit (float): Unrealized profit of the first symbol's position.
            - symbol_1_invested_value (float): Invested value of the first symbol's position.
            - symbol_2_position_qty (float): Absolute quantity of the second symbol's position.
            - symbol_2_position_unrealized_profit (float): Unrealized profit of the second symbol's position.
            - symbol_2_invested_value (float): Invested value of the second symbol's position.
    """
    position_list = get_current_positions_dynamic()
    
    symbol_1_position_qty = 0
    symbol_1_position_unrealized_profit = 0
    symbol_1_invested_value = 0
    symbol_2_position_qty = 0
    symbol_2_position_unrealized_profit = 0
    symbol_2_invested_value = 0
    
    for position in position_list:
        if position["symbol"] == symbol_1:
            symbol_1_position_qty = abs(float(position["positionAmt"]))
            symbol_1_position_unrealized_profit = float(position["unRealizedProfit"])
            symbol_1_invested_value = float(position["entryPrice"]) * symbol_1_position_qty
        
        if position["symbol"] == symbol_2:
            symbol_2_position_qty = abs(float(position["positionAmt"]))
            symbol_2_position_unrealized_profit = float(position["unRealizedProfit"])
            symbol_2_invested_value = float(position["entryPrice"]) * symbol_2_position_qty
    
    return (symbol_1_position_qty, 
            symbol_1_position_unrealized_profit, 
            symbol_1_invested_value, 
            symbol_2_position_qty, 
            symbol_2_position_unrealized_profit,
            symbol_2_invested_value)

# print(get_current_positions_info("EOSUSDT", "XRPUSDT"))

def get_current_position_qty(symbol):
    """
    Gets the current quantity of the specified symbol's position.

    Args:
        symbol (str): The symbol of the position to retrieve.

    Returns:
        float: The absolute quantity of the symbol's position. Returns 0 if the symbol is not found.
    """
    position_list = get_current_positions_dynamic()
    for position in position_list:
        if position["symbol"] == symbol:
            symbol_position_qty = abs(float(position["positionAmt"]))
            return symbol_position_qty
    
    return 0  
        
def get_current_balance_USDT_dynamic():
    """
    Fetches the current available balance of USDT.

    Returns:
        float: The available balance of USDT.
    """
    response = session_private.balance(recvWindow=3000)
    for info in response:
        if info["asset"] == "USDT":
            return float(info["availableBalance"])

# print(get_current_balance_USDT_dynamic())
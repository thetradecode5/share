from fyers_apiv3 import fyersModel
import datetime
import logging
import pytz
import sys
import time
import util.config as config_helper
import util.symbol as symbol_helper
import util.transaction as transaction_helper
import util.orderplacement as orderplacement_helper

# Lot Info
BANKNIFTY_LOT_SIZE = 15
NIFTY_LOT_SIZE = 50
FINNIFTY_LOT_SIZE = 40
SENSEX_LOT_SIZE = 10

BANKNIFTY_LOTS_PER_BATCH = 60
NIFTY_LOTS_PER_BATCH = 36
FINNIFTY_LOTS_PER_BATCH = 45
SENSEX_LOTS_PER_BATCH = 100

BANKNIFTY_BUFFER = 200
NIFTY_BUFFER = 100
FINNIFTY_BUFFER = 100
SENSEX_BUFFER = 300

BANKNIFTY_HEDGE_PRICES = [2.5, 1.5]
NIFTY_HEDGE_PRICES = [1, 0.5]
FINNIFTY_HEDGE_PRICES = [1, 0.5]
SENSEX_HEDGE_PRICES = [3, 1.5]

MAX_ORDERS_PER_BATCH = 20

# Logging Config
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ])

prefix_to_index = {
    "NSE:NIFTY" : "NSE:NIFTY50-INDEX",
    "NSE:BANKNIFTY" : "NIFTYBANK-INDEX",
    "NSE:FINNIFTY" : "FINNIFTY-INDEX",
    "BSE:SENSEX" : "SENSEX-INDEX"
}

tz = pytz.timezone("Asia/Kolkata")
time_obj = datetime.datetime.now(tz)
time_str = time_obj.strftime("%H%M%S")

strategy = "shifter"
date_str = time_obj.strftime("%Y-%m-%d")

# Evaluate these globals at start
fyers = None
ce_options = pe_options = None
todays_prefix = None
state_config = None

def my_handler(event, context):
    login_config = config_helper.getLoginConfig()
    session_config = config_helper.getSessionConfig()
    
    global fyers
    fyers = fyersModel.FyersModel(False, None, login_config["app_id"], session_config["access_token"])
    
    getOptions()
    if not todays_prefix:
        logger.info("Cannot find expiry options! Exiting...")
        return
    
    # Get State
    global state_config
    state_config = config_helper.getStateConfig()
    if not state_config:
        updateStateConfig(pnl = 0, max_profit = 0, re_enter = True)
    # Check if we are done for the day
    latest_pnl = getLatestPNL()
    if latest_pnl != 0 and int(state_config["pnl"]) != int(latest_pnl):
        updatePNL(latest_pnl)

    while True:
        time.sleep(1)
        logger.info ("************** %s *******************" % todays_prefix)

        # enter a strangle with hedges
        if state_config["re_enter"]:
            goShort()
        else:
            logger.info ("Today's PNL: %s. Not re-entering. We are done for the day!")
        
        # monitor positions
        monitor()

def goShort():
    if not canEnter():
        logger.warning ("There are open positions for %s..! No new orders will be placed." % todays_prefix)
        return
    
    option_select = getOptionToSell()
    
    if not option_select:
        logger.warning ("Option select is empty..!")
        return

    logger.warning("Option Select: " + str(option_select))

    lot_size, lots_per_batch = getLotInfo()
    logger.warning("Lot Info for %s: Lot Size: %s, Lots Per Batch: %s" % (str(todays_prefix), str(lot_size), str(lots_per_batch)))

    buy_options_to_enter = []
    buy_options_to_enter.append({"name": option_select["hedge_call"]["name"], "quantity": lot_size * lots_per_batch, "ordertype": "BUY"})
    buy_options_to_enter.append({"name": option_select["hedge_put"]["name"], "quantity": lot_size * lots_per_batch, "ordertype": "BUY"})
    
    sell_options_to_enter = []
    sell_options_to_enter.append({"name": option_select["call"]["name"], "quantity": lot_size * lots_per_batch, "ordertype": "SELL"})
    sell_options_to_enter.append({"name": option_select["put"]["name"], "quantity": lot_size * lots_per_batch, "ordertype": "SELL"})

    lots = 6
    logger.info("Total lots to enter: " + str(lots))

    enterInBatches(lots, buy_options_to_enter, sell_options_to_enter)

def getOptionToSell():
    name = prefix_to_index[todays_prefix]
    indexQuote = symbol_helper.getQuotes(fyers, [name])[name]
    logger.warning(name + " Index quote : " + str(indexQuote))

    call_quotes = symbol_helper.getQuotes(fyers, [a["name"] for a in ce_options])
    put_quotes = symbol_helper.getQuotes(fyers, [a["name"] for a in pe_options])

    hedge_high, hedge_low = getHedgePrices()
    logger.info("Expected hedge_high/hedge_low values for options: %s/%s" % (str(hedge_high), str(hedge_low)))

    buffer = getBuffer()

    call = None
    put = None
    for a in ce_options:
        if a["strike"] > indexQuote + (buffer * 0.5):
            call = a
            break
    
    for b in reversed(pe_options):
        if b["strike"] < indexQuote - (buffer * 0.5):
            put = b
            break

    call_hedges = [a for a in ce_options if a["strike"] > indexQuote + buffer and 
                    a["name"] in call_quotes and 
                    call_quotes[a["name"]] < hedge_high and 
                    call_quotes[a["name"]] > hedge_low]
    put_hedges = [a for a in reversed(pe_options) if a["strike"] < indexQuote and 
                    a["name"] in put_quotes and 
                    put_quotes[a["name"]] < hedge_high and 
                    put_quotes[a["name"]] > hedge_low]

    if len(call_hedges) < 1 or len(put_hedges) < 1:
        logger.warning ("One of call_hedges/put_hedges is empty...!")
        return None
    else:
        logger.info ("Calls: %s, Puts: %s, Call Hedges: %s, Put Hedges: %s" % (str(call), str(put), str(call_hedges), str(put_hedges)))
        return {
            "call" : call,
            "put" : put,
            "hedge_call" : call_hedges[0],
            "hedge_put" : put_hedges[0]
        }
    
def getHedgePrices():
    if todays_prefix == "NSE:FINNIFTY":
        return FINNIFTY_HEDGE_PRICES
    if todays_prefix == "NSE:BANKNIFTY":
        return BANKNIFTY_HEDGE_PRICES
    if todays_prefix == "NSE:NIFTY":
        return NIFTY_HEDGE_PRICES
    if todays_prefix == "BSE:SENSEX":
        return SENSEX_HEDGE_PRICES
    
def getBuffer():
    if todays_prefix == "NSE:FINNIFTY":
        return FINNIFTY_BUFFER
    if todays_prefix == "NSE:BANKNIFTY":
        return BANKNIFTY_BUFFER
    if todays_prefix == "NSE:NIFTY":
        return NIFTY_BUFFER
    if todays_prefix == "BSE:SENSEX":
        return SENSEX_BUFFER

def enterInBatches(lots, buy_options_to_enter, sell_options_to_enter):
    lot_size, lots_per_batch = getLotInfo()
    number_of_batches = int (lots / lots_per_batch)
    for batch in range(1, number_of_batches + 1):
        logger.warning ("Batch %s: Entering BUY Options... %s" % (str(batch), str(buy_options_to_enter)))
        doPlaceOrder(buy_options_to_enter)
        time.sleep(1)
        
        logger.warning ("Batch %s: Entering SELL Options... %s" % (str(batch), str(sell_options_to_enter)))
        doPlaceOrder(sell_options_to_enter)
        time.sleep(1)

    remaining_quantity = int (lots % lots_per_batch)
    if remaining_quantity > 0:
        for option in buy_options_to_enter:
            option.update({"quantity": remaining_quantity * lot_size})
        for option in sell_options_to_enter:
            option.update({"quantity":remaining_quantity * lot_size})

        logger.warning ("Batch Final: Entering BUY Options... %s" % (str(buy_options_to_enter)))
        doPlaceOrder(buy_options_to_enter)
        time.sleep(1)
        
        logger.warning ("Batch Final: Entering SELL Options... %s" % (str(sell_options_to_enter)))
        doPlaceOrder(sell_options_to_enter)
        time.sleep(1)

def doPlaceOrder(options):
    for option in options:
        logger.warning("Placing order : " + str(option))

        iterations = 0
        while iterations < 5:
            try:
                iterations += 1
                response = orderplacement_helper.DerivativesIntradayMarketOrder(fyers, option["name"], option["ordertype"], option["quantity"])
                logger.info ("Order placement successful. Response: " + str(response))
                if "s" in response and response["s"] == "ok":
                    break
            except Exception as e:
                logger.warning("Got exception while placing order. " + str(e) + "\nSleep for 2 seconds.")
                time.sleep(2 * iterations)

def canEnter():
    for position in transaction_helper.getPositions(fyers):
        if position["productType"] == "INTRADAY" and position["symbol"].startswith(todays_prefix) and position["netQty"] != 0:
            return False
    
    for order in transaction_helper.getOrders(fyers):
        if order["symbol"].startswith(todays_prefix) and transaction_helper.isOrderPending(order):
            return False

    return True

def getExchanges():
    if todays_prefix == "SENSEX":
        return "BSE:"
    else:
        return "NSE:"

def getLotInfo():
    if todays_prefix == "NSE:FINNIFTY":
        return FINNIFTY_LOT_SIZE, FINNIFTY_LOTS_PER_BATCH
    if todays_prefix == "NSE:BANKNIFTY":
        return BANKNIFTY_LOT_SIZE, BANKNIFTY_LOTS_PER_BATCH
    if todays_prefix == "NSE:NIFTY":
        return NIFTY_LOT_SIZE, NIFTY_LOTS_PER_BATCH
    if todays_prefix == "BSE:SENSEX":
        return SENSEX_LOT_SIZE, SENSEX_LOTS_PER_BATCH

def getOptions():
    # Get the option data
    instruments = symbol_helper.getInstruments()
    start_of_day = datetime.datetime.combine(datetime.datetime.now(), datetime.time.min).timestamp()
    end_of_day = datetime.datetime.combine(datetime.datetime.now(), datetime.time.max).timestamp()

    global ce_options, pe_options, todays_prefix
    for prefix, index_name in prefix_to_index.items():
        options = [{"name" : a["symbol_ticker"], "expiry" : int(a["expiry_date"]), "tok" : a["fytoken"], "strike" : int(float(a["strike_price"])), "lotsize" : int(a["minimum_lot_size"])} 
                                for a in instruments if a["symbol_ticker"].startswith(prefix) and 
                                (a["symbol_ticker"].endswith("CE") or a["symbol_ticker"].endswith("PE")) and a["tick_size"] == "0.05" and a["exchange"] in ["10"]]
    
        
        ce_options = sorted([a for a in options if a["name"].endswith("CE") and a["expiry"] > start_of_day and a["expiry"] < end_of_day], key = lambda k: k["strike"])
        pe_options = sorted([a for a in options if a["name"].endswith("PE") and a["expiry"] > start_of_day and a["expiry"] < end_of_day], key = lambda k: k["strike"])
        
        if len(ce_options) != 0 and len(pe_options) != 0:
            todays_prefix = prefix
            break

def getLatestPNL():
    latest_pnl = 0
    for position in transaction_helper.getPositions(fyers):
        if position["productType"] == "INTRADAY" and position["symbol"].startswith(todays_prefix):
            if position["netQty"] != 0:
                return 0
            else:
                latest_pnl += position["pl"]

    return latest_pnl

def updatePNL(latest_pnl):
    logger.info("Updating %s PNL..." % todays_prefix)
    updateStateConfig(pnl = latest_pnl)

def updateMaxProfit(latest_max_profit):
    logger.info("Updating %s Max Profit..." % todays_prefix)
    updateStateConfig(max_profit = latest_max_profit)

def resetReEnter():
    logger.info("Resetting re-enter for %s ..." % todays_prefix)
    updateStateConfig(re_enter = False)

def updateStateConfig(**kwargs):
    global state_config
    if not state_config:
        state_config = {}
    state_config.update(kwargs)
    state_config.update({"last_update" : datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")})
    config_helper.putStateConfig(state_config)

def getMaxLoss():
    return -6000

def getMaxAllowedOrders(quantity):
    lot_size, lots_per_batch = getLotInfo()
    
    quantity_per_batch = lot_size * lots_per_batch
    number_of_batches = int (abs(quantity) / quantity_per_batch)
    if abs(quantity) % quantity_per_batch != 0:
        number_of_batches += 1

    return number_of_batches * MAX_ORDERS_PER_BATCH

def getCompletedOrdersCount():
    completed_orders = 0
    for order in transaction_helper.getOrders(fyers):
        if order["symbol"].startswith(todays_prefix) and transaction_helper.isOrderComplete(order):
            completed_orders += 1

    return completed_orders

def canExit():
    openPositions = False
    pendingOrders = False
    retryRequired = True
    retryCount = 0
    while retryRequired and retryCount < 3:
        try:
            for position in transaction_helper.getPositions(fyers):
                if position["productType"] == "INTRADAY" and position["symbol"].startswith(todays_prefix) and position["netQty"] != 0:
                    openPositions = True
                    break
            
            for order in transaction_helper.getOrders(fyers):
                if order["symbol"].startswith(todays_prefix) and transaction_helper.isOrderPending(order):
                    pendingOrders = True
                    break
            retryRequired = False
        except Exception as e:
            logger.error("Sleep for a second. Getting exception: " + str(e))
            time.sleep(1)
            retryCount += 1

    return openPositions and not pendingOrders

def exitAllPositions(open_positions):
    logger.warning ("Exiting all positions...")
    lot_size, lots_per_batch = getLotInfo()

    sell_options_to_exit = []
    buy_options_to_exit = []
    for a in open_positions:
        if a["netQty"] < 0:
            sell_options_to_exit.append({"name": a["symbol"], "quantity": lot_size * lots_per_batch, "original_open_quantity": abs(a["netQty"]), "ordertype": "BUY"})
        else:
            buy_options_to_exit.append({"name": a["symbol"], "quantity": lot_size * lots_per_batch, "original_open_quantity": abs(a["netQty"]), "ordertype": "SELL"})
    
    open_quantities = [abs(a["netQty"]) for a in open_positions]
    if open_quantities.count(open_quantities[0]) == len(open_quantities):
        number_of_batches = int(open_quantities[0] / (lot_size * lots_per_batch))
    else:
        max_common_quantity = min(open_quantities)
        number_of_batches = int(max_common_quantity / (lot_size * lots_per_batch))
    
    exitInBatches(number_of_batches, sell_options_to_exit, buy_options_to_exit, lot_size, lots_per_batch)

    latest_pnl = getLatestPNL()
    if latest_pnl != 0 and int(state_config["pnl"]) != int(latest_pnl):
        updatePNL(latest_pnl)

    resetReEnter()

def exitInBatches(number_of_batches, sell_options_to_exit, buy_options_to_exit, lot_size, lots_per_batch):
    for batch in range(1, number_of_batches + 1):
        if sell_options_to_exit:
            logger.warning ("Batch %s: Exiting SELL Options... %s" % (str(batch), str(sell_options_to_exit)))
            doPlaceOrder(sell_options_to_exit)

        if buy_options_to_exit:
            logger.warning ("Batch %s: Exiting BUY Options... %s" % (str(batch), str(buy_options_to_exit)))
            doPlaceOrder(buy_options_to_exit)

        time.sleep(1)

    exited_quantity = number_of_batches * (lot_size * lots_per_batch)
    if (buy_options_to_exit and exited_quantity != buy_options_to_exit[0]["original_open_quantity"]) or (sell_options_to_exit and exited_quantity != sell_options_to_exit[0]["original_open_quantity"]):
        if sell_options_to_exit:
            for option in sell_options_to_exit:
                option.update({"quantity": option["original_open_quantity"] - exited_quantity})
            logger.warning ("Exiting SELL Options with remaining quantity... %s" % str(sell_options_to_exit))
            doPlaceOrder(sell_options_to_exit)
        
        if buy_options_to_exit:
            for option in buy_options_to_exit:
                option.update({"quantity": option["original_open_quantity"] - exited_quantity})
            
            logger.warning ("Exiting BUY Options with remaining quantity... %s" % str(buy_options_to_exit))
            doPlaceOrder(buy_options_to_exit)

def adjust(ce, pe):
    logger.info ("Adjustment required. Checking which position needs shifting...")

    for a in ce_options:
        if a["name"] == ce["symbol"]:
            ce.update({"strike" : a["strike"]})

    for a in pe_options:
        if a["name"] == pe["symbol"]:
            pe.update({"strike" : a["strike"]})

    if abs(ce["strike"] - pe["strike"]) > getBuffer():
        if ce["quote"] > 2 * pe["quote"]:
            shift(pe, "UP")
        else:
            shift(ce, "DOWN")
    else:
        if ce["quote"] > 2 * pe["quote"]:
            shift(ce, "UP")
        else:
            shift(pe, "DOWN")

def shift(position, direction):
    logger.info ("Shifting %s %s" % (str(position["symbol"]), str(direction)))

    options_list = None
    if position["symbol"].endswith("CE"):
        options_list = ce_options
    else:
        options_list = pe_options

    option_select = None
    for index, option in enumerate(options_list):
        if int(option["strike"]) == int(position["strike"]):
            if direction == "UP":
                option_select = options_list[index + 1]
            else:
                option_select = options_list[index - 1]

    lot_size, lots_per_batch = getLotInfo()
    buy_options_to_enter = []
    buy_options_to_enter.append({"name": position["symbol"], "quantity": lot_size * lots_per_batch, "ordertype": "BUY"})
    
    sell_options_to_enter = []
    sell_options_to_enter.append({"name": option_select["name"], "quantity": lot_size * lots_per_batch, "ordertype": "SELL"})

    lots = int(abs(position["netQty"]) / lot_size)

    enterInBatches(lots, buy_options_to_enter, sell_options_to_enter)

def monitor():
    mtm_pnl = 0
    open_positions = []
    for position in transaction_helper.getPositions(fyers):
        if position["productType"] == "INTRADAY" and position["symbol"].startswith(todays_prefix):
            if position["netQty"] != 0:
                open_positions.append(position)
            else:
                mtm_pnl = mtm_pnl + position["pl"]

    if not len(open_positions):
        logger.warning("No open positions found. No monitoring!")
        return
    
    open_position_names = [a["symbol"] for a in open_positions]
    open_position_quotes = symbol_helper.getQuotes(fyers, open_position_names)
    # logger.info ("[DBG] Open position quotes: " + str(open_position_quotes))

    quantity = 0
    sell_ce = sell_pe = None
    for open_position in open_positions:
        quantity = open_position["netQty"]
        quote = open_position_quotes[open_position["symbol"]]
        mtm_pnl = mtm_pnl + (open_position["sellVal"] - open_position["buyVal"]) + (open_position["netQty"] * quote)
        if quantity < 0:
            if open_position["symbol"].endswith("CE"):
                sell_ce = open_position
                sell_ce.update({"quote" : quote})
            else:
                sell_pe = open_position
                sell_pe.update({"quote" : quote})

    logger.info ("%s MTM PNL : %s. Quantity : %s" % (str(todays_prefix), str(symbol_helper.tradeRound(mtm_pnl)), str(abs(quantity))))
    
    if int(mtm_pnl) > int(state_config["max_profit"]):
        logger.info ("Max Profit Attained: %s" % str(int(mtm_pnl)))
        updateMaxProfit(mtm_pnl)

    max_loss = getMaxLoss()
    if state_config["max_profit"] >= abs(max_loss)/2:
        max_loss = state_config["max_profit"] / 3
    else:
        max_loss += state_config["max_profit"]
    max_orders = getMaxAllowedOrders(quantity)
    completed_orders = getCompletedOrdersCount()
    logger.info ("Max Allowed Loss: " + str(max_loss))
    logger.info ("Max Allowed Orders: " + str(max_orders))
    logger.info ("Completed Orders: " + str(completed_orders))

    if mtm_pnl < max_loss and canExit():
        logger.info ("Max Loss breached 1 percent of utilized capital. Exiting all positions")
        exitAllPositions(open_positions)

    # Check if we have to adjust positions
    elif sell_ce["quote"] > 2 * sell_pe["quote"] or sell_pe["quote"] > 2 * sell_ce["quote"]:
        if completed_orders >= max_orders and canExit():
            logger.info ("Max order limit reached...!")
            exitAllPositions(open_positions)
        else:
            adjust(sell_ce, sell_pe)
    else:
        logger.info ("Adjustment not needed. Prices are balanced.")

my_handler(None, None)
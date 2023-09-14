import logging
import sys
import time

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

def DerivativesIntradayMarketOrder(fyers, name, ordertype, quantity):
    time.sleep(0.5)
    order =  {
        "symbol": name,
        "qty": quantity,
        "type":2,
        "side":1 if ordertype == "BUY" else -1,
        "productType":"INTRADAY",
        "limitPrice":0,
        "stopPrice":0,
        "validity":"DAY",
        "disclosedQty":0,
        "offlineOrder":False,
        "stopLoss":0,
        "takeProfit":0
    }

    return fyers.place_order(order)
    
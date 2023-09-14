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

def getPositions(fyers):
    time.sleep(0.5)
    retryCount = 0
    while retryCount < 3:
        try:
            response = fyers.positions()
            if response["code"] == 200:
                return response["netPositions"]
        except Exception as e:
            logger.warning( "Got exception while getting positions! " + str(e))
            time.sleep(2)
            retryCount += 1

def getOrders(fyers):
    time.sleep(0.5)
    retryCount = 0
    while retryCount < 3:
        try:
            response = fyers.orderbook()
            if response["code"] == 200:
                return response["orderBook"]
        except Exception as e:
            logger.warning( "Got exception while getting orders! " + str(e))
            time.sleep(2)
            retryCount += 1

def isOrderPending(order):
    if order["status"] not in [1, 2, 5, 7]:
        return True
    return False

def isOrderComplete(order):
    if order["status"] == 2:
        return True
    return False
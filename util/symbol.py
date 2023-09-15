import csv
import logging
import requests
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

def getNSEInstruments():
    response = requests.get("https://public.fyers.in/sym_details/NSE_FO.csv", allow_redirects=True)
    
    if response.status_code == 200:
        return list(csv.DictReader(response.content.decode('utf-8').splitlines(), 
                                   skipinitialspace=True, 
                                   fieldnames=["fytoken", "symbol_details", "exchange_instrument_type",
                                               "minimum_lot_size", "tick_size", "isin", "trading_session",
                                               "last_update_date", "expiry_date", "symbol_ticker",
                                               "exchange", "segment", "scrip_code", "underlying_scrip_code",
                                               "underlying_exchange_token", "strike_price", "option_type", "underlying_fytoken"]))
    else:
        logger.info ("Instruments fetch failed. Response: " + str(response))
    
    return []

def getBSEInstruments():
    response = requests.get("https://public.fyers.in/sym_details/BSE_FO.csv", allow_redirects=True)
    
    if response.status_code == 200:
        return list(csv.DictReader(response.content.decode('utf-8').splitlines(), 
                                   skipinitialspace=True, 
                                   fieldnames=["fytoken", "symbol_details", "exchange_instrument_type",
                                               "minimum_lot_size", "tick_size", "isin", "trading_session",
                                               "last_update_date", "expiry_date", "symbol_ticker",
                                               "exchange", "segment", "scrip_code", "underlying_scrip_code",
                                               "underlying_exchange_token", "strike_price", "option_type", "underlying_fytoken"]))
    else:
        logger.info ("Instruments fetch failed. Response: " + str(response))
    
    return []

def getQuotes(fyers, names):
    time.sleep(0.5)
    quotes = {}
    response = fyers.quotes({"symbols": ','.join(names)})
    # logger.info ("Quotes response: " + str(response))
    if "code" in response and response["code"] == 200:
        if "d" in response:
            for quote_item in response["d"]:
                
                quotes.update({quote_item["n"] : quote_item["v"]["lp"]})
    
    else:
        logger.info ("Quotes call failed. Response: " + str(response))

    return quotes

def tradeRound(num):
    num = int(num * 100)
    mod5 = num % 5
    num = num - mod5
    return num/100
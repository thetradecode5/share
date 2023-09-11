from fyers_apiv3 import fyersModel
import logging
import sys
import util.config as config

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

login_config = config.getLoginConfig()
session_config = config.getSessionConfig()

fyers = fyersModel.FyersModel(False, None, login_config["app_id"], session_config["access_token"])

profile = fyers.get_profile()
if "s" in profile and profile["s"] == "ok":
    logger.info("Welcome " + str(profile["data"]["fy_id"]))
else:
    logger.info("Got error: " + str(profile))

nifty50 = {"symbols":"NSE:NIFTY50-INDEX"}
nifty50_quote = fyers.quotes(nifty50)
if "s" in nifty50_quote and nifty50_quote["s"] == "ok":
    logger.info("NIFTY 50 Index Quote: " + str(nifty50_quote["d"][0]["v"]["lp"]))
else:
    logger.info("Got error: " + str(nifty50_quote))
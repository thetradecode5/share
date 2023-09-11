from fyers_apiv3 import fyersModel
import logging
import sys
import util.config as config
import webbrowser

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
if not login_config:
    logger.error ("Unable to read config data")

webbrowser.open(
    fyersModel.SessionModel(login_config["app_id"],
                            login_config["redirect_uri"],
                            login_config["response_type"],
                            None,
                            login_config["state"],
                            None,
                            login_config["secret_id"],
                            login_config["grant_type"])
                            .generate_authcode(),
    1)

logger.info ("Web Browser Opened. Please login to your account to generate the access token")
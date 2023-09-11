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

if len(sys.argv) != 2:
    logger.error ("Unable to read auth token! Please provide auth token obtained after login in the form \"python session.py <YOUR_AUTH_CODE>\".")
    sys.exit(0)

auth_token = config.getAuthToken(sys.argv[1])
if not auth_token:
    logger.error ("Unable to extract auth_token!")
    sys.exit(0)

login_config = config.getLoginConfig()

if not login_config:
    logger.error ("Unable to extract auth_token!")
    sys.exit(0)

logger.info ("Generating session using Auth token...")
session = fyersModel.SessionModel(
    login_config["app_id"],
    login_config["redirect_uri"],
    login_config["response_type"],
    None,
    login_config["state"],
    None,
    login_config["secret_id"],
    login_config["grant_type"])
session.set_token(auth_token)
response = session.generate_token()

if not "access_token" in response:
    logger.error("Access token cannot be fetched!")
    logger.error("Response from generate_token(): " + str(response))
    sys.exit(0)

session_config = {"access_token" : response["access_token"]}
config.putSessionConfig(session_config)
logger.info ("Access token fetched and updated successfully.")
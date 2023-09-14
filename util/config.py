import json
import logging
import sys

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

LOGIN_CONFIG = "config/login.json"
SESSION_CONFIG = "config/session.json"
STATE_CONFIG = "config/state.json"
STRATEGY_CONFIG = "config/strategy.json"

def getConfig(config_file):
    config = None
    try:
        with open(config_file) as config_json:
            config = json.load(config_json)
    except Exception as e:
        logging.error ("Got exception while opening file: %s. Error: %s" % (config_file, str(e)))
    
    return config

def putConfig(config_file, config):
    with open(config_file, "w") as config_json:
        json.dump(config, config_json, indent=4)

# Read login.json
def getLoginConfig():
    return getConfig(LOGIN_CONFIG)

# Read session.json
def getSessionConfig():
    return getConfig(SESSION_CONFIG)

# Update session.json
def putSessionConfig(session_config):
    putConfig(SESSION_CONFIG, session_config)

def getAuthToken(url):
    auth_token = url[url.find("auth_code=") + len("auth_code="):]
    auth_token = auth_token[:auth_token.find("&")]
    return auth_token

def getStateConfig():
    return getConfig(STATE_CONFIG)

def putStateConfig(state_config):
    putConfig(STATE_CONFIG, state_config)

def getStrategyConfig():
    return getConfig(STRATEGY_CONFIG)

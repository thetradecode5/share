import json

LOGIN_CONFIG = "config/login.json"
SESSION_CONFIG = "config/session.json"

def getConfig(config_file):
    config = None
    with open(config_file) as config_json:
        config = json.load(config_json)
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


# Share
This repo contains all the code shared with the community.

# Prerequisites

## Install Python
This code requires python 3.8 or higher to run. Head over to [Python downloads](https://www.python.org/downloads/) and install it for your OS.

## Install Dependencies
This code requires [Fyers API Python Client V3](https://pypi.org/project/fyers-apiv3/) to be installed. Run the below command to install the same.
```
pip install fyers-apiv3
```

## Download source code
Download this source code by clicking `Code -> Download ZIP` At the top of this page.

## Create API App
Once python and the necessary dependencies are installed, head over to [Fyers API Dashboard](https://myapi.fyers.in/dashboard) to create an API App. This generates an `APP ID` and `SECRET ID` which we will need in the next step.

## Update APP ID and SECRET ID
Copy the `APP ID` and `SECRET ID` from previous step and update them in `login.json` in conig directory of source code.
```
{
    "redirect_uri" : "https://myapi.fyers.in/dashboard",
    "app_id" : "ABCDE12345-999", --> Update this
    "secret_id" : "A1B2C3D4E5", --> Update this
    "grant_type" : "authorization_code",
    "response_type" : "code",
    "state" : "sample"
}
```

# How to run
Running the code is a 3 step process. We have 3 different python scripts for each step which has to be run in a command prompt.

## Login
Run the `login.py`
```
python login.py 
```
This will open the default web browser with the required parameters. Once login is successful, it redirects to the `Redirect URL` specified during the app creation with the auth_code.

## Generate Session
Run the `session.py` by passing the entire `Redirect URL` with auth_code in quotes.

```
python session.py "ENTIRE_REDIRECT_URL"
```
For example:
```
python session.py "https://myapi.fyers.in/dashboard?s=ok&code=200&auth_code=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTUsInVzZXJuYW1lIjoia21pbmNoZWxsZSIsImVtYWlsIjoia21pbmNoZWxsZUBxcS5jb20iLCJmaXJzdE5hbWUiOiJKZWFubmUiLCJsYXN0TmFtZSI6IkhhbHZvcnNvbiIsImdlbmRlciI6ImZlbWFsZSIsImltYWdlIjoiaHR0cHM6Ly9yb2JvaGFzaC5vcmcvYXV0cXVpYXV0LnBuZz9zaXplPTUweDUwJnNldD1zZXQxIiwiaWF0IjoxNjM1NzczOTYyLCJleHAiOjE2MzU3Nzc1NjJ9.n9PQX8w8ocKo0dMCw3g8bKhjB8Wo7f7IONFBDqfxKhs"&state=sample"
```
This will generate an `access token` which will be further used to run the strategy

## Run the strategy
Run the `strategy.py` 
```
python strategy.py
```
This will run the actual strategy on your account.
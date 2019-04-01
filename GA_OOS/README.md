# Google Analytics API My Project - 'out_of_stock_reporting'


## Overview of GA API access
============================

### Hello Analytics API:

Python quickstart for installed applications

https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/installed-py



## First time
=============

### Enable the API

https://console.developers.google.com/apis/credentials

- Use link above to access credentials page
- Click into 'out_of_stock_reporting' under 'OAuth 2.0 client IDs'
- Click Download JSON and save to project directory it as client_secrets.json

For more info on client secrets check out https://developers.google.com/api-client-library/python/guide/aaa_client_secrets

### Install the client library
pip install --upgrade google-api-python-client



## Running Out of Stock script
==============================

- run get_oos.py
- enter starting date
- day and hour files saved to 'output_assets' folder
- one file per day

import os
import sys
from dotenv import load_dotenv, find_dotenv

# set root path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
CLIENT_SECRETS_PATH = 'client_secrets.json'
# ANALYTICS_REPORTING_DAT_PATH = 'analyticsreporting.dat'
VIEW_ID = '14346041'


output_assets = os.path.join(ROOT_DIR, 'output_assets')
if not os.path.exists(output_assets):
    os.mkdir(output_assets)

day_events_file = os.path.join(output_assets, '{}_day_events.csv')
hourly_events_file = os.path.join(output_assets, '{}_hourly_events.csv')

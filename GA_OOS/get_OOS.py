import os
import math
import config
import warnings
import pandas as pd
from datetime import datetime, timedelta
warnings.filterwarnings(action='ignore')
import httplib2 # a comprehensive HTTP client library
from oauth2client import client, file, tools # Utilities to work with OAuth 2.0 credentials
from apiclient.discovery import build
import argparse # makes it easy to write user-friendly command-line interfaces

'''
Accesses Google Analytics via API to get hourly Out of Stock (OOS)
data for each product page view event.
'''

today = datetime.now().strftime(('%Y%m%d'))


# initialising headers/auth
def initialize_analyticsreporting():
    # Initializes the analyticsreporting service object.
    # Returns: analytics an authorized analyticsreporting service object.
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                     parents =[tools.argparser])
    flags = parser.parse_args([])

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(config.CLIENT_SECRETS_PATH,
                                          scope=config.SCOPES,
                                          message=tools.message_if_missing(config.CLIENT_SECRETS_PATH))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage('analyticsreporting.dat') #(config.ANALYTICS_REPORTING_DAT_PATH)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())

    # Build the service object.
    analytics = build(serviceName='analytics', version='v4', http=http, discoveryServiceUrl=config.DISCOVERY_URI)
    return analytics


# Request Body
# Use the Analytics Service Object to query the Analytics Reporting API V4.
def get_report(analytics, start, end, pg_tkn=None):
    body={
        'reportRequests': [
            {
                'viewId': config.VIEW_ID,
                'dateRanges': [
                    {'startDate': start, 'endDate': end}],
                'metrics':[
                    {'expression': 'ga:totalEvents'}],
                "dimensions" :[
                    {"name":"ga:eventAction"},
                    {"name":"ga:eventLabel"},
                    {"name":"ga:dateHour"},
                    {"name":"ga:pagePathLevel1"}],
                "dimensionFilterClauses":[
                    {"operator": "AND",
                     "filters":[
                         {"dimensionName":"ga:eventCategory",
                          "operator": "EXACT",
                          "expressions":"StockEvents"}]}],
                "samplingLevel":"LARGE",
                "pageSize":100000}]}
    if pg_tkn:
        body['reportRequests'][0]["pageToken"] = pg_tkn
    return analytics.reports().batchGet(body=body).execute()


# Get OOS - by page - Return list of results
# instantiate headers (auth) - run batchGet for each page (100,000 results each pg)
def get_oos(start, end):
    # build the service object
    analytics = initialize_analyticsreporting()

    # run first batchGet request - add dictionary of results to list
    response_list = []
    print('\n\t{} - starting batchGet request - page 1'.format(start))

    # send reportRequest to GA API
    response = get_report(analytics, start, end)
    response_list.append(response)

    # find if more request pages exist
    if 'nextPageToken' in response['reports'][0].keys():

        # set page token from first request
        pg_tkn = response['reports'][0]['nextPageToken']

        # determine total of rows in dataset
        total_rows = response['reports'][0]['data']['rowCount']

        # Find number of total page requests
        max_page = math.ceil(total_rows / int(pg_tkn))
        print('\tRequest info:\n\tpage token: {:,}\n\ttotal rows: {:,}\n\ttotal pages: {}'.format(int(pg_tkn), total_rows, max_page))

        # Cycle through next pages (max pages minus 1 - already retrieved first page)
        print('\tAdditional batchGet requests: ')

        for page in range(0, max_page-1):

            print('\tpage {} . .'.format(page+2), end=' ')

            # batchGet request
            next_response = get_report(analytics, start, end, pg_tkn)

            # add results dictionary of results to list
            response_list.append(next_response)

            # set page token for next request
            if 'nextPageToken' in next_response['reports'][0]:
                pg_tkn = next_response['reports'][0]['nextPageToken']

            print('\t. completed\n\trows: {}'.format(len(next_response['reports'][0]['data']['rows'])))
    return(response_list)


# Build dataframe from API JSON responses
def response_df(response_list):
    df_dict = {}

    print('\n\tbuilding response dataframe')
    # Create data sets for each response
    for response in range(len(response_list)):
        df = pd.DataFrame(response_list[response]['reports'][0]['data']['rows'])
        df['event_action'] = df['dimensions'].map(lambda x : x[0])
        df['event_label'] = df['dimensions'].map(lambda x : x[1])
        df['date'] = df['dimensions'].map(lambda x : x[2][:4]+'-'+x[2][4:6]+'-'+x[2][6:-2])
        df['hour'] = df['dimensions'].map(lambda x : x[2][-2:])
        df['page'] = df['dimensions'].map(lambda x : x[3][1:3])
        df['total_events'] = df['metrics'].map(lambda x : x[0]['values'][0])
        df_clean = df.drop(['dimensions','metrics'], axis=1)
        df_dict[response] = df_clean

    # Merge dict of dfs into one df
    final_df = pd.concat(df_dict.values()) # same structure as current dataframe - Analytics edge!

    # data clean
    final_df['event_action'] = final_df['event_action'].map(lambda x : x.replace('+',' '))
    final_df = final_df[final_df['event_action']!='ghostery']
    final_df['total_events'] = final_df['total_events'].astype(int)
    return(final_df)


# OOS events by day
def day_events(final_df):
    # set events as integer
    final_df['total_events'] = final_df['total_events'].astype(int)

    # group events == event types by day
    day_events_df = final_df.groupby(['page', 'date', 'event_label','event_action']).sum()[['total_events']].reset_index()

    # sort columns
    day_events_df = day_events_df.sort_values(['date','page','event_label','event_action'])

    # save dataframe
    print('\n\tsaving day events file')
    data_date = day_events_df['date'].max().replace('-','')
    day_events_df.to_csv(config.day_events_file.format(data_date), index=False)


# OOS events by hour
def hourly_events(final_df):
    # set events as integer
    final_df['total_events'] = final_df['total_events'].astype(int)

    # group events == event types by hour
    hourly_events_df = final_df.sort_values(['date','hour','page','event_label'])

    # save dataframe
    print('\n\tsaving hourly events file')
    data_date = hourly_events_df['date'].max().replace('-','')
    hourly_events_df.to_csv(config.hourly_events_file.format(data_date), index=False)


if __name__ == "__main__":
    start_date = input('Select start date (yyyy-mm-dd): ')

    # get list of dates from start to today
    time_diff = datetime.now() - pd.to_datetime(start_date)

    # increment dates by one day
    for d in range(time_diff.days):

        # get only date from timestamp
        ga_date = str(timedelta(days=d) + pd.to_datetime(start_date)).split()[0]

        # query GA for each date in list
        response_list = get_oos(ga_date, ga_date)

        # return full OOS data for each day
        final_df = response_df(response_list)

        # saves GA data by day
        day_events(final_df)

        # saves GA data by hour
        hourly_events(final_df)

        print('\n\tGA OOS data pull completed\n')

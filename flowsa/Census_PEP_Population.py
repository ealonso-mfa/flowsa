# Census_CBP.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8
"""
Pulls County Business Patterns data in NAICS from the Census Bureau
Writes out to various FlowBySector class files for these data items
EMP = Number of employees, Class = Employment
PAYANN = Annual payroll ($1,000), Class = Money
ESTAB = Number of establishments, Class = Other
This script is designed to run with a configuration parameter
--year = 'year' e.g. 2015
"""

import pandas as pd
import json
from flowsa.common import US_FIPS, load_api_key


def Census_pop_URL_helper(build_url, config, args):
    urls = []

    # the url for 2010 and earlier is different
    url2000 = 'https://api.census.gov/data/2000/pep/int_population?get=POP,DATE_DESC&for=__aggLevel__:*&DATE_=12&key=__apiKey__'

    for c in config['agg_levels']:
        if args['year'] > '2010':
            url = build_url
            url = url.replace("__aggLevel__", c)
            urls.append(url)
        elif args['year'] == '2010':
            url = url2000
            url = url.replace("__aggLevel__", c)
            if c == "us":
                url = url.replace("*", "1")
            userAPIKey = load_api_key(config['api_name'])  # (common.py fxn)
            url = url.replace("__apiKey__", userAPIKey)
            urls.append(url)
    return urls


def census_pop_call(url, response_load, args):
    json_load = json.loads(response_load.text)
    # convert response to dataframe
    df = pd.DataFrame(data=json_load[1:len(json_load)], columns=json_load[0])
    return df


def census_pop_parse(dataframe_list, args):
    # concat dataframes
    df = pd.concat(dataframe_list, sort=False)
    # Add year
    df['Year'] = args["year"]
    # replace null county cells with '000'
    df['county'] = df['county'].fillna('000')
    # Make FIPS as a combo of state and county codes
    df['Location'] = df['state'] + df['county']
    # replace the null value representing the US with US fips
    df.loc[df['us'] == '1', 'Location'] = US_FIPS
    # drop columns
    df = df.drop(columns=['state', 'county', 'us'])
    # rename columns
    df = df.rename(columns={"POP": "FlowAmount"})
    # add location system based on year of data
    if args['year'] >= '2019':
        df['LocationSystem'] = 'FIPS_2019'
    elif '2015' <= args['year'] < '2019':
        df['LocationSystem'] = 'FIPS_2015'
    elif '2013' <= args['year'] < '2015':
        df['LocationSystem'] = 'FIPS_2013'
    elif '2010' <= args['year'] < '2013':
        df['LocationSystem'] = 'FIPS_2010'
    # hardcode dta
    df['Class'] = 'Other'
    df['SourceName'] = 'Census_PEP_Population'
    df['FlowName'] = 'Population'
    df['Unit'] = 'p'
    # temporary data quality scores
    df['DataReliability'] = None
    df['DataCollection'] = None
    return df

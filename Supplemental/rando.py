#designed to randomly select a ticker from data folder
#randomly select two dates within data to run backtest off of

import os
import random
import csv
import datetime


def randomTicker(path):
    '''
    Gets a random ticker from data CSVs located in the path
    path: a string representing the data directory
    return: a string representing the ticker
    '''
    #get all files in directory
    #extract name of files
    files = os.listdir(path)
    tickers = []
    for f in files:
        if '.csv' in f:
            ticker = f.split('.')[0]
            tickers.append(ticker)
    #get random file
    T = random.choice(tickers)
    return T


def allTickers(path):
    '''
    Gets a list of tickers from data CSVs located in the path
    path: a string representing the data directory
    return: a list representing the strings for each ticker
    '''
    #get all files in directory
    #extract name of files
    files = os.listdir(path)
    tickers = []
    for f in files:
        if '.csv' in f:
            ticker = f.split('.')[0]
            tickers.append(ticker)
    return tickers


def twoDates(path, t, fmt, minDays=365, maxDays=1500):
    '''
    Gets two dates to run back test for
    path: a string representing the data directory
    t: a string representing the ticker (from randomTicker func.)
    fmt: a string representing the format of dates in csv files
    minDays: minimum number of days required for backtesting
    maxDays: maximum number of days required for backtesting
    return: two datetime objects and an int representing the days between the dates
    '''
    file = os.path.join(path, t+'.csv')
    #iterate through csv and get every date from column 0
    datelist = []
    with open(file, 'r') as f:
        reader = csv.reader(f)
        for r in reader:
            datelist.append(r[0])
    #get first and last date from file
    stDateSt = datelist[1]
    lstDateSt = datelist[-1]
    #convert to datetime objects
    stDate = datetime.datetime.strptime(stDateSt, fmt)
    lstDate = datetime.datetime.strptime(lstDateSt, fmt)
    #get random date to start and end
    daysBetween = lstDate - stDate
    rand1 = 0
    rand2 = 0
    while abs(rand1-rand2) < minDays or abs(rand1-rand2) > maxDays:  #ensure at least a year of backtesting
        rand1 = random.randrange(int(daysBetween.days))
        rand2 = random.randrange(int(daysBetween.days))
    #get date range (datetime objects)
    startDate = stDate + datetime.timedelta(days = min(rand1, rand2))
    endDate = stDate + datetime.timedelta(days = max(rand1, rand2))
    intervalLen = endDate - startDate
    return startDate, endDate, intervalLen.days


def main(path, d, iterator, t=None, minDays=365, maxDays=1500):
    '''
    runs the randomization
    Does not get random ticker if a ticker is specified
    path: a string representing the data directory
    d: a dictionary containing datetime formats
    iterator: a string representing the datetime key
    t (opt): a string representing the ticker
    minDays (opt): minimum number of days required for backtesting
    maxDays (opt): maximum number of days required for backtest
    return: string representing the ticker
            two datetime objects for start and end date
            string representing the date format
            int representing the days between the dates
    '''
    if t == None:
        ticker = randomTicker(path)
    else:
        #make sure ticker is in data
        checkPath = os.path.join(path, t+'.csv')
        if os.path.exists(checkPath):
            ticker = t
        else:
            print("No data found for {}".format(t))
            ticker = randomTicker(path)
    fmt = d[iterator]
    start, end, days = twoDates(path, ticker, fmt, minDays, maxDays)
    return ticker, start, end, fmt, days




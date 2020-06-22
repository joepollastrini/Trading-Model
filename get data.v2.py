from pandas_datareader import data as pdr
from datetime import date
import datetime
import yfinance as yf
yf.pdr_override()
import pandas as pd
import os
SUPP_PATH = os.path.join("C:\\"
                      ,"Users"
                      ,"joepo"
                      ,"Desktop"
                      ,"Back Testing"
                      ,"Supplemental"
                        )
import sys
sys.path.insert(1, SUPP_PATH)
import rando

DATAPATH = os.path.join("C:\\"
                        ,"Users"
                        ,"joepo"
                        ,"Desktop"
                        ,"Back Testing"
                        ,"Data"
                        )
#get tickers
tList = []
tickers = rando.allTickers(os.path.join(DATAPATH, 'Favs'))
tList = tList + tickers
#get dates for data
today = date.today()
endDate = datetime.datetime.strftime(today, '%Y-%m-%d')
startDate = '2019-1-1' #change this every quarter ish
#iterate through tickers
print('Downloading data ... ')
for t in tList:
    print(t)
    data = pdr.get_data_yahoo(t, start=startDate, end=endDate)
    data.to_csv(os.path.join(DATAPATH, 'Live', t+'.csv'))

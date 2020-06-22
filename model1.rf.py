import os
DIRECT = os.getcwd()
SUPP_PATH = os.path.join(DIRECT, "Supplemental")
import sys
sys.path.insert(1, SUPP_PATH)
import backtrader as bt
import datetime
import rando
import strats
import myIndicators as mind
import model_analysis as ma
import matplotlib
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


## VARIABLES ##
DATAPATH = os.path.join(DIRECT, "Data", "Live")
TICKERLIST = rando.allTickers(DATAPATH)
DATEDICT = {'d':'%Y-%m-%d'}
ITERATOR = 'd'
ENDDATE = datetime.date.today()
STARTDATE = ENDDATE - datetime.timedelta(days = 175)
STARTINGCASH = 200000
SIZINGPERC = 0.025
FAST_SMA = 20
SLOW_SMA = 100
BOLL_STD = 1
RANGE_DIST_MIN = 1.7
RANGE_DIST_MAX = 2.3
EXIT_DIST = 3.15
RESET_DIST = 1.15
RSI_THRESH = 20
RSI_CLOSE = 10
RSI_PERIOD = 14
MODEL_NAME = 'mean revert random forest.sav'
MODEL = pickle.load(open(os.path.join(SUPP_PATH, MODEL_NAME), 'rb'))
## VARIABLES ##

cerebro = bt.Cerebro()
for t in TICKERLIST:
    data = bt.feeds.GenericCSVData(dataname = os.path.join(DATAPATH, t + '.csv')
                                   ,fromdate = STARTDATE
                                   ,todate = ENDDATE
                                   ,nullvalue = 0.0
                                   ,dtformat = DATEDICT[ITERATOR]
                                   ,datetime = 0
                                   ,high = 2
                                   ,low = 3
                                   ,open = 1
                                   ,close = 4
                                   ,volume = 6
                                   ,openinterest = -1 #no open interest column
                                   )
    cerebro.adddata(data, name=t)
cerebro.broker.set_cash(STARTINGCASH)
print("Running with ${} as starting cash".format(STARTINGCASH))
print("Trading {:.2f}% of portfolio value".format(SIZINGPERC * 100.0))
cerebro.addstrategy(strats.live_model_1_rf
                    ,sizingPerc = SIZINGPERC
                    ,fastSMA = FAST_SMA
                    ,slowSMA = SLOW_SMA
                    ,bollStd = BOLL_STD
                    ,rangeLow = RANGE_DIST_MIN
                    ,rangeHigh = RANGE_DIST_MAX
                    ,stopRange = EXIT_DIST
                    ,resetRange = RESET_DIST
                    ,rsiBound = RSI_THRESH
                    ,rsiClose = RSI_CLOSE
                    ,rsiPeriod = RSI_PERIOD
                    ,mod = MODEL
                    )
cerebro.run()





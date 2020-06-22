'''
Holds all strategies
'''

import backtrader as bt
import datetime
import random
import myIndicators as mind
import pandas as pd




class SMA_RSI_MEAN_REVERT(bt.Strategy):
    params = dict(
        sizingPerc = 0.01
        ,fastSMA = 20
        ,slowSMA = 100
        ,bollStd = 1
        ,rangeLow = 1.75
        ,rangeHigh = 2.25
        ,stopRange = 2.5
        ,resetRange = 1.5
        ,rsiBound = 20
        ,rsiClose = 5
        ,rsiPeriod = 14
        ,printLog = True
        )

    def __init__(self):
        self.startCash = None
        self.order = {}
        self.stoploss = {}
        self.fastSlow = {}
        self.smaCrosses = {}
        self.distInRange = {}
        self.revertEarly = {}
        self.rsiCross = {}
        self.ls = {}
        self.highStop = {}
        self.lowStop = {}
        self.inds = {}
        for i, d in enumerate(self.datas):
            self.order[d] = None
            self.stoploss[d] = None
            self.fastSlow[d] = None
            self.smaCrosses[d] = 0
            self.distInRange[d] = False
            self.revertEarly[d] = False
            self.rsiCross[d] = None
            self.ls[d] = 0
            self.highStop[d] = 0
            self.lowStop[d] = 0
            self.inds[d] = {}
            self.inds[d]['sma fast'] = bt.ind.SMA(d.close, period = self.p.fastSMA).lines.sma
            self.inds[d]['sma slow'] = bt.ind.SMA(d.close, period = self.p.slowSMA).lines.sma
            self.inds[d]['bands'] = bt.ind.BBands(d.close, period = self.p.fastSMA, devfactor = self.p.bollStd, plot=False)
            self.inds[d]['band diff'] = self.inds[d]['bands'].lines.top - self.inds[d]['bands'].lines.mid
            self.inds[d]['rsi'] = bt.ind.RSI_SMA(d.close, period = self.p.rsiPeriod)
            self.inds[d]['rsi buy'] = bt.ind.CrossDown(self.inds[d]['rsi'].lines.rsi, 50 - self.p.rsiBound, plot=False)
            self.inds[d]['rsi sell'] = bt.ind.CrossUp(self.inds[d]['rsi'].lines.rsi, 50 + self.p.rsiBound, plot=False)
            self.inds[d]['rsi close long'] = bt.ind.CrossUp(self.inds[d]['rsi'].lines.rsi, 50 + self.p.rsiClose, plot=False)
            self.inds[d]['rsi close short'] = bt.ind.CrossDown(self.inds[d]['rsi'].lines.rsi, 50 - self.p.rsiClose, plot=False)

    def start(self):
        self.startCash = self.broker.getvalue()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            d = order.data
            if order.isbuy():
                bs = "Bought"
                self.ls[d] = 1
            else:
                bs = "Sold"
                self.ls[d] = -1
            self.log("{} {} shares of {} for ${:.2f}".format(
                bs
                ,order.executed.size
                ,d._name
                ,order.executed.price))
        elif order.status in [order.Canceled]:
            self.log('Order Canceled for {}'.format(order.data._name))
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order rejected or margin issue')

    def resetBools(self, t):
        self.fastSlow[t] = None
        self.smaCrosses[t] = 0
        self.distInRange[t] = False
        self.revertEarly[t] = False
        self.rsiCross[t] = None
        self.ls[t] = 0
    
    def notify_trade(self, trade):
        d = trade.data
        if not trade.isclosed:
            return
        self.log("P&L:  ${:.2f}".format(trade.pnlcomm))
        self.stoploss[d] = None
        self.resetBools(d)

    def log(self, txt, dp=False):
        if self.p.printLog or dp:
            date = self.datas[0].datetime.date(0)
            print("{}: {}".format(date, txt))

    def sizingCalc(self, capital, price):
        available = float(capital) * self.p.sizingPerc
        shares = round(available/price)
        return shares

    def awayThreshold(self, thresh, fast, close, ab):
        if ab == "Above":
            new = float(fast) * (1 + float(thresh))
            if float(close) > new:
                return True
            else:
                return False
        elif ab == "Below":
            new = float(fast) * (1 - float(thresh))
            if float(close) < new:
                return True
            else:
                return False
        else:
            self.log("awayThreshold:  We have a problem: {}".format(ab))

    def resetAway(self, reset, fast, close, ab):
        if ab == "Above":
            new = float(fast) * (1 + float(reset))
            if float(close) > new:
                return True
            else:
                return False
        elif ab == "Below":
            new = float(fast) * (1 - float(reset))
            if float(close) < new:
                return True
            else:
                return False

    def next(self):
        for i, d in enumerate(self.datas):
            #self.log("{} : ${:.2f}".format(d._name, d.close[0]))
            if self.getposition(d).size == 0: ##not in market
                sma = self.inds[d]['sma fast'][0]
                if self.inds[d]['sma fast'] > self.inds[d]['sma slow']: ##fast above slow ma
                    self.fastSlow[d] = "Above"
                    if self.distInRange[d]:
                        if d.close[0] < sma + (self.inds[d]['band diff'][0] * self.p.resetRange):
                            ##fell out of range
                            self.distInRange[d] = False
                        else:
                            ##still in range
                            if self.inds[d]['rsi sell'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.sell(data=d, size=numShares)
                                self.log("Sell {} shares of {}".format(numShares, d._name))
                                self.highStop[d] = sma + (self.inds[d]['band diff'][0] * self.p.stopRange)
                    else:
                        lowRange = self.inds[d]['band diff'][0] * self.p.rangeLow
                        highRange = self.inds[d]['band diff'][0] * self.p.rangeHigh
                        if d.close[0] > sma + lowRange and d.close < sma + highRange:
                            self.distInRange[d] = True
                            if self.inds[d]['rsi sell'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.sell(data=d, size=numShares)
                                self.log("Sell {} shares of {}".format(numShares, d._name))
                                self.highStop[d] = sma + (self.inds[d]['band diff'][0] * self.p.stopRange)                  

                elif self.inds[d]['sma fast'] < self.inds[d]['sma slow']: ##fast below slow sma
                    self.fastSlow[d] = "Below"
                    if self.distInRange[d]:
                        if d.close[0] > sma - (self.inds[d]['band diff'][0] * self.p.resetRange):
                            ##fell out of range
                            self.distInRange[d] = False
                        else:
                            ##still in range
                            if self.inds[d]['rsi buy'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.buy(data=d, size = numShares)
                                self.log("Buy {} shares of {}".format(numShares, d._name))
                                self.lowStop[d] = sma - (self.inds[d]['band diff'][0] * self.p.stopRange)
                    else:
                        lowRange = self.inds[d]['band diff'][0] * self.p.rangeLow
                        highRange = self.inds[d]['band diff'][0] * self.p.rangeHigh
                        if d.close[0] > sma - highRange and d.close[0] < sma - lowRange:
                            self.distInRange[d] = True
                            if self.inds[d]['rsi buy'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.buy(data=d, size = numShares)
                                self.log("Buy {} shares of {}".format(numShares, d._name))
                                self.lowStop[d] = sma - (self.inds[d]['band diff'][0] * self.p.stopRange)

            else:
                if self.ls[d] < 0: ##sold
                    if self.stoploss[d] is None:
                        self.stoploss[d] = self.close(data=d
                                                      ,exectype=bt.Order.Stop
                                                      ,price=self.highStop[d]
                                                      )
                        self.log("Buy stop created at ${:.2f} for {}".format(
                            self.highStop[d], d._name))
                    ##check for rsi cross
                    if self.inds[d]['rsi close short'].lines.cross[0] > 0:
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("RSI broke below for {}, close position".format(d._name))
                    ##check for number of sma crosses #starts above
                    elif self.smaCrosses[d] == 0:
                        ##check for sma cross below
                        if self.inds[d]['sma fast'] < self.inds[d]['sma slow']:
                            self.smaCrosses[d] = 1
                    elif self.smaCrosses[d] == 1:
                        if self.inds[d]['sma fast'] > self.inds[d]['sma slow']:
                            ##sma crossed back above, exit short position
                            self.order[d] = self.close(data=d)
                            self.cancel(self.stoploss[d])
                            self.log("Upward momentum with SMA crossing up for {}, close position".format(d._name))
                else:  ##bought
                    if self.stoploss[d] is None:
                        self.stoploss[d] = self.close(data=d
                                                      ,exectype=bt.Order.Stop
                                                      ,price=self.lowStop[d]
                                                      )
                        self.log("Sell stop created at ${:.2f} for {}".format(
                            self.lowStop[d], d._name))

                    ##check for rsi cross
                    if self.inds[d]['rsi close long'].lines.cross[0] > 0:
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("RSI broke above for {}, close position".format(d._name))
                    elif self.smaCrosses[d] == 0:
                        ##check for sma cross above
                        if self.inds[d]['sma fast'] > self.inds[d]['sma slow']:
                            self.smaCrosses[d] = 1
                    elif self.smaCrosses[d] == 1:
                        if self.inds[d]['sma fast'] < self.inds[d]['sma slow']:
                            ##sma crossed back below, exit long position
                            self.order[d] = self.close(data=d)
                            self.cancel(self.stoploss[d])
                            self.log("Downard momentum with SMA crossing down for {}, close position".format(d._name))
        #print(" ---------------------- ")                            
                        
    def stop(self):
        pnl = self.broker.getvalue() - self.startCash
        self.log("\n\n ------- Final Analysis ------- ")
        print("Ending Value: ${:.2f}\nP&L:  ${:.2f}\n".format(self.broker.getvalue(), pnl))
        
        


class BOLL_RSI(bt.Strategy):
    params = dict(
        sizingPerc = .01 ##percent of fund used per trade
        ,rsiThresh = 0 ##50 +/- this to get buy/sell signals
        ,printLog = True
        ,rsiPeriod = 14 ##num days for rsi calc
        ,bollPeriod = 20 ##num days for boll calc
        ,bollDev = 2.0 ##standard deviation factor for boll calc
        ,rsiType = True ##true = simple, false = exponential
        )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.stoploss = None
        self.startCash = None
        self.aboveMid = False ##indicator for crossing above mid boll
        self.belowMid = False ##indicator for crossing below mid boll
        self.ls = 0 ##1 = long, -1 = short
        self.highStop = 0.0
        self.lowStop = 0.0
        if self.p.rsiType:
            self.RSI = bt.ind.RSI_SMA(period = self.p.rsiPeriod)
        else:
            self.RSI = bt.ind.RSI_EMA(period = self.p.rsiPeriod)
        self.bollBands = bt.ind.BBands(period = self.p.bollPeriod, devfactor = self.p.bollDev)
        self.bollCrossUp = bt.ind.CrossUp(self.dataclose, self.bollBands.lines.mid, plot=False)
        self.bollCrossDown = bt.ind.CrossDown(self.dataclose, self.bollBands.lines.mid, plot=False)
        self.rsiBuy = bt.ind.CrossUp(self.RSI.lines.rsi, 50 + self.p.rsiThresh, plot=False)
        self.rsiSell = bt.ind.CrossDown(self.RSI.lines.rsi, 50 - self.p.rsiThresh, plot=False)
        self.bottomCross = bt.ind.CrossDown(self.dataclose, self.bollBands.bot, plot=False)
        self.topCross = bt.ind.CrossUp(self.dataclose, self.bollBands.top, plot=False)
        self.closeLong = bt.ind.CrossDown(self.RSI.lines.rsi, 50, plot=False)
        self.closeShort = bt.ind.CrossUp(self.RSI.lines.rsi, 50, plot=False)

    def start(self):
        self.startCash = self.broker.getvalue()
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("Paid ${:.2f} on {}".format(order.executed.price, order.executed.size))
            elif order.issell():
                self.log("Sold {} at ${:.2f}".format(order.executed.size, order.executed.price))
        elif order.status in [order.Canceled]:
            self.log('Order Canceled')
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order rejected or margin issue')
        self.order = None     
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log("P&L:  ${:.2f}".format(trade.pnlcomm))
        self.stoploss = None ##remove stop loss orders

    def log(self, txt):
        if self.p.printLog:
            date = self.datas[0].datetime.date(0)
            print("{}: {}".format(date, txt))

    def sizingCalc(self, capital, price):
        available = float(capital) * self.p.sizingPerc
        shares = round(available/price)
        return shares

    def next(self):
        '''
        self.log("\nBands:\nTop: {:.2f}\nMid: {:.2f}\nLow: {:.2f}\n------\nRSI: {:.2f}\nClose: {:.2f}\nOpen:{:.2f}\n".format(
            self.bollBands.lines.top[0]
            ,self.bollBands.lines.mid[0]
            ,self.bollBands.lines.bot[0]
            ,self.RSI.lines.rsi[0]
            ,self.dataclose[0]
            ,self.datas[0].open[0]
            ))
        '''
        if not self.position:  ##not in market
            if self.bollCrossUp:
                #self.log("Crossed above")
                self.belowMid = False
                self.aboveMid = True
            elif self.bollCrossDown:
                #self.log("Crossed below")
                self.belowMid = True
                self.aboveMid = False
            '''
            else:
                self.log("No crossing")
            '''
            if self.rsiBuy and self.aboveMid:
                ##RSI above threshold and has crossed above midpoint and still there
                numShares = self.sizingCalc(self.broker.getvalue(), self.dataclose[0])
                ##buy order
                self.order = self.buy(size = numShares)
                self.log("Buy {} shares".format(numShares))
                self.ls = 1
                ##stop order
                self.lowStop = self.bollBands.lines.bot[0]
                self.stoploss = self.close(exectype = bt.Order.Stop
                                       ,price = self.lowStop
                                       )
                self.log("Sell stop created at {:.2f}".format(
                self.lowStop))
            elif self.rsiSell and self.belowMid:
                ##RSI below threshold and has crossed below mid and still there
                numShares = self.sizingCalc(self.broker.getvalue(), self.dataclose[0])
                ##sell order
                self.order = self.sell(size = numShares)
                self.log("Sell {} shares".format(numShares))
                self.ls = -1
                ##stop order
                self.highStop = self.bollBands.lines.top[0]
                self.stoploss = self.close(exectype = bt.Order.Stop
                                           ,price = self.highStop
                                           )
                self.log("Buy stop created at {:.2f}".format(
                    self.highStop))
        elif self.ls > 0 and self.bottomCross:
            ##long and cross bottom band
            self.order = self.close()
            #self.log("Lower band crossed, close position.")
            self.cancel(self.stoploss)
            ##reset crossover stats
            self.belowMid = False
            self.aboveMid = False
        elif self.ls > 0 and self.closeLong:
            ##long and rsi below threshold
            self.order = self.close()
            #self.log("RSI broke below, close position.")
            self.cancel(self.stoploss)
            ##reset crossover stats
            self.belowMid = False
            self.aboveMid = False
        elif self.ls < 0 and self.topCross:
            ##short and cross above top band
            self.order = self.close()
            #self.log("Upper band crossed, close position")
            self.cancel(self.stoploss)
            ##reset crossover stats
            self.belowMid = False
            self.aboveMid = False
        elif self.ls < 0 and self.closeShort:
            ##short and rsi above threshold
            self.order = self.close()
            #self.log("RSI broke above, close position.")
            self.cancel(self.stoploss)
            ##reset crossover stats
            self.belowMid = False
            self.aboveMid = False




class SmaCross(bt.Strategy):
    '''
    Buy when 10 day MA crosses above 30 MA
    Close when breaks back below
    '''
    params = dict(
        pfast = 10 # period for the fast moving average
        ,pslow = 30  # period for the slow moving average
        ,sizingPerc = .01 # percent of fund value to use per trade
        ,trailPerc = .025 # percent of price to use for stop losses
        ,printLog = True
        )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.stoploss = None
        self.buyPrice = None
        self.startCash = None
        sma1 = bt.ind.SMA(period = self.p.pfast)
        sma2 = bt.ind.SMA(period = self.p.pslow)
        self.crossover = bt.ind.CrossOver(sma1, sma2) #crossover signal

    def start(self):
        self.startCash = self.broker.getvalue()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("Paid ${:.2f} on {}".format(order.executed.price, order.executed.size))
                self.buyPrice = order.executed.price
            elif order.issell():
                self.log("Sold {} at ${:.2f}".format(order.executed.size, order.executed.price))
                self.buyPrice = None
        elif order.status in [order.Canceled]:
            self.log('Order Canceled')
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order rejected or margin issue')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log("P&L:  ${:.2f}".format(trade.pnlcomm))
        self.cancel(self.stoploss) # cancel stop loss order
        self.stoploss = None

    def log(self, txt):
        if self.p.printLog:
            date = self.datas[0].datetime.date(0)
            print("{}: {}".format(date, txt))
        
    def sizingCalc(self, capital, price):
        available = float(capital) * self.p.sizingPerc
        shares = round(available/price)
        return shares

    def next(self):
        if not self.position: # not in market
            if self.crossover > 0:  # fast crosses slow to the upside
                numShares = self.sizingCalc(self.broker.getvalue(), self.dataclose[0])
                self.order = self.buy(size = numShares)  # enter long position
                self.log("Buy {} shares".format(numShares))
        elif self.crossover < 0: # in market and crosses to downside
                self.order = self.close()  # close long position
                self.log("Close Position")
                self.cancel(self.stoploss)
        elif self.stoploss is None:
            stopLoss = self.buyPrice * (1.0 - self.p.trailPerc) # set stop price
            self.stoploss = self.close(exectype = bt.Order.Stop # create stop order
                                    ,price = stopLoss
                                    )
            self.log("Trailing stop created at {:.2f}".format(stopLoss))
            

    def stop(self):
        pnl = self.broker.getvalue() - self.startCash
        self.log("Ending Value: ${:.2f}\nP&L:  ${:.2f}".format(
            self.broker.getvalue()
            ,pnl))




class Dartboard(bt.Strategy):
    '''
    Trade based on randomness
    Buy/Sell based on randomness
    Close based on randomness
    '''
    params = dict(
        ptrade = 0.2 # prob of making trade each day
        ,pbuy = 0.5 # prob of buying if trade maded
        ,sizingPerc = 0.05 # percent of fund value to use per trade
        ,printLog = True
        )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyPrice = None
        self.startCash = None

    def start(self):
        self.startCash = self.broker.getvalue()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("Paid ${:.2f} on {}".format(order.executed.price, order.executed.size))
                self.buyPrice = order.executed.price
            elif order.issell():
                self.log("Sold {} at ${:.2f}".format(order.executed.size, order.executed.price))
                self.buyPrice = None
        elif order.status in [order.Canceled]:
            self.log('Order Canceled')
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order rejected or margin issue')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log("P&L:  ${:.2f}".format(trade.pnlcomm))

    def log(self, txt):
        if self.p.printLog:
            date = self.datas[0].datetime.date(0)
            print("{}: {}".format(date, txt))

    def sizingCalc(self, capital, price):
        available = float(capital) * self.p.sizingPerc
        shares = round(available/price)
        return shares        

    def next(self):
        tradeBool = random.random()
        if not self.position: # if not in market
            if tradeBool <= self.p.ptrade:
                buyBool = random.random()
                numShares = self.sizingCalc(self.broker.getvalue(), self.dataclose)
                if buyBool <= self.p.pbuy:
                    self.buy(size = numShares)
                else:
                    self.sell(size = numShares)
            else:
                pass
        else: # in market
            if tradeBool <= self.p.ptrade:
                self.close()

    def stop(self):
        pnl = self.broker.getvalue() - self.startCash
        self.log("Ending Value: ${:.2f}\nP&L:  ${:.2f}".format(
            self.broker.getvalue()
            ,pnl))





class Hold(bt.Strategy):
    '''
    Buy as much as possible at start and hold til end
    '''
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.startCash = None
        self.order = None
        self.buyPrice = None

    def start(self):
        self.startCash = self.broker.getvalue()

    def notify_order(self, order):
        if order.status in [order.Submitted, order. Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("Paid ${:.2f} on {}".format(
                    order.executed.price
                    ,order.executed.size
                    ))
                self.buyPrice = order.executed.price
            if order.issell():
                self.log("Houston, we have a problem")

    def log(self, txt):
        date = self.datas[0].datetime.date(0)
        print("{}: {}".format(date, txt))

    def sizingCalc(self, capital, price):
        shares = int(capital/price)
        return shares

    def next(self):
        if not self.position: #not in market
            numShares = self.sizingCalc(self.broker.getvalue(), self.dataclose)
            self.buy(size = numShares)
        else:
            pass

    def stop(self):
        pnl = self.broker.getvalue() - self.startCash
        self.log("Ending Value: ${:.2f}\nP&L:  ${:.2f}".format(
            self.broker.getvalue()
            ,pnl))



## ----------- LIVE MODELS -------------- ##
class live_model_1(bt.Strategy):
    '''
    SMA mean reverting
    '''
    params = dict(
        sizingPerc = 0.01
        ,fastSMA = 20
        ,slowSMA = 100
        ,bollStd = 1
        ,rangeLow = 1.75
        ,rangeHigh = 2.25
        ,stopRange = 2.5
        ,resetRange = 1.5
        ,rsiBound = 20
        ,rsiClose = 5
        ,rsiPeriod = 14
        ,printLog = True
        )

    def __init__(self):
        self.startCash = None
        self.order = {}
        self.stoploss = {}
        self.fastSlow = {}
        self.smaCrosses = {}
        self.distInRange = {}
        self.revertEarly = {}
        self.rsiCross = {}
        self.ls = {}
        self.highStop = {}
        self.lowStop = {}
        self.inds = {}
        for i, d in enumerate(self.datas):
            self.order[d] = None
            self.stoploss[d] = None
            self.fastSlow[d] = None
            self.smaCrosses[d] = 0
            self.distInRange[d] = False
            self.revertEarly[d] = False
            self.rsiCross[d] = None
            self.ls[d] = 0
            self.highStop[d] = 0
            self.lowStop[d] = 0
            self.inds[d] = {}
            self.inds[d]['sma fast'] = bt.ind.SMA(d.close, period = self.p.fastSMA).lines.sma
            self.inds[d]['sma slow'] = bt.ind.SMA(d.close, period = self.p.slowSMA).lines.sma
            self.inds[d]['bands'] = bt.ind.BBands(d.close, period = self.p.fastSMA, devfactor = self.p.bollStd, plot=False)
            self.inds[d]['band diff'] = self.inds[d]['bands'].lines.top - self.inds[d]['bands'].lines.mid
            self.inds[d]['rsi'] = bt.ind.RSI_SMA(d.close, period = self.p.rsiPeriod)
            self.inds[d]['rsi buy'] = bt.ind.CrossDown(self.inds[d]['rsi'].lines.rsi, 50 - self.p.rsiBound, plot=False)
            self.inds[d]['rsi sell'] = bt.ind.CrossUp(self.inds[d]['rsi'].lines.rsi, 50 + self.p.rsiBound, plot=False)
            self.inds[d]['rsi close long'] = bt.ind.CrossUp(self.inds[d]['rsi'].lines.rsi, 50 + self.p.rsiClose, plot=False)
            self.inds[d]['rsi close short'] = bt.ind.CrossDown(self.inds[d]['rsi'].lines.rsi, 50 - self.p.rsiClose, plot=False)

    def start(self):
        self.startCash = self.broker.getvalue()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            d = order.data
            if order.isbuy():
                bs = "Bought"
                self.ls[d] = 1
            else:
                bs = "Sold"
                self.ls[d] = -1
            self.log("{} {} shares of {} for ${:.2f}".format(
                bs
                ,order.executed.size
                ,d._name
                ,order.executed.price))
        elif order.status in [order.Canceled]:
            self.log('Order Canceled for {}'.format(order.data._name))
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order rejected or margin issue')

    def resetBools(self, t):
        self.fastSlow[t] = None
        self.smaCrosses[t] = 0
        self.distInRange[t] = False
        self.revertEarly[t] = False
        self.rsiCross[t] = None
        self.ls[t] = 0
    
    def notify_trade(self, trade):
        d = trade.data
        if not trade.isclosed:
            return
        self.stoploss[d] = None
        self.resetBools(d)

    def log(self, txt, dp=False):
        if self.p.printLog or dp:
            date = self.datas[0].datetime.date(0)
            print("{}: {}".format(date, txt))

    def sizingCalc(self, capital, price):
        available = float(capital) * self.p.sizingPerc
        shares = round(available/price)
        return shares

    def awayThreshold(self, thresh, fast, close, ab):
        if ab == "Above":
            new = float(fast) * (1 + float(thresh))
            if float(close) > new:
                return True
            else:
                return False
        elif ab == "Below":
            new = float(fast) * (1 - float(thresh))
            if float(close) < new:
                return True
            else:
                return False
        else:
            self.log("awayThreshold:  We have a problem: {}".format(ab))

    def resetAway(self, reset, fast, close, ab):
        if ab == "Above":
            new = float(fast) * (1 + float(reset))
            if float(close) > new:
                return True
            else:
                return False
        elif ab == "Below":
            new = float(fast) * (1 - float(reset))
            if float(close) < new:
                return True
            else:
                return False

    def next(self):
        for i, d in enumerate(self.datas):
            if self.getposition(d).size == 0: ##not in market
                sma = self.inds[d]['sma fast'][0]
                if self.inds[d]['sma fast'][0] > self.inds[d]['sma slow'][0]: ##fast above slow ma
                    self.fastSlow[d] = "Above"
                    if self.distInRange[d]:
                        if d.close[0] < sma + (self.inds[d]['band diff'][0] * self.p.resetRange):
                            ##fell out of range
                            self.distInRange[d] = False
                        else:
                            ##still in range
                            if self.inds[d]['rsi sell'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.sell(data=d, size=numShares)
                                self.log("Sell {} shares of {}".format(numShares, d._name))
                                self.highStop[d] = sma + (self.inds[d]['band diff'][0] * self.p.stopRange)
                    else:
                        lowRange = self.inds[d]['band diff'][0] * self.p.rangeLow
                        highRange = self.inds[d]['band diff'][0] * self.p.rangeHigh
                        if d.close[0] > sma + lowRange and d.close < sma + highRange:
                            self.distInRange[d] = True
                            if self.inds[d]['rsi sell'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.sell(data=d, size=numShares)
                                self.log("Sell {} shares of {}".format(numShares, d._name))
                                self.highStop[d] = sma + (self.inds[d]['band diff'][0] * self.p.stopRange)                  

                elif self.inds[d]['sma fast'][0] < self.inds[d]['sma slow'][0]: ##fast below slow sma
                    self.fastSlow[d] = "Below"
                    if self.distInRange[d]:
                        if d.close[0] > sma - (self.inds[d]['band diff'][0] * self.p.resetRange):
                            ##fell out of range
                            self.distInRange[d] = False
                        else:
                            ##still in range
                            if self.inds[d]['rsi buy'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.buy(data=d, size = numShares)
                                self.log("Buy {} shares of {}".format(numShares, d._name))
                                self.lowStop[d] = sma - (self.inds[d]['band diff'][0] * self.p.stopRange)
                    else:
                        lowRange = self.inds[d]['band diff'][0] * self.p.rangeLow
                        highRange = self.inds[d]['band diff'][0] * self.p.rangeHigh
                        if d.close[0] > sma - highRange and d.close[0] < sma - lowRange:
                            self.distInRange[d] = True
                            if self.inds[d]['rsi buy'].lines.cross[0] > 0:
                                numShares = self.sizingCalc(self.broker.getvalue(), d.close[0])
                                self.order[d] = self.buy(data=d, size = numShares)
                                self.log("Buy {} shares of {}".format(numShares, d._name))
                                self.lowStop[d] = sma - (self.inds[d]['band diff'][0] * self.p.stopRange)

            else:
                if self.ls[d] < 0: ##sold
                    if self.stoploss[d] is None:
                        self.stoploss[d] = self.close(data=d
                                                      ,exectype=bt.Order.Stop
                                                      ,price=self.highStop[d]
                                                      )
                        self.log("Buy stop created at ${:.2f} for {}".format(
                            self.highStop[d], d._name))
                    ##check for rsi cross
                    if self.inds[d]['rsi close short'].lines.cross[0] > 0:
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("RSI broke below for {}, close position".format(d._name))
                    ##check for number of sma crosses #starts above
                    elif self.smaCrosses[d] == 0:
                        ##check for sma cross below
                        if self.inds[d]['sma fast'] < self.inds[d]['sma slow']:
                            self.smaCrosses[d] = 1
                    elif self.smaCrosses[d] == 1:
                        if self.inds[d]['sma fast'] > self.inds[d]['sma slow']:
                            ##sma crossed back above, exit short position
                            self.order[d] = self.close(data=d)
                            self.cancel(self.stoploss[d])
                            self.log("Upward momentum with SMA crossing up for {}, close position".format(d._name))
                else:  ##bought
                    if self.stoploss[d] is None:
                        self.stoploss[d] = self.close(data=d
                                                      ,exectype=bt.Order.Stop
                                                      ,price=self.lowStop[d]
                                                      )
                        self.log("Sell stop created at ${:.2f} for {}".format(
                            self.lowStop[d], d._name))

                    ##check for rsi cross
                    if self.inds[d]['rsi close long'].lines.cross[0] > 0:
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("RSI broke above for {}, close position".format(d._name))
                    elif self.smaCrosses[d] == 0:
                        ##check for sma cross above
                        if self.inds[d]['sma fast'] > self.inds[d]['sma slow']:
                            self.smaCrosses[d] = 1
                    elif self.smaCrosses[d] == 1:
                        if self.inds[d]['sma fast'] < self.inds[d]['sma slow']:
                            ##sma crossed back below, exit long position
                            self.order[d] = self.close(data=d)
                            self.cancel(self.stoploss[d])
                            self.log("Downard momentum with SMA crossing down for {}, close position".format(d._name))                          
                        
    def stop(self):
        pnl = self.broker.getvalue() - self.startCash
        self.log("\n ------- Final Day ------- ")
        



        
class live_model_1_rf(bt.Strategy):
    '''
    SMA mean reverting
    '''
    params = dict(
        sizingPerc = 0.01
        ,fastSMA = 20
        ,slowSMA = 100
        ,bollStd = 1
        ,rangeLow = 1.75
        ,rangeHigh = 2.25
        ,stopRange = 2.5
        ,resetRange = 1.5
        ,rsiBound = 20
        ,rsiClose = 5
        ,rsiPeriod = 14
        ,profitTake = 0.1
        ,mod = None
        ,printLog = True
        )

    def __init__(self):
        self.startCash = None
        self.order = {}
        self.stoploss = {}
        self.fastSlow = {}
        self.smaCrosses = {}
        self.distInRange = {}
        self.revertEarly = {}
        self.rsiCross = {}
        self.ls = {}
        self.highStop = {}
        self.lowStop = {}
        self.price = {}
        self.inds = {}     
        for i, d in enumerate(self.datas):
            self.order[d] = None
            self.stoploss[d] = None
            self.fastSlow[d] = None
            self.smaCrosses[d] = 0
            self.distInRange[d] = False
            self.revertEarly[d] = False
            self.rsiCross[d] = None
            self.ls[d] = 0
            self.highStop[d] = 0
            self.lowStop[d] = 0
            self.price[d] = 0
            self.inds[d] = {}
            self.inds[d]['sma fast'] = bt.ind.SMA(d.close, period = self.p.fastSMA).lines.sma
            self.inds[d]['sma slow'] = bt.ind.SMA(d.close, period = self.p.slowSMA).lines.sma
            self.inds[d]['bands'] = bt.ind.BBands(d.close, period = self.p.fastSMA, devfactor = self.p.bollStd, plot=False)
            self.inds[d]['band diff'] = self.inds[d]['bands'].lines.top - self.inds[d]['bands'].lines.mid
            self.inds[d]['rsi'] = bt.ind.RSI_SMA(d.close, period = self.p.rsiPeriod)
            self.inds[d]['rsi buy'] = bt.ind.CrossDown(self.inds[d]['rsi'].lines.rsi, 50 - self.p.rsiBound, plot=False)
            self.inds[d]['rsi sell'] = bt.ind.CrossUp(self.inds[d]['rsi'].lines.rsi, 50 + self.p.rsiBound, plot=False)
            self.inds[d]['rsi close long'] = bt.ind.CrossUp(self.inds[d]['rsi'].lines.rsi, 50 + self.p.rsiClose, plot=False)
            self.inds[d]['rsi close short'] = bt.ind.CrossDown(self.inds[d]['rsi'].lines.rsi, 50 - self.p.rsiClose, plot=False)        

    def start(self):
        self.startCash = self.broker.getvalue()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            d = order.data
            if order.isbuy():
                bs = "Bought"
                self.ls[d] = 1
            else:
                bs = "Sold"
                self.ls[d] = -1
            self.log("{} {} shares of {} for ${:.2f}".format(
                bs
                ,order.executed.size
                ,d._name
                ,order.executed.price))
            self.price[d] = order.executed.price
        elif order.status in [order.Canceled]:
            self.log('Order Canceled for {}'.format(order.data._name))
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order rejected or margin issue')         
    
    def notify_trade(self, trade):
        d = trade.data
        if not trade.isclosed:
            return
        self.cancel(self.stoploss[d])
        self.stoploss[d] = None
        self.resetBools(d)

    def resetBools(self, t):
        self.fastSlow[t] = None
        self.smaCrosses[t] = 0
        self.distInRange[t] = False
        self.revertEarly[t] = False
        self.rsiCross[t] = None
        self.ls[t] = 0
        self.price[t] = 0

    def log(self, txt, dp=False):
        if self.p.printLog or dp:
            date = self.datas[0].datetime.date(0)
            print("{}: {}".format(date, txt))

    def sizingCalc(self, capital, price, half=False):
        available = float(capital) * self.p.sizingPerc
        if half:
            inter = available/price
            shares = round(inter/2.0)
        else:
            shares = round(available/price)
        return shares

    def awayThreshold(self, thresh, fast, close, ab):
        if ab == "Above":
            new = float(fast) * (1 + float(thresh))
            if float(close) > new:
                return True
            else:
                return False
        elif ab == "Below":
            new = float(fast) * (1 - float(thresh))
            if float(close) < new:
                return True
            else:
                return False
        else:
            self.log("awayThreshold:  We have a problem: {}".format(ab))

    def resetAway(self, reset, fast, close, ab):
        if ab == "Above":
            new = float(fast) * (1 + float(reset))
            if float(close) > new:
                return True
            else:
                return False
        elif ab == "Below":
            new = float(fast) * (1 - float(reset))
            if float(close) < new:
                return True
            else:
                return False

    def next(self):
        for i, d in enumerate(self.datas):
            fast = self.inds[d]['sma fast'][0]
            slow = self.inds[d]['sma slow'][0]
            bollWidth = self.inds[d]['band diff'][0]
            rsi = self.inds[d]['rsi'][0]
            close = d.close[0]
            ticker = d._name
            sma_diff_norm = abs(fast-slow)/close
            boll_diff_norm = bollWidth/close
            rsi_extra = rsi - (50 + self.p.rsiBound)
            
            
            if self.getposition(d).size == 0: ##not in market
                if fast > slow: ##fast above slow ma
                    self.fastSlow[d] = "Above"
                    if self.distInRange[d]:
                        if close < fast + (bollWidth * self.p.resetRange):
                            ##fell out of range
                            self.distInRange[d] = False
                        else:
                            ##still in range
                            if self.inds[d]['rsi sell'].lines.cross[0] > 0:
                                wl = self.p.mod.predict(pd.DataFrame([[sma_diff_norm, boll_diff_norm, rsi_extra]]))[0]
                                if wl == 1:
                                    self.log('Predicting winner for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close)
                                else:
                                    self.log('Predicting loser for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close, half=True)
                                self.order[d] = self.sell(data=d, size=numShares)
                                self.log("Sell {} shares of {}".format(numShares, ticker))
                    else:
                        lowRange = bollWidth * self.p.rangeLow
                        highRange = bollWidth * self.p.rangeHigh
                        if close > (fast + lowRange) and close < (fast + highRange):
                            self.distInRange[d] = True
                            if self.inds[d]['rsi sell'].lines.cross[0] > 0:
                                wl = self.p.mod.predict(pd.DataFrame([[sma_diff_norm, boll_diff_norm, rsi_extra]]))[0]
                                if wl == 1:
                                    self.log('Predicting winner for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close)
                                else:
                                    self.log('Predicting loser for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close, half=True)
                                self.order[d] = self.sell(data=d, size=numShares)
                                self.log("Sell {} shares of {}".format(numShares, ticker))

                elif fast < slow: ##fast below slow sma
                    self.fastSlow[d] = "Below"
                    if self.distInRange[d]:
                        if close > fast - (bollWidth * self.p.resetRange):
                            ##fell out of range
                            self.distInRange[d] = False
                        else:
                            ##still in range
                            if self.inds[d]['rsi buy'].lines.cross[0] > 0:
                                wl = self.p.mod.predict(pd.DataFrame([[sma_diff_norm, boll_diff_norm, rsi_extra]]))[0]
                                if wl == 1:
                                    self.log('Predicting winner for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close)
                                else:
                                    self.log('Predicting loser for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close, half=True)
                                self.order[d] = self.buy(data=d, size = numShares)
                                self.log("Buy {} shares of {}".format(numShares, ticker))
                    else:
                        lowRange = bollWidth * self.p.rangeLow
                        highRange = bollWidth * self.p.rangeHigh
                        if close > (fast - highRange) and close < (fast - lowRange):
                            self.distInRange[d] = True
                            if self.inds[d]['rsi buy'].lines.cross[0] > 0:
                                wl = self.p.mod.predict(pd.DataFrame([[sma_diff_norm, boll_diff_norm, rsi_extra]]))[0]
                                if wl == 1:
                                    self.log('Predicting winner for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close)
                                else:
                                    self.log('Predicting loser for {}'.format(ticker))
                                    numShares = self.sizingCalc(self.broker.getvalue(), close, half=True)
                                self.order[d] = self.buy(data=d, size = numShares)
                                self.log("Buy {} shares of {}".format(numShares, ticker))

            else:
                if self.ls[d] < 0: ##sold
                    if self.stoploss[d] is None:
                        self.highStop[d] = fast + (bollWidth * self.p.stopRange)
                        self.stoploss[d] = self.close(data=d
                                                      ,exectype=bt.Order.Stop
                                                      ,price=self.highStop[d]
                                                      )
                        self.log("Buy stop created at ${:.2f} for {}".format(
                            self.highStop[d], ticker))
                    ##check exits
                    ##take profit
                    if close < self.price[d] * (1-self.p.profitTake):
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("Take {}% profit and close {}".format(self.p.profitTake * 100.0, ticker))
                    ##rsi cross
                    elif self.inds[d]['rsi close short'].lines.cross[0] > 0:
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("RSI broke below for {}, close position".format(ticker))
                    ##check for number of sma crosses #starts above
                    elif self.smaCrosses[d] == 0:
                        ##check for sma cross below
                        if fast < slow:
                            self.smaCrosses[d] = 1
                    elif self.smaCrosses[d] == 1:
                        if fast > slow:
                            ##sma crossed back above, exit short position
                            self.order[d] = self.close(data=d)
                            self.cancel(self.stoploss[d])
                            self.log("Upward momentum with SMA crossing up for {}, close position".format(ticker))                                  
                else:  ##bought
                    if self.stoploss[d] is None:
                        self.lowStop[d] = fast - (bollWidth * self.p.stopRange)
                        self.stoploss[d] = self.close(data=d
                                                      ,exectype=bt.Order.Stop
                                                      ,price=self.lowStop[d]
                                                      )
                        self.log("Sell stop created at ${:.2f} for {}".format(self.lowStop[d], ticker))
                    ##check for exits
                    ##profit take
                    if close > self.price[d] * (1+self.p.profitTake):
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("Take {}% profit and close {}".format(self.p.profitTake*100.0, ticker))
                    ##rsi cross
                    elif self.inds[d]['rsi close long'].lines.cross[0] > 0:
                        self.order[d] = self.close(data=d)
                        self.cancel(self.stoploss[d])
                        self.log("RSI broke above for {}, close position".format(ticker))
                    ##check for number of sma crosses #starts below
                    elif self.smaCrosses[d] == 0:
                        ##check for sma cross above
                        if fast > slow:
                            self.smaCrosses[d] = 1
                    elif self.smaCrosses[d] == 1:
                        if fast < slow:
                            ##sma crossed back below, exit long position
                            self.order[d] = self.close(data=d)
                            self.cancel(self.stoploss[d])
                            self.log("Downard momentum with SMA crossing down for {}, close position".format(ticker))    
                       
    def stop(self):
        pnl = self.broker.getvalue() - self.startCash
        print("\n\n ------- Final Analysis ------- ")
        print("Ending Value: ${:.2f}\nP&L:  ${:.2f}\n".format(self.broker.getvalue(), pnl))

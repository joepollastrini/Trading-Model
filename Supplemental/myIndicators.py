import backtrader as bt


class MoneyFlow(bt.Indicator):
    lines = ('mfi',)
    params = dict(period=14)

    alias = ('MoneyFlowIndicator',)

    def __init__(self):
        tprice = (self.data.close + self.data.low + self.data.high) / 3.0
        mfraw = tprice * self.data.volume

        flowpos = bt.ind.SumN(mfraw * (tprice > tprice(-1)), period=self.p.period)
        flowneg = bt.ind.SumN(mfraw * (tprice < tprice(-1)), period=self.p.period)

        mfiratio = bt.ind.DivByZero(flowpos, flowneg, zero=100.0)
        self.l.mfi = 100.0 - 100.0 / (1.0 + mfiratio)



class ChaikinMoneyFlow(bt.Indicator):
    lines = ('mfi',)
    params = (
        ('period', 20),
        )

    plotlines = dict(
        money_flow=dict(
            _name='CMF',
            color='green',
            alpha=0.50
        )
    )

    def __init__(self):
        # Let the indicator get enough data
        self.addminperiod(self.p.period)

        # Plot horizontal Line
        self.plotinfo.plotyhlines = [0]

        # Aliases to avoid long lines
        c = self.data.close
        h = self.data.high
        l = self.data.low
        v = self.data.volume
        
        self.data.ad = bt.If(bt.Or(bt.And(c == h, c == l), h == l), 0, ((2*c-l-h)/(h-l))*v)
        self.lines.mfi = bt.indicators.SumN(self.data.ad, period=self.p.period) / bt.indicators.SumN(self.data.volume, period=self.p.period)



class percAway(bt.Indicator):
    lines = ('perc',)

    params = dict(
        sma = 1
        ,close = 1
        )

    plotlines = dict(
        percAway = dict(
            _name='Percent Away'
            ,color = 'black'
            ))

    def __init__(self):
        perc = (self.p.close/self.p.sma) - 1.0
        self.lines.perc = perc
        

class OBV(bt.Indicator):
    lines = ('obv',)
    params = (
      ('length', 12),
    )

    plotlines = dict(
        obv=dict(
            _name='OBV',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):

        # Plot a horizontal Line
        self.plotinfo.plotyhlines = [0]
            

    def nextstart(self):
        # Create some aliases
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = v[0]
        elif c[0] < c[-1]: 
            obv[0] = -v[0] 
        else: 
            obv[0] = 0 
                
    def next(self): 
        # Aliases to avoid long lines 
        c = self.data.close 
        v = self.data.volume 
        obv = self.lines.obv 
        
        if c[0] > c[-1]:
            obv[0] = obv[-1] + v[0]
        elif c[0] < c[-1]:
            obv[0] = obv[-1] - v[0]
        else:
            obv[0] = obv[-1]          






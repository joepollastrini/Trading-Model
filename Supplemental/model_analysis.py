'''
Used to analyze the model after its run
'''
import backtrader as bt
import datetime

def main_analysis(sharp, sqn, ret):
    '''
    Takes bt.analyzer objects as arguments
    return: string with all analysis
    '''
    if sharp == None:
        sharpText = ""
    else:
        sharpText = "Sharpe Ratio:  {:.2f}\n".format(
            sharp['sharperatio']
            )
    if sqn == None:
        sqnText = ""
    else:
        sqnText = "SQN:  {}\n{} total trades\n".format(
            sqn['sqn']
            ,sqn['trades']
            )
    if ret == None:
        retText = ""
    else:
        retText = "Normalized Return:  {:.2f}%\nTotal Return:  {:.2f}\nAverage Return:  {:.2f}\n".format(
            ret['rnorm100']
            ,ret['rtot']
            ,ret['ravg']
            )
    #final printing return
    header = " ------ Quick Glance ------ \n"
    footer = " -------------------------- \n"
    if sharp == None and sqn == None and ret == None:
        info = "No analysis to be done"
        return "{}{}{}".format(
            header
            ,info
            ,footer
            )
    else:
        return "{}{}{}{}{}".format(
            header
            ,sharpText
            ,sqnText
            ,retText
            ,footer
            )


def trade_analysis(analyzer, total=True, winLoss=True, hold=True, longShort=False, streaks=False):
    if total == False:
        return ""
    else:
        closed = analyzer['total']['closed']
        pnlDict = analyzer['pnl']
        net = pnlDict['net']['total']
        avg = pnlDict['net']['average']
        totalText = "{} Trades\nP&L:  ${:.2f}\nAverage:  ${:.2f}\n\n".format(
            closed
            ,net
            ,avg
            )
    if winLoss:
        winDict = analyzer['won']
        wins = winDict['total']
        pnlWins = winDict['pnl']['total']
        winAvg = winDict['pnl']['average']
        losses = closed - wins
        pnlLosses = net - pnlWins
        lossAvg = analyzer['lost']['pnl']['average']
        winRate = (float(wins)/float(closed)) * 100.0
        winText = "Win Rate:  {:.1f}% / ({})\nGain:  ${:.2f}\nAvg. Gain:  ${:.2f}\n".format(
            winRate
            ,wins
            ,pnlWins
            ,winAvg
            )
        lossText = "------------\nLosses:  {}\nAvg. Loss:  ${:.2f}\n".format(
            losses
            ,lossAvg
            )
        winLossText = "{}{}\n".format(winText, lossText)
    else:
        winLossText = ""
    if hold:
        holdDict = analyzer['len']
        avgHold = holdDict['average']
        winHold = holdDict['won']['average']
        lossHold = holdDict['lost']['average']
        holdText = "Days Held:\nAverage:  {:.1f}\nWin:  {:.1f}\nLoss:  {:.1f}\n".format(
            avgHold
            ,winHold
            ,lossHold
            )
    else:
        holdText = ""
    if longShort:
        longShortText = "Haven't done anything here yet"
    else:
        longShortText = ""
    if streaks:
        streakText = "Haven't done anything with streaks yet"
    else:
        streakText = ""
    header = " ------ Trade Analysis ------ \n"
    footer = " ---------------------------- \n"
    allText = "{}{}{}{}{}".format(
        totalText
        ,winLossText
        ,holdText
        ,longShortText
        ,streakText
        )
    return "{}{}{}".format(header, allText, footer)
        
        
        
    
    








import backtrader as bt
import datetime as dt
import argparse
import DBconnect
import Const
from collections import deque
from datetime import timedelta

database = None
# trade_type  0 is short, 1 is long
trade_type, NumberOfWins, NumberOfLoss, buytime, buyprice, total_trades, sum_profit, opencode = (0,) * 8
shortposSize, longposSize = 2, 0
# RunningMode = Const.AnalysisMode  # 0 is analysis mode, 1 is execution mode
RunningMode = Const.AnalysisMode
StockNo = 'MTX00'
StratName = 'SampleShort'


class TheStrategy(bt.Strategy):
    params = (('onlydaily', False),)

    def __init__(self):
        self.fast_ema = bt.ind.EMA(period=80)
        self.slow_ema = bt.ind.EMA(period=200)
        self.ema_mcross = bt.indicators.CrossOver(self.fast_ema, self.slow_ema)
        if not self.p.onlydaily:
            self.sma_day5 = bt.ind.SMA(self.data1, period=6)

        # self.data1.plotinfo.plot = False

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        global sum_profit, total_trades, NumberOfWins, NumberOfLoss
        if not trade.isclosed:
            return
        if trade.pnl > 0:
            NumberOfWins = NumberOfWins + 1
        else:
            NumberOfLoss = NumberOfLoss + 1
        sum_profit = sum_profit + trade.pnl
        total_trades = total_trades + 1
        if trade.long:
            self.pnl = trade.pnl
        else:
            self.pnl = -trade.pnl
        print('OPERATION PROFIT, GROSS %.2f, NET %.2f SUM %.2f ' % (trade.pnl, trade.pnlcomm, sum_profit))
        # trade.long is 1, we need convert it to 0 which represent buy in our system

    def notify_order(self, order):
        global buyprice, buytime
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed]:
            if order.isbuy():
                buyprice = order.executed.price
                buytime = bt.num2date(order.executed.dt)
                print('Buy EXECUTED, Time: %s, Price: %.2f Size %d ' % (bt.num2date(order.executed.dt), order.executed.price, order.executed.size))
            else:
                buyprice = order.executed.price
                buytime = bt.num2date(order.executed.dt)
                print('Sell EXECUTED, Time: %s, Price: %.2f, Size %d ' % (bt.num2date(order.executed.dt), order.executed.price, order.executed.size))
        elif order.status in [order.Canceled, order.Margin]:
            print('%s ,' % order.Status[order.status])
            pass  # Simply log
        self.order = None  # indicate no order is pending

    def next(self):
        global total_trades, trade_type, buyprice, buytime, opencode
        exitcode = 0

        tradeopen = 0
        settlement_day = database.GetTXSettlementDay(Const.MorningSession, self.data.datetime.datetime(), 0)
        crosslist = [i for i in self.ema_mcross.get(size=80) if i == 1 or i == -1]
        if not self.position and self.data.datetime.date() == self.data1.datetime.date():
            if sum(crosslist) == -1:
                trade_type = 1
                tradeopen = 1
                opencode = 10010
            buyprice = self.data0.close[0]
        elif self.position and self.data.datetime.date() == self.data1.datetime.date():
            if settlement_day and str(self.data.datetime.datetime().time()) == '13:25:00':  # settlement day close, backtesting purposes
                exitcode = 88
            elif str(self.data.datetime.datetime().time()) == '13:40:00' and sum(crosslist) == 1:  # day trade close
                exitcode = 86

        if exitcode != 0:  # This is trade close, 1 if self.position.size > 0 else 0 used for trade_type, if position size greater than 0, trade type is 0. When close the order, use trade type 1
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 1 if self.position.size > 0 else 0, RunningMode)
            if matched:
                self.close(coc=True)
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 1 if self.position.size > 0 else 0, abs(self.position.size), self.data.close[0], 'M', Const.NoDayTrade, Const.TradeTypeIOC, exitcode)
        if tradeopen == 1 and trade_type == 0:  # This is trade open, long position
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 0, RunningMode)
            if matched:
                self.buy(data=self.datas[0], size=longposSize)
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 0, longposSize, self.data.close[0], 'M', Const.NoDayTrade, Const.TradeTypeIOC, opencode)
        if tradeopen == 1 and trade_type == 1:  # This is trade open, short position
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 1, RunningMode)
            if matched:
                self.sell(data=self.datas[0], size=shortposSize)
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 1, shortposSize, self.data.close[0], 'M', Const.NoDayTrade, Const.TradeTypeIOC, opencode)

        # database.InsertBacktestLog('Time %s Close %s sma_day5 %d sma_day10 %d sma_day20 %d sma_day50 %d '
        #                           % (str(self.data.datetime.datetime()), self.data.close[0], self.sma_day5[0], self.sma_day10[0], self.sma_day20[0], self.sma_day50[0]))


def runstrat(args=None):
    global sum_profit, total_trades, database, NumberOfWins, NumberOfLoss

    database = None
    database = DBconnect.DBconnect('localhost', 'Stock', 'trader', 'trader')
    database.Connect()

    database.InsertExecLog('3.1 %s Starting' % StratName)
    # database.ClearOrderLog()

    args = parse_args(args)

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.set_coc(True)

    minutefromdate = dt.datetime(2020, 1, 1)  # -8 days
    # minutefromdate = dt.datetime(2020, 5, 2)
    dayfromdate = dt.datetime(2019, 1, 1)
    # todate = dt.datetime(2020, 1, 1)
    todate = dt.datetime(2022, 12, 31)
    # Don't put todate on last trade day, it will not place order

    data0 = bt.feeds.MySQLData(fromdate=minutefromdate, todate=todate, server='localhost', database='Stock', username='trader', password='trader', stockID='TX00', KLine='5', Session=0, timeframe=bt.TimeFrame.Minutes)
    data1 = bt.feeds.MySQLData(fromdate=dayfromdate, todate=todate, server='localhost', database='Stock', username='trader', password='trader', stockID='TX00', KLine='0', Session=0, timeframe=bt.TimeFrame.Days,
                               sessionend=dt.time(00, 00))
    # data2 = bt.feeds.MySQLData(fromdate=dayfromdate, todate=todate, server='localhost', database='Stock', username='trader', password='trader', stockID='TX00', KLine='60', Session=0, timeframe=bt.TimeFrame.Minutes,
    #                           sessionend=dt.time(00, 00))
    # only work on session end 00 no idea why day is not aligned with min when set sessionend to 13:45
    cerebro.adddata(data0)
    cerebro.adddata(data1)

    cerebro.addstrategy(TheStrategy, onlydaily=args.onlydaily)
    cerebro.run(stdstats=False)
    total_trades = 1 if total_trades == 0 else total_trades

    print('Sum of profit ', sum_profit)
    print('Number of trades ', total_trades)
    print('Profit per trans %.2f' % (sum_profit / total_trades))
    print('Total Fee in currency %.2f' % (total_trades * 50))
    print('Total profit in currency %.2f' % (sum_profit * 50 - total_trades * 50))
    print('Total wins %i ' % NumberOfWins)
    print('Total loss %i' % NumberOfLoss)
    print('Winning Percentage %.2f' % (NumberOfWins / total_trades * 100))
    # cerebro.plot()
    database.InsertExecLog('3.3 %s Finished' % StratName)


def TimeUntilOpen(d1):
    if d1.time() <= dt.time(5, 00):
        d2 = d1 + timedelta(days=-1)
        return d1 - dt.datetime(d2.year, d2.month, d2.day, 8, 45, 00)
    else:
        return d1 - dt.datetime(d1.year, d1.month, d1.day, 8, 45, 00)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--cash', required=False, action='store', type=float, default=10000000)
    parser.add_argument('--onlydaily', action='store_true')
    if pargs is not None:
        return parser.parse_args(pargs)
    return parser.parse_args()


if __name__ == '__main__':
    runstrat()

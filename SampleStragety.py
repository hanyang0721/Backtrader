import backtrader as bt
import datetime as dt
import argparse
import DBconnect
import Const
from statistics import mean
from datetime import timedelta

RunningMode = Const.AnalysisMode
trade_type, NumberOfWins, NumberOfLoss, buytime, buyprice, total_trades, sum_profit = (0,) * 7
StratName = 'SampleStrategy'
StockNo = 'MTX00'
PlaceOrdersAmt = 0
database = None


class SampleStrategy(bt.Strategy):
    params = (
        ('onlydaily', False),
        ('ema1', 60),
        ('ema2', 120),
    )

    def __init__(self):
        self.ema1 = bt.ind.EMA(self.data, period=self.params.ema1)
        self.ema2 = bt.ind.EMA(self.data, period=self.params.ema2)
        self.ema_mcross1 = bt.indicators.CrossOver(self.ema1, self.ema2)
        if not self.p.onlydaily:
            self.sma_day5 = bt.ind.SMA(self.data1, period=5)
            self.sma_day50 = bt.ind.SMA(self.data1, period=50)
        self.data1.plotinfo.plot = False


    def notify_trade(self, trade):
        global sum_profit, total_trades, NumberOfWins, NumberOfLoss
        if not trade.isclosed:
            return

        print('OPERATION PROFIT, GROSS %.2f, NET %.2f SUM %.2f ' % (trade.pnl, trade.pnlcomm, sum_profit))
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
                print('Buy EXECUTED, Time: %s, Price: %.2f ' % (bt.num2date(order.executed.dt), order.executed.price))
            else:
                buyprice = order.executed.price
                buytime = bt.num2date(order.executed.dt)
                print('Sell EXECUTED, Time: %s, Price: %.2f ' % (bt.num2date(order.executed.dt), order.executed.price))
        elif order.status in [order.Canceled, order.Margin]:
            # print('%s ,' % order.Status[order.status])
            pass  # Simply log
        self.order = None  # indicate no order is pending

    def next(self):
        global trade_type, buyprice, buytime
        stratcode, dnline, upline, pclose = 0, 0, 0, 0
        tradeopen = 0
        settlement_day = database.GetTXSettlementDay(Const.MorningSession, self.data.datetime.datetime())
        if not self.position:
            if self.ema_mcross1[0] == 1:
                trade_type = 0
                tradeopen = 1
                stratcode = 10000
            buyprice = self.data0.close[0]
        else:
            if str(self.data.datetime.datetime().time()) == '04:55:00' and settlement_day:
                stratcode = 1
            elif self.ema_mcross1[0] == -1:
                stratcode = 2

        if tradeopen == 1 and trade_type == 0:
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 0, RunningMode)
            if matched:
                self.buy(data=self.datas[0])
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 0, PlaceOrdersAmt, buyprice, 'M', Const.NoDayTrade, Const.TradeTypeIOC, stratcode)
        elif tradeopen == 1 and trade_type == 1:
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 1, RunningMode)
            if matched:
                self.sell(data=self.datas[0])
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 1, PlaceOrdersAmt, buyprice, 'M', Const.NoDayTrade, Const.TradeTypeIOC, stratcode)
        elif stratcode != 0 and trade_type == 0:  # This is trade close
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 1, RunningMode)
            if matched:
                self.close(coc=True)
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 1, PlaceOrdersAmt, self.data.close[0], 'M', Const.NoDayTrade, Const.TradeTypeIOC, stratcode)
        elif stratcode != 0 and trade_type == 1:  # This is trade close
            matched = database.CheckMatchedOrder(StockNo, self.data.datetime.datetime(), 0, RunningMode)
            if matched:
                self.close(coc=True)
                database.InsertOrder(StratName, StockNo, self.data.datetime.datetime(), 0, PlaceOrdersAmt, self.data.close[0], 'M', Const.NoDayTrade, Const.TradeTypeIOC, stratcode)


def runstrat(args=None):
    global sum_profit, total_trades, database, NumberOfWins, NumberOfLoss

    database = None
    database = DBconnect.DBconnect('localhost', 'Stock', 'trader', 'trader')
    database.Connect()
    args = parse_args(args)

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.set_coc(True)
    cerebro.broker.set_cash(args.cash)

    minutefromdate = dt.datetime(2020, 3, 1)
    dayfromdate = dt.datetime(2020, 1, 1)
    todate = dt.datetime(2022, 5, 20)

    data0 = bt.feeds.MySQLData(dataname='data0', fromdate=minutefromdate, todate=todate, server='localhost', database='Stock', username='trader', password='trader', stockID='TX00', KLine='5', Session=0, timeframe=bt.TimeFrame.Minutes)
    data1 = bt.feeds.MySQLData(dataname='data1', fromdate=dayfromdate, todate=todate, server='localhost', database='Stock', username='trader', password='trader', stockID='TX00', KLine='0', Session=0, timeframe=bt.TimeFrame.Days,
                               sessionend=dt.time(00, 00))
    cerebro.adddata(data0)
    cerebro.adddata(data1)

    cerebro.addstrategy(SampleStrategy, )
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
    # cerebro.plot(fmt_x_ticks='%Y-%m-%d %H:%M', fmt_x_data='%Y-%m-%d %H:%M')


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--ema1', required=False, type=int)
    parser.add_argument('--ema2', required=False, type=int)
    parser.add_argument('--cash', required=False, type=float, default=1000000)

    if pargs is not None:
        return parser.parse_args(pargs)
    return parser.parse_args()


if __name__ == '__main__':
    runstrat()

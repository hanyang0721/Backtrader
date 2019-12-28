import backtrader as bt
import datetime as dt
import argparse
import DBconnect
import Const

database = None
trade_type = 0  # 0 is short, 1 is long
NumberOfWins, NumberOfLoss, buytime, buyprice, total_trades, sum_profit = (0,)*6
PlaceOrdersAmt = 1
StockNo = 'MTX00'


class TheStrategy(bt.Strategy):
    params = (
        # Standard MACD Parameters
        ('macd1', 5),
        ('macd2', 35),
        ('macdsig', 5),
        ('atrdist', 3.0),
        ('onlydaily', False),
    )

    def __init__(self):
        self.macd = bt.indicators.MACDHisto(self.data,
                                            period_me1=self.p.macd1,
                                            period_me2=self.p.macd2,
                                            period_signal=self.p.macdsig)
        self.atr = bt.indicators.ATR(self.data, period=8)

        if not self.p.onlydaily:
            self.sma_day5 = bt.ind.SMA(self.data1, period=5)
            self.sma_day20 = bt.ind.SMA(self.data1, period=20)

        self.sma_vol5 = bt.ind.SMA(self.data.volume, period=5)
        self.sma_vol20 = bt.ind.SMA(self.data.volume, period=20)
        self.sma_vol10 = bt.ind.SMA(self.data.volume, period=10)

        self.data1.plotinfo.plot = True
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
        # because True is 1, we need convert it to 0 which represent buy
        database.InsertPerfLog('TheStraAlpha', bt.num2date(trade.dtopen), bt.num2date(trade.dtclose), trade.price, trade.price + self.pnl, int(not trade.long))

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
            print('%s ,' % order.Status[order.status])
            pass  # Simply log
        self.order = None  # indicate no order is pending

    def next(self):
        global total_trades, trade_type, buyprice, buytime
        settlement_day = False

        if (self.data.datetime.datetime().weekday() == 2 and 15 <= self.data.datetime.datetime().day <= 21) or \
                (self.data.datetime.datetime().weekday() == 3 and 15 <= self.data.datetime.datetime().day <= 22):
            settlement_day = True

        if not self.position:
            if self.macd.signal[0] < 0 and self.macd[0] >= 0.0:
                pdist = self.atr[0] * self.p.atrdist
                buyprice = self.data.close[0]
                self.pstop = self.data.close[0] - pdist
                trade_type = 1
                self.sell(data=self.datas[0])
                database.InsertOrder(StockNo, self.data.datetime.datetime(), 1, PlaceOrdersAmt, buyprice, buyprice-2,  Const.NoDayTrade, Const.TradeTypeROD)
            if self.macd.signal[0] >= 0 and self.macd[0] < 0:
                pdist = self.atr[0] * self.p.atrdist
                buyprice = self.data.close[0]
                self.pstop = self.data.close[0] - pdist
                trade_type = 0
                self.buy(data=self.datas[0])
                database.InsertOrder(StockNo, self.data.datetime.datetime(), 0, PlaceOrdersAmt, buyprice, buyprice+2, Const.NoDayTrade, Const.TradeTypeROD)
        elif self.position:
            pclose = self.data.close[0]
            pstop = self.pstop
            tradeclose = 0
            if settlement_day and str(self.data.datetime.datetime().time()) == '13:25:00':
                self.close(coc=settlement_day)
                tradeclose = 1
            elif (pstop > pclose) and trade_type == 1:
                self.close(coc=True)
                tradeclose = 1
            elif (pstop > pclose+30) and trade_type == 0:
                self.close(coc=True)
                tradeclose = 1
            else:
                pdist = self.atr[0] * self.p.atrdist
                self.pstop = max(pstop, pclose - pdist)

            if tradeclose == 1 and trade_type == 0:
                database.InsertOrder(StockNo, self.data.datetime.datetime(), 1, PlaceOrdersAmt, pclose, pclose + 2, Const.NoDayTrade, Const.TradeTypeROD)
            if tradeclose == 1 and trade_type == 1:
                database.InsertOrder(StockNo, self.data.datetime.datetime(), 0, PlaceOrdersAmt, pclose, pclose - 2, Const.NoDayTrade, Const.TradeTypeROD)


def runstrat(args=None):
        global sum_profit, total_trades, database, NumberOfWins, NumberOfLoss

        database = None
        database = DBconnect.DBconnect('localhost', 'trader', 'trader')
        database.Connect()

        database.InsertExecLog('3.1  Backtrader Starting')
        database.ClearPerfLog()

        args = parse_args(args)

        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(args.cash)
        cerebro.broker.set_coc(True)

        fromdate = dt.datetime(2019, 7, 15)
        todate = dt.datetime(2019, 12, 31)

        data0 = bt.feeds.MySQLData(fromdate=fromdate, todate=todate, server='localhost', username='trader', password='trader', stockID='TX00', KLine='5', Session=1, timeframe=bt.TimeFrame.Minutes)
        data1 = bt.feeds.MySQLData(fromdate=fromdate, todate=todate, server='localhost', username='trader', password='trader', stockID='TX00', KLine='0', Session=1, timeframe=bt.TimeFrame.Days)

        cerebro.adddata(data0)
        cerebro.adddata(data1)

        # args for the strategy, period is a MUST why??
        cerebro.addstrategy(TheStrategy, onlydaily=args.onlydaily, )

        #cerebro.addstrategy(testStrategy,)
        cerebro.run()
        if total_trades == 0: total_trades = 1
        print('Sum of profit ', sum_profit)
        print('Number of trades ', total_trades)
        print('Profit per trans %.2f' % (sum_profit / total_trades))
        print('Total Fee in currency %.2f' % (total_trades * 50))
        print('Total profit in currency %.2f' % (sum_profit * 50 - total_trades * 50))
        print('Total wins %i ' % NumberOfWins)
        print('Total loss %i' % NumberOfLoss)
        print('Winning Percentage %.2f' % (NumberOfWins/total_trades*100))
        cerebro.plot()

def parse_args(pargs=None):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Sample for Tharp example with MACD')

        parser.add_argument('--cash', required=False, action='store',
                            type=float, default=500000,
                            help=('Cash to start with'))

        parser.add_argument('--period', default=50, required=False, type=int,
                            help='Period to apply to indicator')

        parser.add_argument('--onlydaily', action='store_true',
                            help='Indicator only to be applied to daily timeframe')

        if pargs is not None:
            return parser.parse_args(pargs)

        return parser.parse_args()


if __name__ == '__main__':
    runstrat()

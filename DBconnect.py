# coding=utf-8
import pyodbc


class DBconnect:
    def __init__(self, addr, database, username, password):
        self.Server = {"server": addr, "database": database, "username": username, 'password': password}
        self.conn = None
        self.driver = '{SQL Server Native Client 11.0}'

    def Connect(self):
        self.conn = pyodbc.connect('DRIVER=' + self.driver + ';SERVER=' + self.Server['server'] + ';DATABASE=' + self.Server['database'] + ';UID=' + self.Server['username'] + ';PWD=' + self.Server['password'])

    def InsertPerfLog(self, straname, buytime, selltime, buyprice, sellprice, trade_type):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.StrategyPerformanceHis ([StrName],[buytime],[selltime],[buyprice],[sellprice], [TradeType]) values (? , ?, ?, ?, ?, ?) "
        param_values = [straname, buytime, selltime, buyprice, sellprice, trade_type]
        # SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL, param_values)
        cursor.commit()

    def InsertOptimizeLog(self, StratName, Datefrom, Dateto, SumOfProfit, NumerOfTrades, ProfitPertrades, TotalWins, TotalLoss, WinningPct,
                          Para1=0, value1=0, Para2=0, value2=0, Para3=0, value3=0, Para4=0, value4=0, Para5=0, value5=0, Para6=0, value6=0, Para7=0, value7=0, Para8=0,
                          value8=0, Para9=0, value9=0, Para10=0, value10=0):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.StrategyOpitimizeResult values (? , ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        param_values = [StratName, Datefrom, Dateto, SumOfProfit, NumerOfTrades, ProfitPertrades, TotalWins, TotalLoss, WinningPct,
                        Para1, value1, Para2, value2, Para3, value3, Para4, value4, Para5, value5, Para6, value6, Para7, value7, Para8, value8, Para9, value9, Para10, value10]
        # SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL, param_values)
        cursor.commit()

    def InsertBacktestLog(self, message):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.Backtestlog values (?) "
        param_values = [message]
        # SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL, param_values)
        cursor.commit()

    def ClearBacktestLog(self):
        cursor = self.conn.cursor()
        SQL = " DELETE dbo.BacktestLog "
        cursor.execute(SQL)
        cursor.commit()

    def ChkOrderMatched(self):
        cursor = self.conn.cursor()
        SQL = "EXEC dbo.sp_GetNotifyOrders"
        cursor.execute(SQL)
        logList = cursor.fetchall()
        return logList

    def InsertExecLog(self, message):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.[ATM_DailyLog] (ExecTime, Service, MsgType ,Message) values (GETDATE() , 'PyStartegy', 'INFO' ,'{message}' ) "
        SQL = SQL.format(message=message)
        cursor.execute(SQL)
        cursor.commit()

    def ClearPerfLog(self):
        cursor = self.conn.cursor()
        SQL = " DELETE dbo.StrategyPerformanceHis "
        cursor.execute(SQL)
        cursor.commit()

    def ClearOrderLog(self):
        cursor = self.conn.cursor()
        SQL = " DELETE dbo.Orders "
        cursor.execute(SQL)
        cursor.commit()

    def InsertOrder(self, StratName, stockNo, SignalTime, BuyOrSell, Size, Price, DealPrice, DayTrade, TradeType, Stratcode):
        cursor = self.conn.cursor()
        SQL = """ IF NOT EXISTS (SELECT 1 FROM dbo.Orders WHERE SignalTime='{SignalTime}' AND BuyOrSell='{BuyOrSell}' AND StratCode='{Stratcode}' )　
                                 BEGIN INSERT INTO dbo.Orders ([StrategyName], [stockNo],[SignalTime],[BuyOrSell],[Size], [Price], 
                                 [DealPrice], [DayTrade], [TradeType], [Stratcode]) 
                  values ('{StratName}', '{stockNo}', '{SignalTime}', '{BuyOrSell}', '{Size}', '{Price}','{DealPrice}','{DayTrade}','{TradeType}', '{Stratcode}') END """
        SQL = SQL.format(StratName=StratName, stockNo=stockNo, SignalTime=SignalTime, BuyOrSell=BuyOrSell, Size=Size, Price=Price,
                         DealPrice=DealPrice, DayTrade=DayTrade, TradeType=TradeType, Stratcode=Stratcode)

        # param_values = [stockNo, SignalTime, BuyOrSell, Size, Price]
        # SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL)
        cursor.commit()

    # 1 -> matched order happen on either of the following conditions.
    #    Order is found in the order table
    #    Running Mode is Analysis(0), or
    #    ExecutionMode (1) and Signal time is less than 300 minutes, use 300 minutes because it could still notify us when order comes late in same day market time
    #    Late order reason can be no tick, program issue
    def CheckMatchedOrder(self, stockNo, SignalTime, BuyOrSell, RunningMode):
        cursor = self.conn.cursor()
        SQL = """ IF EXISTS (SELECT 1 FROM dbo.Orders WHERE SignalTime='{SignalTime}' AND BuyOrSell='{BuyOrSell}' AND stockNo='{stockNo}' ) 
                     OR 0='{RunningMode}' OR '{SignalTime}' >= DATEADD(minute, -300, GETDATE())
                    SELECT 1　
                  ELSE 
                    SELECT 0"""
        SQL = SQL.format(stockNo=stockNo, SignalTime=SignalTime, BuyOrSell=BuyOrSell, RunningMode=RunningMode)
        cursor.execute(SQL)
        matched = cursor.fetchall()
        return matched[0][0]

    def GetNotifyOrders(self):
        cursor = self.conn.cursor()
        SQL = "EXEC dbo.sp_GetNotifyOrders"
        cursor.execute(SQL)
        logList = cursor.fetchall()
        return logList

    def UpdateNotifyOrders(self, orderid):
        cursor = self.conn.cursor()
        SQL = "UPDATE dbo.LineNotifyLog SET Result=0, Notifytime=GETDATE() WHERE orderid= '{orderid}'"
        SQL = SQL.format(orderid=orderid)
        cursor.execute(SQL)
        cursor.commit()

    def GetTXSettlementDay(self, Session, SignalTime, functioncode):
        cursor = self.conn.cursor()
        SQL = """ EXEC dbo.sp_GetTXSettlementDay @session='{Session}', @signaltime='{SignalTime}', @functioncode='{functioncode}' """
        SQL = SQL.format(SignalTime=SignalTime, Session=Session, functioncode=functioncode)
        cursor.execute(SQL)
        matched = cursor.fetchall()
        return matched[0][0]

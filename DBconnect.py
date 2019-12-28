import pyodbc


class DBconnect:
    def __init__(self, addr, username, password):
        self.Server = { "server": addr, "username": username, 'password': password}
        self.conn = None
        self.driver = '{SQL Server Native Client 11.0}'
        self.database = None
        self.Query = ''
        self.database = ''

    def SetDatabase(self, database):
        self.Server['name'] = database
        self.database = database

    def Connect(self):
        self.conn = pyodbc.connect('DRIVER=' + self.driver + ';PORT=1433;SERVER=' + self.Server['server']
                                   + ';PORT=1443;DATABASE=Stock;' + 'Trusted_Connection=yes')

    def InsertPerfLog(self, straname, buytime, selltime, buyprice, sellprice, trade_type):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.StrategyPerformanceHis ([StrName],[buytime],[selltime],[buyprice],[sellprice], [TradeType]) values (? , ?, ?, ?, ?, ?) "
        param_values = [straname, buytime, selltime, buyprice, sellprice, trade_type]
        #SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL, param_values)
        cursor.commit()

    def InsertExecLog(self, message):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.[ATM_DailyLog] (ExecTime,Steps) values (GETDATE() ,'{message}' ) "
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

    def InsertOrder(self, stockNo , SignalTime, BuyOrSell, Size, Price, DealPrice, DayTrade, TradeType):
        cursor = self.conn.cursor()
        SQL = """ IF NOT EXISTS (SELECT 1 FROM Orders WHERE SignalTime='{SignalTime}' AND BuyOrSell='{BuyOrSell}' )　
                                 BEGIN INSERT INTO dbo.Orders ([stockNo],[SignalTime],[BuyOrSell],[Size], [Price], 
                                 [DealPrice], [DayTrade], [TradeType]) 
                  values ('{stockNo}', '{SignalTime}', '{BuyOrSell}', '{Size}', '{Price}','{DealPrice}','{DayTrade}','{TradeType}') END """
        SQL = SQL.format(stockNo=stockNo, SignalTime=SignalTime, BuyOrSell=BuyOrSell, Size=Size, Price=Price,
                         DealPrice=DealPrice, DayTrade=DayTrade, TradeType=TradeType)

        #param_values = [stockNo, SignalTime, BuyOrSell, Size, Price]
        #SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL)
        cursor.commit()

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
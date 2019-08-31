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
                                   + ';PORT=1443;DATABASE=Stock;' + 'UID=' + self.Server['username'] + ';PWD=' +
                                   self.Server['password'])

    def InsertPerfLog(self, straname ,buytime, selltime, buyprice, sellprice, trade_type):
        cursor = self.conn.cursor()
        SQL = " INSERT INTO dbo.StrategyPerformanceHis ([StrName],[buytime],[selltime],[buyprice],[sellprice], [TradeType]) values (? , ?, ?, ?, ?, ?) "
        param_values = [straname, buytime, selltime, buyprice, sellprice, trade_type]
        #SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL, param_values)
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

    def InsertOrder(self, stockNo , SignalTime, BuyOrSell, Size, Price):
        cursor = self.conn.cursor()
        SQL = """ IF NOT EXISTS (SELECT 1 FROM Orders WHERE SignalTime='{SignalTime}' AND BuyOrSell='{BuyOrSell}' )　BEGIN INSERT INTO dbo.Orders ([stockNo],[SignalTime],[BuyOrSell],[Size], [Price]) 
                  values ('{stockNo}', '{SignalTime}', '{BuyOrSell}', '{Size}', '{Price}') END """
        SQL = SQL.format(stockNo=stockNo, SignalTime=SignalTime, BuyOrSell=BuyOrSell, Size=Size,Price=Price)

        #param_values = [stockNo, SignalTime, BuyOrSell, Size, Price]
        #SQL = SQL.format(OrderSN=OrderSN, ErrorLog=ErrorLog)
        cursor.execute(SQL)
        cursor.commit()

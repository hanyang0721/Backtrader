from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


from backtrader.feed import DataBase
from backtrader import date2num
#from sqlalchemy import create_engine
import pyodbc

class MySQLData(DataBase):
    params = (
        ('server', None),
        ('username', None),
        ('password', None),
        ('database', 'Stock'),
        ('driver', '{SQL Server Native Client 11.0}'),
        ('fromdate', None),
        ('todate', None),
        ('stockID', None),
        ('KLine', None))
        #0 stands for daily based
        #5 stands for 5 minute based
    def __init__(self):
        self.conn = None
        self.driver = '{SQL Server Native Client 11.0}'
        self.database = 'Stock'
        self.stockID = self.params.__dict__['stockID']

    def start(self):
        self.conn = pyodbc.connect('DRIVER=' + self.driver + ';PORT=1433;SERVER=' + self.params.__dict__['server']
                                   + ';PORT=1443;DATABASE=Stock;' + 'UID='+ self.params.__dict__['username'] + ';PWD='+ self.params.__dict__['password'] )

        if self.params.KLine == '0':
            SQLQuery = "EXEC [dbo].sp_GetTicksDaily  '%s', '%s','%s' " % (self.params.fromdate, self.params.todate, self.stockID)
        elif self.params.KLine == '5':
            SQLQuery = """EXEC [dbo].[sp_GetTicksIn5Min]  '%s', '%s','%s'  """ % (self.params.fromdate, self.params.todate, self.stockID )
        elif self.params.KLine == '60':
            SQLQuery = """EXEC [dbo].[sp_GetTickInHour]  '%s', '%s','%s'  """ % (self.params.fromdate, self.params.todate, self.stockID )

        print(SQLQuery)
        self.result = self.conn.execute(SQLQuery)

    def stop(self):
        self.conn.close()
        #self.engine.dispose()
    #format(one_row[4],'.2f')
    def _load(self):
        one_row = self.result.fetchone()
        if one_row is None:
            return False
        self.lines.datetime[0] = date2num(one_row[0])
        self.lines.open[0] = float(one_row[1])
        self.lines.high[0] = float(one_row[2])
        self.lines.low[0] = float(one_row[3])
        self.lines.close[0] = float(one_row[4])
        self.lines.volume[0] = int(one_row[5])
        self.lines.openinterest[0] = -1
        return True
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


from backtrader.feed import DataBase
from backtrader import date2num
from datetime import date, datetime, time
import pyodbc

class MySQLData(DataBase):
    params = (
        ('server', None),
        ('username', None),
        ('password', None),
        ('database', None),
        ('driver', '{SQL Server Native Client 11.0}'),
        ('fromdate', None),
        ('todate', None),
        ('stockID', None),
        ('KLine', None),
        ('Session', None))
        #0 stands for daily based
        #5 stands for 5 minute based
    def __init__(self):
        self.conn = None
        self.driver = '{SQL Server Native Client 11.0}'
        self.stockID = self.params.__dict__['stockID']
        self.database = self.params.__dict__['database']

    def start(self):
        self.conn = pyodbc.connect('DRIVER=' + self.driver + ';SERVER=' + self.params.server + ';DATABASE=' + self.database + ';UID=' + self.params.username + ';PWD=' + self.params.password)

        if self.params.KLine == '0':
            SQLQuery = "EXEC [dbo].[sp_GetTicksDaily]  '%s', '%s','%s',%s " % (self.params.fromdate, self.params.todate, self.params.stockID, self.params.Session)
        elif self.params.KLine == '5':
            SQLQuery = "EXEC [dbo].[sp_GetTicksIn5Min]  '%s', '%s','%s', %s  " % (self.params.fromdate, self.params.todate, self.params.stockID, self.params.Session)
        elif self.params.KLine == '15':
            SQLQuery = "EXEC [dbo].[sp_GetTicksIn15Min]  '%s', '%s','%s', %s  " % (self.params.fromdate, self.params.todate, self.params.stockID, self.params.Session)
        elif self.params.KLine == '30':
            SQLQuery = "EXEC [dbo].[sp_GetTicksIn30Min]  '%s', '%s','%s', %s  " % (self.params.fromdate, self.params.todate, self.params.stockID, self.params.Session)
        elif self.params.KLine == '60':
            SQLQuery = "EXEC [dbo].[sp_GetTicksIn60Min]  '%s', '%s','%s', %s  " % (self.params.fromdate, self.params.todate, self.params.stockID, self.params.Session)
        elif self.params.KLine == '1':
            SQLQuery = "EXEC [dbo].[sp_GetTicksIn1Min]  '%s', '%s','%s', %s  " % (self.params.fromdate, self.params.todate, self.params.stockID, self.params.Session)
        print(SQLQuery)
        self.result = self.conn.execute(SQLQuery)

    def stop(self):
        self.conn.close()

    def _load(self):
        one_row = self.result.fetchone()
        if one_row is None:
            return False

        if one_row[0].resolution.days == 0:
            dt = date(int(str(one_row[0])[0:4]), int(str(one_row[0])[5:7]), int(str(one_row[0])[8:10]))
            tm = time(int(str(one_row[0])[11:13]), int(str(one_row[0])[14:16]), int(str(one_row[0])[17:19]))
        else:
            dt = date(int(str(one_row[0])[0:4]), int(str(one_row[0])[5:7]), int(str(one_row[0])[8:10]))
            tm = self.p.sessionend  # end of the session parameter

        self.lines.datetime[0] = date2num(datetime.combine(dt, tm))
        self.lines.open[0] = float(one_row[1])
        self.lines.high[0] = float(one_row[2])
        self.lines.low[0] = float(one_row[3])
        self.lines.close[0] = float(one_row[4])
        self.lines.volume[0] = int(one_row[5])
        self.lines.openinterest[0] = -1
        return True
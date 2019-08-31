# Backtrader

參考<https://www.backtrader.com>
回測及下單用的script. 

## 步驟
將sql.py放入backtrader的library, 如C:\Users\xx\AppData\Local\Programs\Python\Python36\Lib\site-packages\backtrader\feeds
backtrader才可使用data feed from sql

如需分k,日k請用SKQuote下載資料

這個sample使用了日線搭配五分K兩個data feeds
```python
data0 = bt.feeds.MySQLData(fromdate=fromdate, todate=todate, server='localhost', username='trader', password='trader', stockID='TX00', 
KLine='5', timeframe=bt.TimeFrame.Minutes)
```
5代表5分K
0代表日K

SQL部分我寫使用了自己的login, 可改寫sql.py自訂connectionstring

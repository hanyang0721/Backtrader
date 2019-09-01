# Backtrader

參考 <https://www.backtrader.com> </br>
供回測及下單用的script. </br>
此程式內使用策略僅為為範例檔, 請自行開發穩定策略

## 程式功能
1. 提供SQL view and procedure做回測數據的檢視
1. StrategyPerformanceHis表格為回測用, 

## 安裝步驟
1. **設定python環境**  
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

2. **設定SQL環境**  
將Query.sql裡的schema, table, procedure等等全部倒到對應的路徑

## 執行畫面
![image](https://github.com/hanyang0721/Backtrader/blob/master/strat.PNG)

# Backtrader

參考 <https://www.backtrader.com> </br>
供回測及下單用的script. </br>
此程式內使用策略僅為為範例檔, 請自行開發穩定策略

## 程式功能
1. 提供SQL view and procedure做回測數據的檢視
2. 提供SQL server data feeds連結, 原始backtrader網站沒有

## 安裝步驟
1. **設定python環境**  
將sql.py放入backtrader的library, 如C:\Users\xx\AppData\Local\Programs\Python\Python36\Lib\site-packages\backtrader\feeds
backtrader才可使用data feed from sql

這個sample使用了日線搭配五分K兩個data feeds, 可使用一個data feeds到多個data feeds全依策略安排
```python
data0 = bt.feeds.MySQLData(fromdate=fromdate, todate=todate, server='localhost', username='trader', password='trader', stockID='TX00', 
KLine='5', timeframe=bt.TimeFrame.Minutes)
```
5代表5分K
0代表日K
SQL部分我寫使用了自己的login, 可改寫sql.py自訂connectionstring

2. **設定SQL環境**  
將Query.sql裡的schema, table, procedure等等全部倒到對應的路徑

3. **下載報價**
請用SKQuote下載資料分k,日k

## 執行畫面
![image](https://github.com/hanyang0721/Backtrader/blob/master/strat.PNG)

## 策略數據檢驗
```sql
SELECT * FROM [Stock].[dbo].[GetMonthlyPerformanceDetails] 
SELECT *  FROM [Stock].[dbo].[GetMonthlyPerformanceSum]
```
![image](https://github.com/hanyang0721/Backtrader/blob/master/backtrader.PNG)

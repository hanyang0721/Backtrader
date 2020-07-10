# Backtrader策略機 

參考 <https://www.backtrader.com> </br>
供回測及下單用的script. </br>
Backtrader是一個基於Python語言的進行自動化回溯測試的平臺。可以新增自定義的指標和交易策略,提高對交易系統回測的效率。 
這個工具可以匯入自己的行情資料檔案,也可以新增自定義的指標
此程式內使用策略僅為為範例檔, 請自行開發穩定策略

## 程式功能
1. 提供SQL view and procedure做回測數據的檢視
2. 提供SQL server data feeds連結
3. 提供DBConnect與database連動後可使用於下單及回測

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
  SQL部分我使用了自己的login, 可改寫sql.py自訂connectionstring

2. **設定SQL環境**  
將這個資料庫還原: https://github.com/hanyang0721/Stock-Database
使用bak還原, 或是script還原

3. **(Optional)下載報價**
請用SKQuote下載資料分k,日k

## 執行畫面
![image](https://github.com/hanyang0721/image/blob/master/strat.png)
<br>
![image](https://github.com/hanyang0721/image/blob/master/plot.png)

## 線上執行績效
3口小台, 僅交易早盤<br>
![image](https://github.com/hanyang0721/image/blob/master/IMG_4177.PNG)

## 程式參數說明
shortposzie, longposSize 多空下單口數<br>
StockNo 下單標的<br>
RunningMode (AnalysisMode, ExecutionMode) ExecutionMode為盤中使用, 回測及優化策略時使用AnalysisMode<br>
settlement_day 結算日<br>
stratcode 目前定義10000~10009為long open, 10010以上為short open, 其餘為exit code, 可自行定義opencode, exitcode做策略的analysis<br>
tradetype 0 為做多, 1為做空<br>
sessionend 收盤時間, use with caution. 早盤為00:00 夜盤為05:00<br> 

## 策略數據檢驗
執行sp後使用https://github.com/hanyang0721/Stock-Database 裡的CashMining.sql
做分析
```sql
EXEC dbo.sp_GetActualOrderPerformance
```
![image](https://github.com/hanyang0721/image/blob/master/analysis.PNG)

USE [Stock]
GO

-----------------------------------------下單用table------------------------------------------------------
CREATE TABLE [dbo].[Orders](
	[orderid] [int] IDENTITY(1,1) NOT NULL,
	[stockNo] [varchar](10) NOT NULL,
	[SignalTime] [smalldatetime] NOT NULL,
	[BuyOrSell] [varchar](4) NOT NULL,
	[Size] [int] NOT NULL,
	[Price] [float] NULL,
	[DayTrade] [int] NULL,
	[Result] [varchar](12) NULL,
	[EntryDate] [datetime] NULL,
PRIMARY KEY CLUSTERED 
(
	[SignalTime] ASC,
	[BuyOrSell] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[Orders] ADD  CONSTRAINT [DF__Orders__EntryDat__76969D2E]  DEFAULT (getdate()) FOR [EntryDate]
GO

--------------------------------------回測數據表------------------------------------------------------

USE [Stock]
GO

CREATE TABLE [dbo].[StrategyPerformanceHis](
	[StrName] [varchar](32) NOT NULL,
	[buytime] [datetime] NULL,
	[selltime] [datetime] NULL,
	[buyprice] [float] NULL,
	[sellprice] [float] NULL,
	[TradeType] [int] NULL,
	[Entrydate] [datetime] NULL
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[StrategyPerformanceHis] ADD  DEFAULT (getdate()) FOR [Entrydate]
GO


-------------------------------------五分K sp-----------------------------------------------------
CREATE PROCEDURE [dbo].[sp_GetTicksIn5Min] 
@from date,
@to date,
@stockID varchar(8)

AS
	SET NOCOUNT ON-----This make sp work like a query, prevent any insert rowcount returns
	SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED

	DECLARE @dtdaily date, @ticktime date
	SELECT @dtdaily = MAX(CAST([sdate] as date)) FROM Stock.dbo.StockHisotryMin
	SELECT @ticktime = MAX(CONVERT(datetime,convert(char(8),ndate))) FROM Stock.dbo.TickData

	SELECT (CAST([sdate] AS DATE)) [sdate], 
	--(stime),LEFT(stime,4) + case when RIGHT(stime,1)<='5' then '0' else '5' END stimeround,
	CAST(CAST([sdate] AS DATE) AS VARCHAR) + ' ' +
			LEFT(CASE WHEN RIGHT(stime,1)='0' THEN DATEADD(MINUTE,-5,cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='1' AND RIGHT(stime,1)<='5'THEN DATEADD(MINUTE,-CAST(RIGHT(stime,1) as int),cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='6' AND RIGHT(stime,1)<='9'THEN DATEADD(MINUTE,-(CAST(RIGHT(stime,1) as int)-5),cast(stime as time(0)))
			END,5) AS stime2 ,
	CONVERT(DECIMAL(8,2), [open]/100) [open] , 
	CONVERT(DECIMAL(8,2), [highest]/100) [highest],
	CONVERT(DECIMAL(8,2), [lowest]/100) [lowest], 
	CONVERT(DECIMAL(8,2), [close]/100) [close], [vol] ,
	RANK() OVER (partition by 
	CAST(CAST([sdate] AS DATE) AS VARCHAR) + ' ' +
			LEFT(CASE WHEN RIGHT(stime,1)='0' THEN DATEADD(MINUTE,-5,CAST(stime as time(0)))
			WHEN RIGHT(stime,1)>='1' AND RIGHT(stime,1)<='5'THEN DATEADD(MINUTE,-CAST(RIGHT(stime,1) as int),cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='6' AND RIGHT(stime,1)<='9'THEN DATEADD(MINUTE,-(CAST(RIGHT(stime,1) as int)-5),cast(stime as time(0)))
			END,5) 
	ORDER BY CAST([sdate] AS DATE), stime) [Rank]
    INTO #TEMP1
	FROM  Stock..StockHisotryMin WHERE stockNo=@stockID
	AND [sdate] BETWEEN @from AND @to 

	--If tick data is greater than StockHistoryMin, then it's today
	IF @ticktime>@dtdaily
	BEGIN
		print('Tickkkkkkk')
		INSERT INTO #TEMP1
		SELECT (CAST([sdate] AS DATE)) [sdate], 
		CAST(CAST([sdate] AS DATE) AS VARCHAR) + ' ' +
			LEFT(CASE WHEN RIGHT(stime,1)='0' THEN DATEADD(MINUTE,-5,cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='1' AND RIGHT(stime,1)<='5'THEN DATEADD(MINUTE,-CAST(RIGHT(stime,1) as int),cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='6' AND RIGHT(stime,1)<='9'THEN DATEADD(MINUTE,-(CAST(RIGHT(stime,1) as int)-5),cast(stime as time(0)))
			END,5) AS stime2,
		CONVERT(DECIMAL(8,2), [nopen]/100) [open] , 
		CONVERT(DECIMAL(8,2), High/100) [High],
		CONVERT(DECIMAL(8,2), Low/100) [lowest], 
		CONVERT(DECIMAL(8,2), nClose/100) [close], [vol] ,
		RANK() OVER (partition by 
		CAST(CAST([sdate] AS DATE) AS VARCHAR) + ' ' +
			LEFT(CASE WHEN RIGHT(stime,1)='0' THEN DATEADD(MINUTE,-5,cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='1' AND RIGHT(stime,1)<='5'THEN DATEADD(MINUTE,-CAST(RIGHT(stime,1) as int),cast(stime as time(0)))
			WHEN RIGHT(stime,1)>='6' AND RIGHT(stime,1)<='9'THEN DATEADD(MINUTE,-(CAST(RIGHT(stime,1) as int)-5),cast(stime as time(0)))
			END,5) 
		ORDER BY CAST([sdate] AS DATE), stime) [Rank]
		FROM  Stock..GetTodayTickAM()
	END

	SELECT stime2, MAX([Rank] ) RK INTO #TEMP2 FROM #TEMP1 GROUP BY stime2

	------------prepare index for later join
	create index idx on #TEMP1 (stime2) 
	create index idx on #TEMP2 (stime2) 

	SELECT  CAST(stime2 AS datetime) stime2, 
			MAX([open]) [open], 
			MAX(highest) highest, 
			MIN(lowest) lowest,
			MAX([close]) [close], 
			SUM(vol) vol FROM (
		SELECT S.stime2, 
		CASE WHEN [Rank]=1 THEN [open] ELSE 0 END [open], highest, lowest,
		CASE WHEN [Rank]=RK THEN [close] ELSE 0 END [close] , vol, T.RK 
		FROM #TEMP1 S INNER JOIN #TEMP2 T ON S.stime2=T.stime2) E
	--WHERE CAST(stime2 as time) Between '00:45:00' AND '13:45:00'
	GROUP BY stime2 
	ORDER BY stime2 ASC


---------------------------------------回傳今日的Tick--------------------------------------------------
CREATE FUNCTION [dbo].[GetTodayTickAM]
(	
)
RETURNS TABLE 
AS
RETURN 
(
	SELECT stockIdx,sdate, ' ' + LEFT(stime,5) AS stime ,  nOpen, High, Low, nClose, nQty AS vol FROM (
	SELECT stockIdx, SUBSTRING(LTRIM(Str(S.ndate)),5,2) +'/'+RIGHT(S.ndate,2)+'/'+ LEFT(S.ndate,4) AS sdate,
					   DATEADD(MINUTE, 1 ,DATEADD(hour, (Time2 / 100) % 100,
					   DATEADD(minute, (Time2 / 1) % 100, cast('00:00:00' as time(0)))))  AS stime,
       Max(nClose)                                                                AS High,
       Min(nClose)                                                                AS Low,
       dbo.Ptrvalue(Min(Ptr))                                                     AS nOpen,
       dbo.Ptrvalue(Max(Ptr))                                                     AS nClose,
       Sum(nQty)                                                                  AS nQty
	FROM   [Stock].[dbo].[TickData] X
    INNER JOIN (SELECT ndate, lTimehms / 100 AS Time2 FROM   [Stock].[dbo].[TickData] 
				GROUP  BY ndate,lTimehms / 100) S
                ON S.ndate = X.ndate AND S.Time2 = X.lTimehms / 100 --WHERE lTimehms <=104959
	GROUP  BY Time2, S.ndate, stockIdx) E
	WHERE  CAST(stime as time(0)) >= '08:45:00' AND CAST(stime as time(0)) <= '13:45:00' 
	--AND cast(sdate as date) = cast(GETDATE() as date) 
)

---------------------------------------回傳日K的sp--------------------------------------------------
CREATE procedure [dbo].[sp_GetTicksDaily]
@from date,
@to date,
@stockID varchar(8)

AS
BEGIN

SET NOCOUNT ON
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED

DECLARE @dtdaily date, @ticktime date
SELECT @dtdaily = MAX(CAST([sdate] as date)) FROM Stock.dbo.StockHistoryDaily
SELECT @ticktime = MAX(CONVERT(datetime,convert(char(8),ndate))) FROM Stock.dbo.TickData

IF @ticktime>@dtdaily
BEGIN
	DECLARE @tickopen float, @tickclose float, @tickhigh float, @ticklow float, @tickvol int
	SELECT @tickopen = nClose FROM Stock.dbo.TickData WHERE Ptr=(SELECT MIN(Ptr) FROM Stock.dbo.TickData WHERE ndate=FORMAT(@ticktime,'yyyyMMdd') AND lTimehms BETWEEN 84500 AND 134500)
	SELECT @tickclose = nClose FROM Stock.dbo.TickData WHERE Ptr=(SELECT MAX(Ptr) FROM Stock.dbo.TickData WHERE ndate=FORMAT(@ticktime,'yyyyMMdd') AND lTimehms BETWEEN 84500 AND 134500)
	SELECT @tickhigh = MAX(nClose) FROM Stock.dbo.TickData WHERE ndate=FORMAT(@ticktime,'yyyyMMdd') AND lTimehms BETWEEN 84500 AND 134500
	SELECT @ticklow = MIN(nClose) FROM Stock.dbo.TickData WHERE ndate=FORMAT(@ticktime,'yyyyMMdd') AND lTimehms BETWEEN 84500 AND 134500
	SELECT @tickvol = SUM(nQty) FROM Stock.dbo.TickData WHERE ndate=FORMAT(@ticktime,'yyyyMMdd') AND lTimehms BETWEEN 84500 AND 134500

	SELECT @ticktime AS [sdate] , CONVERT(DECIMAL(8,2), @tickopen/100), CONVERT(DECIMAL(8,2), @tickhigh/100), CONVERT(DECIMAL(8,2), @ticklow/100), CONVERT(DECIMAL(8,2), @tickclose/100), @tickvol
	UNION

	SELECT CAST([sdate] as date) AS [sdate],CONVERT(DECIMAL(8,2), [open]/100) , CONVERT(DECIMAL(8,2), [highest]/100)  ,CONVERT(DECIMAL(8,2), [lowest]/100),  
				CONVERT(DECIMAL(8,2), [close]/100), [vol] FROM Stock.dbo.StockHistoryDaily WHERE stockNo=@stockID AND CAST([sdate] as date) 
				 BETWEEN @from AND @to 
	ORDER BY [sdate] ASC
END

ELSE
BEGIN
	SELECT CAST([sdate] as date) AS [sdate],CONVERT(DECIMAL(8,2), [open]/100) , CONVERT(DECIMAL(8,2), [highest]/100)  ,CONVERT(DECIMAL(8,2), [lowest]/100),  
				CONVERT(DECIMAL(8,2), [close]/100), [vol] FROM Stock.dbo.StockHistoryDaily WHERE stockNo=@stockID AND CAST([sdate] as date) 
				 BETWEEN @from AND @to 
	ORDER BY [sdate] ASC
END
END
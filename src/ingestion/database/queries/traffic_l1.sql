-- 一级流量源查询
-- 对应Excel工作表: 一级流量源
-- 说明: 按一级流量源分组的流量和销售数据

SELECT
    YEAR(dtm.date) as year,
    MONTH(dtm.date) as month,
    dtm.traffic_source_l1 as source_name,
    dtm.channel,
    dtm.traffic_type,
    -- 核心指标
    SUM(dtm.uv) as uv,
    SUM(dtm.buyers) as buyers,
    ROUND(SUM(dtm.buyers) / NULLIF(SUM(dtm.uv), 0) * 100, 2) as cr,
    SUM(dtm.gmv) as gmv,
    SUM(dtm.net) as net,
    -- 可选: AOV和ATV
    SUM(dtm.gmv) / NULLIF(SUM(dtm.orders), 0) as aov,
    SUM(dtm.gmv) / NULLIF(SUM(dtm.buyers), 0) as atv
FROM daily_traffic_metrics dtm
WHERE DATE(dtm.date) BETWEEN %s AND %s
    AND dtm.source_level = 1
GROUP BY YEAR(dtm.date), MONTH(dtm.date),
         dtm.traffic_source_l1, dtm.channel, dtm.traffic_type
ORDER BY year, month, SUM(dtm.uv) DESC;

-- 参数:
--   1. start_date (string): 开始日期, 格式 'YYYY-MM-DD'
--   2. end_date (string): 结束日期, 格式 'YYYY-MM-DD'

-- 说明:
--   - traffic_source_l1: 一级流量源名称
--   - traffic_type: 流量类型 (paid/free/organic)
--   - source_level = 1: 只查询一级流量源
--   - 按UV降序排列，找出主要流量源

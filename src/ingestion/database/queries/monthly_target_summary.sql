-- 月度目标汇总查询
-- 说明: 从数据库读取日度目标并按月汇总（PFS + DTC）
-- FF目标从Excel单独读取，然后在Python中合并

SELECT
    YEAR(Date) as year,
    MONTH(Date) as month,
    channel,
    -- 核心指标汇总
    SUM(gmv) as gmv,
    SUM(net) as net,
    SUM(net_units) as net_units,
    SUM(gmv_units) as gmv_units,
    SUM(uv) as uv,
    SUM(buyers) as buyers,
    SUM(free_traffic) as free_traffic,
    SUM(paid_traffic) as paid_traffic,
    -- DTC细分渠道汇总
    SUM(dtc_social_net) as dtc_social_net,
    SUM(dtc_social_gmv) as dtc_social_gmv,
    SUM(dtc_social_traffic) as dtc_social_traffic,
    SUM(dtc_organic_net) as dtc_organic_net,
    SUM(dtc_organic_gmv) as dtc_organic_gmv,
    SUM(dtc_organic_traffic) as dtc_organic_traffic,
    -- 计算有多少天的数据
    COUNT(DISTINCT Date) as days
FROM dunhill_pfs_target
WHERE Date BETWEEN %s AND %s
GROUP BY YEAR(Date), MONTH(Date), channel
ORDER BY year, month, channel;

-- 参数:
--   1. start_date (string): 开始日期, 格式 'YYYY-MM-DD'
--   2. end_date (string): 结束日期, 格式 'YYYY-MM-DD'

-- 说明:
--   - 按月汇总日度目标数据
--   - 返回PFS和DTC渠道的月度目标
--   - FF目标从Excel读取后在Python中合并

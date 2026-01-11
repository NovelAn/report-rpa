-- 月度汇总查询
-- 对应Excel工作表: 全店核心数据_bymonth
-- 说明: 基于目标表数据计算月度汇总

SELECT
    YEAR(dkm.date) as year,
    MONTH(dkm.date) as month,
    dkm.channel,
    -- 核心指标聚合
    SUM(dkm.gmv) as gmv,
    SUM(dkm.net) as net,
    SUM(dkm.uv) as uv,
    SUM(dkm.buyers) as buyers,
    SUM(dkm.orders) as orders,
    SUM(dkm.paid_traffic) as paid_traffic,
    SUM(dkm.free_traffic) as free_traffic,
    -- 退款指标聚合
    SUM(dkm.cancel_amount) as cancel_amount,
    SUM(dkm.return_amount) as return_amount,
    -- DTC细分渠道聚合
    SUM(dkm.dtc_social_net) as dtc_social_net,
    SUM(dkm.dtc_social_gmv) as dtc_social_gmv,
    SUM(dkm.dtc_ff_net) as dtc_ff_net,
    SUM(dkm.dtc_ff_gmv) as dtc_ff_gmv,
    SUM(dkm.dtc_ad_net) as dtc_ad_net,
    SUM(dkm.dtc_ad_gmv) as dtc_ad_gmv,
    SUM(dkm.dtc_organic_net) as dtc_organic_net,
    SUM(dkm.dtc_organic_gmv) as dtc_organic_gmv
FROM daily_kpi_metrics dkm
WHERE DATE(dkm.date) BETWEEN %s AND %s
    AND dkm.channel IN ('PFS', 'DTC', 'TOTAL')
GROUP BY YEAR(dkm.date), MONTH(dkm.date), dkm.channel
ORDER BY year, month, channel;

-- 参数:
--   1. start_date (string): 开始日期, 格式 'YYYY-MM-DD'
--   2. end_date (string): 结束日期, 格式 'YYYY-MM-DD'

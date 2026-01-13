-- 目标表查询: 日度KPI指标
-- 对应Excel工作表: 目标表
-- 说明: 查询指定日期范围内的日度核心业务指标

SELECT
    DATE(dkm.date) as Date,
    dkm.channel,
    -- 核心销售指标
    dkm.gmv,
    dkm.net,
    dkm.net_units,
    dkm.gmv_units,
    -- 流量指标
    dkm.uv,
    dkm.buyers,
    dkm.orders,
    dkm.paid_traffic,
    dkm.free_traffic,
    -- 退款指标
    dkm.rrc,
    dkm.cancel_amount,
    dkm.return_amount,
    -- DTC细分渠道 - Social (社群推广)
    dkm.dtc_social_net,
    dkm.dtc_social_gmv,
    dkm.dtc_social_traffic,
    dkm.dtc_social_spend,
    -- DTC细分渠道 - FF (员工福利)
    dkm.dtc_ff_net,
    dkm.dtc_ff_gmv,
    dkm.dtc_ff_traffic,
    -- DTC细分渠道 - Organic (自然流量)
    dkm.dtc_organic_net,
    dkm.dtc_organic_gmv,
    dkm.dtc_organic_traffic,
FROM daily_kpi_metrics dkm
WHERE DATE(dkm.date) BETWEEN %s AND %s
    AND dkm.channel IN ('PFS', 'DTC', 'TOTAL')
ORDER BY dkm.date, dkm.channel;

-- 参数:
--   1. start_date (string): 开始日期, 格式 'YYYY-MM-DD'
--   2. end_date (string): 结束日期, 格式 'YYYY-MM-DD'

-- 说明:
--   - 查询指定日期范围内的所有日度数据
--   - 包含PFS、DTC、TOTAL三个渠道
--   - 包含DTC的四个细分渠道数据
--   - 用于日度聚合和月度汇总

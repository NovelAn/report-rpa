"""
月度目标和YTD目标读取 - 使用示例
"""

# 示例1：获取月度目标（DataFrame格式）
from src.ingestion import get_monthly_targets

# 获取2025年11月的月度目标
df_monthly = get_monthly_targets(
    year=2025,
    month=11,
    excel_path="data/input/FF目标填报模板_2025财年.csv"
)

# 查看数据
print("=" * 80)
print("月度目标数据")
print("=" * 80)
print(df_monthly[['channel', 'gmv', 'net', 'source']])


# 示例2：获取YTD累计目标（DataFrame格式）
from src.ingestion import get_ytd_targets

# 获取2025年11月的YTD目标（2025年4月-11月累计）
df_ytd = get_ytd_targets(
    year=2025,
    month=11,
    excel_path="data/input/FF目标填报模板_2025财年.csv"
)

# 查看数据
print("\n" + "=" * 80)
print("YTD累计目标数据（财年4月开始累计）")
print("=" * 80)
print(df_ytd[['channel', 'gmv', 'net', 'source']])


# 示例3：字典格式
from src.ingestion import get_monthly_targets_dict, get_ytd_targets_dict

# 月度目标（字典格式）
monthly_targets = get_monthly_targets_dict(
    year=2025,
    month=11,
    excel_path="data/input/FF目标填报模板_2025财年.csv"
)

# YTD目标（字典格式）
ytd_targets = get_ytd_targets_dict(
    year=2025,
    month=11,
    excel_path="data/input/FF目标填报模板_2025财年.csv"
)

# 对比月度vs YTD
print("\n" + "=" * 80)
print("月度 vs YTD 对比")
print("=" * 80)
for channel in ['PFS', 'DTC', 'TOTAL']:
    monthly_gmv = monthly_targets[channel]['gmv']
    ytd_gmv = ytd_targets[channel]['gmv']
    print(f"{channel}: 月度={monthly_gmv:,.0f}, YTD累计={ytd_gmv:,.0f}")


# 示例4：遍历所有渠道
print("\n" + "=" * 80)
print("YTD各渠道详情")
print("=" * 80)
for channel, metrics in ytd_targets.items():
    print(f"\n{channel}:")
    print(f"  GMV: {metrics['gmv']:,.0f}")
    print(f"  NET: {metrics['net']:,.0f}")
    print(f"  UV: {metrics['uv']:,.0f}")
    print(f"  来源: {metrics.get('source', 'unknown')}")


# 示例5：计算完成率
# 假设有实际完成数据
# actual_gmv = 1000000
# target_gmv = monthly_targets['TOTAL']['gmv']
# achievement_rate = (actual_gmv / target_gmv * 100) if target_gmv > 0 else 0
# print(f"\nGMV完成率: {achievement_rate:.1f}%")


# 示例6：数据结构说明
"""
数据来源:
- PFS, DTC: 从数据库读取
  - 月度: 日度目标 → SQL按月汇总
  - YTD: 日度目标 → SQL按财年累计（4月到指定月）
- DTC_FF: 从Excel读取
  - 月度: 直接读取该月目标
  - YTD: 累加财年所有月份的FF目标
- DTC_EXCL_FF: 计算得出（DTC - DTC_FF）
- TOTAL: 计算得出（PFS + DTC）

财年定义:
- 财年从4月1日开始
- 例如: 2025年11月的YTD = 2025年4月到11月的累计
- 跨年情况: 2025年2月的YTD = 2024年4月到2025年2月的累计

Excel格式要求:
工作表: 包含"目标"字样的工作表
列名: 年份, 月份, 渠道, GMV目标, NET目标, UV目标, Buyers目标
FF数据: 渠道='FF' 或 'DTC_FF'
"""

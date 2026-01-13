"""
测试月度目标和YTD目标读取（简化版）
数据库月度汇总 + pandas读取Excel FF
"""

import sys
from pathlib import Path
sys.path.insert(0, '.')

from src.ingestion import get_monthly_targets, get_ytd_targets

def test_monthly():
    """测试月度目标读取"""
    print("\n" + "="*80)
    print("测试1：获取月度目标数据（数据库 + Excel）")
    print("="*80)

    # 获取2025年12月的月度目标
    year = 2025
    month = 12
    excel_path = "data/input/FF目标填报模板_2025财年.csv"  # 根据实际情况调整

    print(f"\n查询: {year}年{month}月")
    print(f"Excel: {excel_path}")

    # 读取数据
    df = get_monthly_targets(year, month, excel_path=excel_path)

    if df is None:
        print("\n✗ 未读取到数据")
        return

    # 显示结果
    print("\n" + "="*80)
    print("月度目标数据")
    print("="*80)

    # 只显示关键列
    display_cols = ['channel', 'gmv', 'net', 'uv', 'buyers', 'source']
    df_display = df[display_cols].copy()

    # 格式化数字显示
    for col in ['gmv', 'net', 'uv', 'buyers']:
        df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")

    print("\n" + str(df_display))

    # 按渠道汇总统计
    print("\n" + "="*80)
    print("渠道汇总")
    print("="*80)

    for _, row in df.iterrows():
        channel = row['channel']
        print(f"\n{channel}:")
        print(f"  GMV目标: {row['gmv']:,.0f}")
        print(f"  NET目标: {row['net']:,.0f}")
        print(f"  UV目标: {row['uv']:,.0f}")
        print(f"  Buyers: {row['buyers']:,.0f}")
        print(f"  数据来源: {row['source']}")
        if 'days' in row and row['days'] > 0:
            print(f"  数据天数: {row['days']}")


def test_ytd():
    """测试YTD累计目标读取"""
    print("\n" + "="*80)
    print("测试2：获取YTD累计目标数据（财年4月开始）")
    print("="*80)

    # 获取2025年11月的YTD目标（2025年4月-11月累计）
    year = 2025
    month = 11
    excel_path = "data/input/FF目标填报模板_2025财年.csv"

    print(f"\n查询: {year}年{month}月")
    print(f"财年范围: {year}年4月 - {year}年{month}月")
    print(f"Excel: {excel_path}")

    # 读取YTD数据
    df = get_ytd_targets(year, month, excel_path=excel_path)

    if df is None:
        print("\n✗ 未读取到YTD数据")
        return

    # 显示结果
    print("\n" + "="*80)
    print("YTD累计目标数据")
    print("="*80)

    # 只显示关键列
    display_cols = ['channel', 'gmv', 'net', 'uv', 'buyers', 'source']
    df_display = df[display_cols].copy()

    # 格式化数字显示
    for col in ['gmv', 'net', 'uv', 'buyers']:
        df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")

    print("\n" + str(df_display))

    # 按渠道汇总统计
    print("\n" + "="*80)
    print("YTD渠道汇总")
    print("="*80)

    for _, row in df.iterrows():
        channel = row['channel']
        print(f"\n{channel}:")
        print(f"  GMV目标: {row['gmv']:,.0f}")
        print(f"  NET目标: {row['net']:,.0f}")
        print(f"  UV目标: {row['uv']:,.0f}")
        print(f"  Buyers: {row['buyers']:,.0f}")
        print(f"  数据来源: {row['source']}")
        if 'days' in row and row['days'] > 0:
            print(f"  数据天数: {row['days']}")

    # 计算完成率示例（假设有实际数据）
    print("\n" + "="*80)
    print("完成率计算示例")
    print("="*80)
    print("注意：需要配合实际完成数据才能计算完成率")
    print("示例:")
    print("  actual_gmv = get_actual_data(year, month)  # 从其他数据源获取")
    print("  target_gmv = df[df['channel'] == 'TOTAL']['gmv'].values[0]")
    print("  achievement_rate = (actual_gmv / target_gmv * 100)")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("MBR目标数据测试套件")
    print("="*80)

    # 测试1：月度目标
    test_monthly()

    # 测试2：YTD累计目标
    test_ytd()

    print("\n" + "="*80)
    print("测试完成")
    print("="*80)


if __name__ == "__main__":
    import pandas as pd
    main()

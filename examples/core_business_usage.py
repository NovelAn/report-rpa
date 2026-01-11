"""
渠道剔除与Core Business核心业务计算示例

本示例展示如何使用渠道剔除功能和Core Business核心业务指标计算

业务场景:
1. 剔除FF(员工福利)进行日常销售分析
2. 剔除FF和SC(社群推广)分析核心业务
3. 计算Core Business = PFS + DTC_EXCL_FF_SC

使用方式:
    python examples/core_business_usage.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.excel_reader import ExcelDataReader
from src.transformation.calculator import DataAggregator
from src.transformation.core_business_calculator import CoreBusinessCalculator
from src.transformation.channel_aggregator import ChannelAggregator
from src.models.data_schema import ChannelType
import yaml


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def example_1_basic_aggregation():
    """
    示例1: 基础聚合 - 不使用渠道剔除
    """
    print("\n" + "="*80)
    print("示例1: 基础数据聚合 (不使用渠道剔除)")
    print("="*80)

    # 模拟数据读取 (实际使用时从Excel读取)
    # reader = ExcelDataReader("path/to/template.xlsx")
    # unified_data = reader.parse_all()

    # 假设我们已经有日度数据
    # daily_metrics = unified_data.target_metrics

    # 创建聚合器
    # aggregator = DataAggregator(daily_metrics)

    # 聚合DTC数据 (包含所有来源: Social + FF + Ad + Organic)
    # dtc_metric = aggregator.aggregate_monthly(2025, 12, ChannelType.DTC)

    print("\n✓ DTC包含完整数据:")
    print("  DTC = Social + FF + Ad + Organic")
    print("  - 包含员工福利(FF)的完整销售数据")
    print("  - 包含社群推广(SC)的完整销售数据")
    print("  - 适用于总体业务概览")


def example_2_exclude_ff():
    """
    示例2: 剔除FF(员工福利)进行日常销售分析
    """
    print("\n" + "="*80)
    print("示例2: 剔除FF进行日常销售分析")
    print("="*80)

    print("\n✓ 使用场景:")
    print("  - FF是员工内部促销渠道,折扣率高,销售滞销商品")
    print("  - 剔除FF后可以更好地反映正常业务表现")
    print("  - 适用于日常销售分析和业务监控")

    print("\n代码示例:")
    print("""
    from src.transformation.calculator import DataAggregator
    from src.models.data_schema import ChannelType

    aggregator = DataAggregator(daily_metrics)

    # 剔除FF聚合DTC数据
    dtc_excl_ff = aggregator.aggregate_monthly_with_exclusion(
        year=2025,
        month=12,
        channel=ChannelType.DTC,
        exclude_ff=True,
        exclude_social=False
    )

    # 结果: DTC_EXCL_FF = DTC - FF
    print(f"DTC剔除FF后净销售: {dtc_excl_ff.net:,.2f}")
    print(f"FF占比: {(ff_net / dtc_total.net * 100):.2f}%")
    """)


def example_3_core_business():
    """
    示例3: 计算Core Business核心业务指标
    """
    print("\n" + "="*80)
    print("示例3: 计算Core Business核心业务指标")
    print("="*80)

    print("\n✓ 业务背景:")
    print("  - SC(社群推广)是买量承诺ROI渠道,与常规广告投放不同")
    print("  - Core Business剔除FF和SC,反映核心业务能力")
    print("  - Core Business = PFS + DTC_EXCL_FF_SC")

    print("\n代码示例:")
    print("""
    from src.transformation.calculator import DataAggregator
    from src.transformation.core_business_calculator import CoreBusinessCalculator
    from src.models.data_schema import ChannelType

    aggregator = DataAggregator(daily_metrics)
    calc = CoreBusinessCalculator()

    # 步骤1: 聚合PFS数据
    pfs_metric = aggregator.aggregate_monthly(2025, 12, ChannelType.PFS)

    # 步骤2: 聚合DTC数据并剔除FF和SC
    dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
        year=2025,
        month=12,
        channel=ChannelType.DTC,
        exclude_ff=True,
        exclude_social=True
    )

    # 步骤3: 计算Core Business
    core_business = calc.calculate_core_business(pfs_metric, dtc_excl_ff_sc)

    print(f"Core Business净销售: {core_business.net:,.2f}")
    print(f"  - PFS贡献: {pfs_metric.net:,.2f} ({pfs_metric.net/core_business.net*100:.1f}%)")
    print(f"  - DTC(剔除FF&SC)贡献: {dtc_excl_ff_sc.net:,.2f} ({dtc_excl_ff_sc.net/core_business.net*100:.1f}%)")
    """)


def example_4_configuration_based():
    """
    示例4: 基于配置文件的自动化计算
    """
    print("\n" + "="*80)
    print("示例4: 基于配置文件的自动化计算")
    print("="*80)

    # 加载配置
    config = load_config()
    exclusion_config = config['processing']['channel_exclusion']

    print("\n✓ 配置文件 (config.yaml):")
    print(f"""
    processing:
      channel_exclusion:
        enabled: {exclusion_config['enabled']}
        dtc_exclusions:
          exclude_ff: {exclusion_config['dtc_exclusions']['exclude_ff']}
          exclude_social: {exclusion_config['dtc_exclusions']['exclude_social']}
          exclude_ff_and_social: {exclusion_config['dtc_exclusions']['exclude_ff_and_social']}
        calculate_derived_channels:
          {exclusion_config['calculate_derived_channels']}
    """)

    print("\n代码示例:")
    print("""
    import yaml
    from src.transformation.calculator import DataAggregator
    from src.transformation.core_business_calculator import CoreBusinessCalculator

    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    exclusion = config['processing']['channel_exclusion']['dtc_exclusions']

    # 根据配置创建计算器
    calc = CoreBusinessCalculator(
        exclude_ff=exclusion['exclude_ff'],
        exclude_social=exclusion['exclude_social'],
        calculate_derived=True
    )

    aggregator = DataAggregator(daily_metrics)

    # 使用配置进行聚合
    dtc_metric = calc.aggregate_monthly_with_exclusion(
        daily_metrics=daily_metrics,
        year=2025,
        month=12,
        channel=ChannelType.DTC,
        exclusion_config={
            'exclude_ff': exclusion['exclude_ff'],
            'exclude_social': exclusion['exclude_social']
        }
    )

    # 自动计算所有派生渠道
    all_metrics = calc.calculate_all_derived_channels([dtc_metric, pfs_metric])
    """)


def example_5_channel_comparison():
    """
    示例5: 渠道对比分析
    """
    print("\n" + "="*80)
    print("示例5: 渠道对比分析")
    print("="*80)

    print("\n✓ 多维度渠道对比:")
    print("""
    指标              TOTAL       DTC         DTC_EXCL_FF   DTC_EXCL_FF_SC  CORE_BUSINESS
    ──────────────────────────────────────────────────────────────────────────────
    NET销售          10,000,000   6,000,000    5,700,000     5,000,000       8,500,000
    YoY增长          +15.2%       +18.5%       +19.3%        +21.2%          +16.8%
    UV               500,000      300,000      285,000       250,000         420,000
    CR (%)           3.2          3.5          3.6           3.8             3.4
    AOV              2,000        2,100        2,120         2,200           2,050

    分析洞察:
    1. FF渠道贡献: 300K (5% of DTC)
    2. SC渠道贡献: 700K (11.7% of DTC)
    3. 剔除FF&SC后,CR和AOV显著提升,反映核心业务质量更高
    4. Core Business YoY +16.8%,体现真实业务增长
    """)


def example_6_complete_workflow():
    """
    示例6: 完整工作流
    """
    print("\n" + "="*80)
    print("示例6: 完整工作流 (从Excel读取到Core Business计算)")
    print("="*80)

    print("""
    # 完整工作流代码
    import yaml
    from src.ingestion.excel_reader import ExcelDataReader
    from src.transformation.calculator import DataAggregator
    from src.transformation.core_business_calculator import CoreBusinessCalculator
    from src.models.data_schema import ChannelType

    # 1. 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 2. 读取Excel数据
    reader = ExcelDataReader("MBR数据模板.xlsx")
    unified_data = reader.parse_all()
    daily_metrics = unified_data.target_metrics

    # 3. 创建聚合器和计算器
    aggregator = DataAggregator(daily_metrics)
    calc = CoreBusinessCalculator(
        exclude_ff=config['processing']['channel_exclusion']['dtc_exclusions']['exclude_ff'],
        exclude_social=config['processing']['channel_exclusion']['dtc_exclusions']['exclude_social'],
        calculate_derived=True
    )

    # 4. 聚合各渠道数据 (2025年12月)
    pfs = aggregator.aggregate_monthly(2025, 12, ChannelType.PFS)
    dtc = aggregator.aggregate_monthly(2025, 12, ChannelType.DTC)

    # 5. 计算剔除渠道后的DTC
    dtc_excl_ff = aggregator.aggregate_monthly_with_exclusion(
        2025, 12, ChannelType.DTC, exclude_ff=True, exclude_social=False
    )
    dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
        2025, 12, ChannelType.DTC, exclude_ff=True, exclude_social=True
    )

    # 6. 计算Core Business
    core_business = calc.calculate_core_business(pfs, dtc_excl_ff_sc)

    # 7. 输出对比报告
    print(f"\\n{'='*60}")
    print(f"2025年12月 渠道销售对比")
    print(f"{'='*60}")
    print(f"PFS:                    {pfs.net:>15,.2f}")
    print(f"DTC (完整):             {dtc.net:>15,.2f}")
    print(f"DTC excl FF:            {dtc_excl_ff.net:>15,.2f} (剔除FF: {dtc.net - dtc_excl_ff.net:>12,.2f})")
    print(f"DTC excl FF&SC:         {dtc_excl_ff_sc.net:>15,.2f} (剔除SC: {dtc_excl_ff.net - dtc_excl_ff_sc.net:>12,.2f})")
    print(f"─" * 60)
    print(f"CORE BUSINESS:          {core_business.net:>15,.2f} (PFS + DTC excl FF&SC)")
    print(f"{'='*60}\\n")

    # 8. 计算所有派生渠道指标
    monthly_metrics = [pfs, dtc, dtc_excl_ff, dtc_excl_ff_sc, core_business]
    all_metrics = calc.calculate_all_derived_channels(monthly_metrics)

    print(f"✓ 计算完成! 共生成 {len(all_metrics)} 个渠道指标")
    """)


def main():
    """运行所有示例"""
    print("\n" + "="*80)
    print("MBR自动化系统 - 渠道剔除与Core Business计算示例")
    print("="*80)

    example_1_basic_aggregation()
    example_2_exclude_ff()
    example_3_core_business()
    example_4_configuration_based()
    example_5_channel_comparison()
    example_6_complete_workflow()

    print("\n" + "="*80)
    print("✓ 所有示例展示完成!")
    print("="*80)
    print("\n相关文件:")
    print("  - src/models/data_schema.py: 数据模型定义 (FF字段、渠道类型)")
    print("  - src/transformation/core_business_calculator.py: 核心业务计算器")
    print("  - src/transformation/calculator.py: 数据聚合器 (支持渠道剔除)")
    print("  - src/transformation/channel_aggregator.py: 渠道汇总器")
    print("  - config.yaml: 配置文件 (渠道剔除配置)")
    print("\n")


if __name__ == "__main__":
    main()

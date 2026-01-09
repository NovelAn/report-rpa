"""
MBR自动化系统 - 基础工作流测试
测试从Excel读取到数据验证的完整流程
"""

import sys
from pathlib import Path

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.excel_reader import ExcelDataReader
from src.transformation.calculator import DataAggregator, MetricCalculator
from src.validation.validator import DataValidator
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主测试函数"""
    print("=" * 60)
    print("MBR自动化系统 - 基础工作流测试")
    print("=" * 60)

    # Excel文件路径
    excel_file = Path("dec-25/MBR数据模板.xlsx")

    if not excel_file.exists():
        print(f"\n错误: Excel文件不存在: {excel_file}")
        print("请确保文件路径正确")
        return

    try:
        # Step 1: 读取Excel数据
        print("\n[Step 1] 读取Excel数据...")
        reader = ExcelDataReader(excel_file)
        data = reader.parse_all()

        print(f"  ✓ 成功读取数据")
        print(f"  - 报告期间: {data.report_period}")
        print(f"  - 品牌: {data.brand}")
        print(f"  - 日度指标数: {len(data.target_metrics)}")
        print(f"  - 活动数: {len(data.campaigns)}")

        # Step 2: 数据聚合
        print("\n[Step 2] 聚合月度数据...")
        if data.target_metrics:
            aggregator = DataAggregator(data.target_metrics)

            # 计算所有月度指标
            monthly_metrics = aggregator.calculate_all_monthly()
            print(f"  ✓ 计算了 {len(monthly_metrics)} 个月度指标")

            # 计算YoY增长率
            monthly_metrics = aggregator.calculate_yoy_for_all(monthly_metrics)
            print(f"  ✓ 计算了YoY增长率")

            # 计算MoM增长率
            monthly_metrics = aggregator.calculate_mom_for_all(monthly_metrics)
            print(f"  ✓ 计算了MoM增长率")

            # 更新报告数据
            data.monthly_metrics = monthly_metrics

            # 显示部分月度数据
            print("\n  月度数据示例 (前3条):")
            for metric in monthly_metrics[:3]:
                yoy_str = f"{metric.yoy_growth:+.1f}%" if metric.yoy_growth else "N/A"
                print(f"    {metric.channel} {metric.period}: "
                      f"NET={metric.net:,.0f}, YoY={yoy_str}")

        # Step 3: 数据验证
        print("\n[Step 3] 验证数据质量...")
        validator = DataValidator(strict_mode=False)
        validation_result = validator.validate_report_data(data)

        print(f"  验证结果:")
        print(f"  - 是否通过: {'✓ 是' if validation_result.is_valid else '✗ 否'}")
        print(f"  - 错误数: {validation_result.error_count}")
        print(f"  - 警告数: {validation_result.warning_count}")
        print(f"  - 质量评分: {validation_result.score:.1f}/100")

        if validation_result.errors:
            print(f"\n  错误详情:")
            for error in validation_result.errors[:3]:
                print(f"    ✗ {error}")
            if len(validation_result.errors) > 3:
                print(f"    ... 还有 {len(validation_result.errors) - 3} 个错误")

        if validation_result.warnings:
            print(f"\n  警告详情:")
            for warning in validation_result.warnings[:3]:
                print(f"    ⚠ {warning}")
            if len(validation_result.warnings) > 3:
                print(f"    ... 还有 {len(validation_result.warnings) - 3} 个警告")

        # Step 4: 数据统计
        print("\n[Step 4] 数据统计摘要...")

        if data.target_metrics:
            # 按渠道统计
            channels = {}
            for metric in data.target_metrics:
                ch = metric.channel.value
                if ch not in channels:
                    channels[ch] = {'net': 0, 'gmv': 0, 'uv': 0}
                channels[ch]['net'] += metric.net or 0
                channels[ch]['gmv'] += metric.gmv or 0
                channels[ch]['uv'] += metric.uv or 0

            print(f"\n  按渠道汇总:")
            for channel, stats in sorted(channels.items()):
                print(f"    {channel}:")
                print(f"      - GMV: {stats['gmv']:,.0f}")
                print(f"      - NET: {stats['net']:,.0f}")
                print(f"      - UV: {stats['uv']:,.0f}")

        # Step 5: 计算示例
        print("\n[Step 5] 计算器功能演示...")

        # YoY计算示例
        yoy = MetricCalculator.calculate_yoy(1500000, 1000000)
        print(f"  YoY计算示例:")
        print(f"    当期: 1,500,000")
        print(f"    去年同期: 1,000,000")
        print(f"    YoY增长率: {yoy:+.1f}%")

        # MoM计算示例
        mom = MetricCalculator.calculate_mom(120000, 100000)
        print(f"\n  MoM计算示例:")
        print(f"    当月: 120,000")
        print(f"    上月: 100,000")
        print(f"    MoM增长率: {mom:+.1f}%")

        # CR计算示例
        cr = MetricCalculator.calculate_cr(500, 10000)
        print(f"\n  CR计算示例:")
        print(f"    购买人数: 500")
        print(f"    UV: 10,000")
        print(f"    转化率: {cr:.2f}%")

        # 完成提示
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

        if validation_result.is_valid:
            print("\n✓ 数据验证通过,可以进行下一步处理")
        else:
            print("\n⚠ 数据验证未完全通过,请检查错误和警告")

    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n提示: 这是Phase 1的基础功能测试")
    print("后续将实现: Phase 2 (AI洞察) → Phase 3 (PPT生成) → Phase 4 (Claude Skill)")


if __name__ == "__main__":
    main()

"""
MBR自动化系统 - 主入口文件

这是运行MBR月报自动化系统的主要入口点。
展示从数据读取、处理、验证到输出报告的完整工作流程。

使用方式:
    # 方式1: 使用默认配置
    python main.py

    # 方式2: 指定配置文件
    python main.py --config config.yaml

    # 方式3: 指定输入Excel文件
    python main.py --input path/to/MBR数据模板.xlsx

    # 方式4: 指定报告期间
    python main.py --period 2025-12

示例:
    python main.py --input data/input/MBR数据模板.xlsx --period 2025-12
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
import yaml

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion.excel_reader import ExcelDataReader
from src.transformation.calculator import DataAggregator
from src.transformation.core_business_calculator import CoreBusinessCalculator
from src.transformation.channel_aggregator import ChannelAggregator
from src.validation.validator import DataValidator
from src.models.data_schema import ChannelType, UnifiedReportData


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('outputs/logs/app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class MBRAutomationPipeline:
    """
    MBR自动化处理管道
    实现从数据读取到报告生成的完整流程
    """

    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化处理管道

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.config_path = config_path

        logger.info("="*80)
        logger.info("MBR自动化系统启动")
        logger.info("="*80)
        logger.info(f"配置文件: {config_path}")
        logger.info(f"环境: {self.config['application']['environment']}")

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("✓ 配置文件加载成功")
            return config
        except Exception as e:
            logger.error(f"✗ 配置文件加载失败: {e}")
            raise

    def run(self, input_file: str, period: str = None):
        """
        运行完整的MBR自动化处理流程

        Args:
            input_file: 输入Excel文件路径
            period: 报告期间 (YYYY-MM格式)

        Returns:
            UnifiedReportData: 统一报告数据对象
        """
        try:
            # === Step 1: 数据读取 ===
            logger.info("\n" + "="*80)
            logger.info("Step 1: 数据读取")
            logger.info("="*80)

            unified_data = self._read_data(input_file)

            # === Step 2: 数据聚合 ===
            logger.info("\n" + "="*80)
            logger.info("Step 2: 数据聚合")
            logger.info("="*80)

            monthly_metrics = self._aggregate_data(unified_data, period)

            # === Step 3: 渠道汇总 ===
            logger.info("\n" + "="*80)
            logger.info("Step 3: 渠道汇总")
            logger.info("="*80)

            channel_metrics = self._aggregate_channels(monthly_metrics)

            # === Step 4: Core Business计算 ===
            logger.info("\n" + "="*80)
            logger.info("Step 4: Core Business计算")
            logger.info("="*80)

            core_business_metrics = self._calculate_core_business(channel_metrics)

            # === Step 5: 数据验证 ===
            logger.info("\n" + "="*80)
            logger.info("Step 5: 数据验证")
            logger.info("="*80)

            validation_result = self._validate_data(unified_data)

            # === Step 6: 生成报告摘要 ===
            logger.info("\n" + "="*80)
            logger.info("Step 6: 生成报告摘要")
            logger.info("="*80)

            self._generate_summary(channel_metrics, core_business_metrics)

            logger.info("\n" + "="*80)
            logger.info("✓ MBR自动化处理完成!")
            logger.info("="*80)

            return unified_data

        except Exception as e:
            logger.error(f"\n✗ 处理失败: {e}", exc_info=True)
            raise

    def _read_data(self, input_file: str) -> UnifiedReportData:
        """
        Step 1: 读取Excel数据

        Args:
            input_file: Excel文件路径

        Returns:
            UnifiedReportData: 统一报告数据
        """
        logger.info(f"读取文件: {input_file}")

        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件不存在: {input_file}")

        # 读取Excel数据
        reader = ExcelDataReader(input_file)
        unified_data = reader.parse_all()

        logger.info(f"✓ 数据读取完成:")
        logger.info(f"  - 日度数据条数: {len(unified_data.target_metrics)}")
        logger.info(f"  - Campaign活动数: {len(unified_data.campaigns)}")
        logger.info(f"  - 流量源数量: {sum(len(v) for v in unified_data.traffic_sources.values())}")

        return unified_data

    def _aggregate_data(
        self,
        unified_data: UnifiedReportData,
        period: str = None
    ) -> list:
        """
        Step 2: 聚合日度数据为月度数据

        Args:
            unified_data: 统一报告数据
            period: 报告期间 (YYYY-MM)

        Returns:
            月度指标列表
        """
        # 解析期间
        if period:
            year, month = map(int, period.split('-'))
        else:
            # 使用最新数据的期间
            latest_metric = max(unified_data.target_metrics, key=lambda m: m.date)
            year, month = latest_metric.date.year, latest_metric.date.month

        logger.info(f"聚合期间: {year}-{month:02d}")

        # 创建聚合器
        aggregator = DataAggregator(unified_data.target_metrics)

        # 获取渠道剔除配置
        exclusion_config = self.config['processing']['channel_exclusion']
        dtc_exclusions = exclusion_config['dtc_exclusions']

        # 聚合各渠道数据
        monthly_metrics = []

        # 1. PFS渠道
        pfs = aggregator.aggregate_monthly(year, month, ChannelType.PFS)
        if pfs:
            monthly_metrics.append(pfs)
            logger.info(f"✓ PFS: NET={pfs.net:,.2f}, GMV={pfs.gmv:,.2f}")

        # 2. DTC渠道 (完整)
        dtc = aggregator.aggregate_monthly(year, month, ChannelType.DTC)
        if dtc:
            monthly_metrics.append(dtc)
            logger.info(f"✓ DTC: NET={dtc.net:,.2f}, GMV={dtc.gmv:,.2f}")

        # 3. DTC_EXCL_FF (如果配置要求)
        if dtc_exclusions['exclude_ff']:
            dtc_excl_ff = aggregator.aggregate_monthly_with_exclusion(
                year, month, ChannelType.DTC,
                exclude_ff=True,
                exclude_social=False
            )
            if dtc_excl_ff:
                monthly_metrics.append(dtc_excl_ff)
                logger.info(f"✓ DTC_EXCL_FF: NET={dtc_excl_ff.net:,.2f}, GMV={dtc_excl_ff.gmv:,.2f}")

        # 4. DTC_EXCL_FF_SC (如果配置要求)
        if dtc_exclusions['exclude_ff'] or dtc_exclusions['exclude_social']:
            dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
                year, month, ChannelType.DTC,
                exclude_ff=dtc_exclusions['exclude_ff'],
                exclude_social=dtc_exclusions['exclude_social']
            )
            if dtc_excl_ff_sc:
                monthly_metrics.append(dtc_excl_ff_sc)
                logger.info(f"✓ DTC_EXCL_FF_SC: NET={dtc_excl_ff_sc.net:,.2f}, GMV={dtc_excl_ff_sc.gmv:,.2f}")

        return monthly_metrics

    def _aggregate_channels(self, monthly_metrics: list) -> dict:
        """
        Step 3: 计算渠道层级汇总

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            按渠道组织的字典
        """
        logger.info("计算渠道汇总...")

        # 使用渠道汇总器
        channels = ChannelAggregator.calculate_channel_breakdown(monthly_metrics)

        # 输出TOTAL和DTC
        if ChannelType.TOTAL in channels:
            total = channels[ChannelType.TOTAL]
            logger.info(f"✓ TOTAL: NET={total.net:,.2f}, GMV={total.gmv:,.2f}")

        if ChannelType.DTC in channels:
            dtc = channels[ChannelType.DTC]
            logger.info(f"✓ DTC (汇总): NET={dtc.net:,.2f}, GMV={dtc.gmv:,.2f}")

        return channels

    def _calculate_core_business(self, channel_metrics: dict) -> dict:
        """
        Step 4: 计算Core Business核心业务指标

        Args:
            channel_metrics: 渠道指标字典

        Returns:
            包含Core Business的字典
        """
        logger.info("计算Core Business...")

        pfs = channel_metrics.get(ChannelType.PFS)
        dtc_excl_ff_sc = channel_metrics.get(ChannelType.DTC_EXCL_FF_SC)

        if pfs and dtc_excl_ff_sc:
            # 计算Core Business
            core_business = ChannelAggregator.calculate_core_business(pfs, dtc_excl_ff_sc)
            if core_business:
                channel_metrics[ChannelType.CORE_BUSINESS] = core_business
                logger.info(f"✓ CORE_BUSINESS: NET={core_business.net:,.2f}, GMV={core_business.gmv:,.2f}")
                logger.info(f"  - PFS占比: {pfs.net/core_business.net*100:.1f}%")
                logger.info(f"  - DTC_EXCL_FF_SC占比: {dtc_excl_ff_sc.net/core_business.net*100:.1f}%")
        else:
            logger.warning("缺少PFS或DTC_EXCL_FF_SC数据，无法计算Core Business")

        return channel_metrics

    def _validate_data(self, unified_data: UnifiedReportData):
        """
        Step 5: 数据验证

        Args:
            unified_data: 统一报告数据

        Returns:
            验证结果
        """
        logger.info("验证数据质量...")

        validator = DataValidator(
            strict_mode=self.config['validation']['strict_mode']
        )

        result = validator.validate_report_data(unified_data)

        logger.info(f"✓ 数据验证完成:")
        logger.info(f"  - 完整性检查: {'通过' if result.is_complete else '失败'}")
        logger.info(f"  - 质量评分: {result.quality_score}/100")
        logger.info(f"  - 错误数: {len(result.errors)}")
        logger.info(f"  - 警告数: {len(result.warnings)}")

        if result.errors:
            logger.error("验证错误:")
            for error in result.errors[:5]:  # 只显示前5个
                logger.error(f"  - {error}")

        if result.warnings:
            logger.warning("验证警告:")
            for warning in result.warnings[:5]:
                logger.warning(f"  - {warning}")

        return result

    def _generate_summary(self, channel_metrics: dict, core_business_metrics: dict):
        """
        Step 6: 生成报告摘要

        Args:
            channel_metrics: 渠道指标
            core_business_metrics: 包含Core Business的指标
        """
        logger.info("\n" + "="*80)
        logger.info("报告摘要")
        logger.info("="*80)

        # 渠道对比表
        logger.info("\n渠道销售对比:")
        logger.info(f"{'渠道':<20} {'净销售':>15} {'GMV':>15} {'UV':>12} {'CR(%)':>8}")
        logger.info("-" * 80)

        for channel_type in [
            ChannelType.TOTAL,
            ChannelType.PFS,
            ChannelType.DTC,
            ChannelType.DTC_EXCL_FF,
            ChannelType.DTC_EXCL_FF_SC,
            ChannelType.CORE_BUSINESS
        ]:
            if channel_type in core_business_metrics:
                metric = core_business_metrics[channel_type]
                logger.info(
                    f"{channel_type.value:<20} "
                    f"{metric.net:>15,.2f} "
                    f"{metric.gmv:>15,.2f} "
                    f"{metric.uv:>12,} "
                    f"{metric.cr:>8.2f}"
                )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MBR月报自动化系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py
  python main.py --config config.yaml
  python main.py --input data/input/MBR数据模板.xlsx --period 2025-12
        """
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )

    parser.add_argument(
        '--input',
        help='输入Excel文件路径'
    )

    parser.add_argument(
        '--period',
        help='报告期间，格式: YYYY-MM (例如: 2025-12)'
    )

    args = parser.parse_args()

    # 确定输入文件
    if args.input:
        input_file = args.input
    else:
        # 使用配置中的默认路径
        input_file = 'data/input/MBR数据模板.xlsx'
        logger.warning(f"未指定输入文件，使用默认路径: {input_file}")

    # 确保日志目录存在
    os.makedirs('outputs/logs', exist_ok=True)

    # 运行处理管道
    try:
        pipeline = MBRAutomationPipeline(config_path=args.config)
        result = pipeline.run(input_file=input_file, period=args.period)

        logger.info("\n✓ 处理成功完成!")
        return 0

    except FileNotFoundError as e:
        logger.error(f"\n✗ 文件未找到: {e}")
        logger.info("\n提示:")
        logger.info("  1. 请确保Excel数据文件存在")
        logger.info("  2. 使用 --input 参数指定文件路径")
        logger.info("  3. 示例: python main.py --input path/to/your/file.xlsx")
        return 1

    except Exception as e:
        logger.error(f"\n✗ 运行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

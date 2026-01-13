"""
数据库工作流测试脚本
测试从数据库读取数据并转换为业务模型
"""

import sys
import logging
from pathlib import Path
from datetime import date, datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.database import DatabaseReader
from src.models.data_schema import TargetMetric

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 80)
    print("步骤 1: 测试数据库连接")
    print("=" * 80)

    # 连接数据库 (使用默认配置文件中的第二个数据库)
    print("\n正在连接数据库...")
    print(f"配置文件: {Path.home()}/database_config.json")
    reader = DatabaseReader(1)  # 使用索引1的数据库（第二个）

    if not reader.is_connected():
        print("\n✗ 数据库连接失败")
        print("提示: 请在用户根目录创建 database_config.json 文件")
        return None

    print("✓ 数据库连接成功!")
    return reader


def explore_database(reader):
    """探索数据库结构"""
    print("\n" + "=" * 80)
    print("步骤 2: 探索数据库结构")
    print("=" * 80)

    # 获取表列表
    tables = reader.get_table_list()

    print(f"\n找到 {len(tables)} 张表:")
    for i, table in enumerate(tables[:30], 1):
        print(f"  {i:2d}. {table}")

    if len(tables) > 30:
        print(f"  ... 还有 {len(tables) - 30} 张表")

    return tables


def inspect_table(reader, table_name: str):
    """检查表结构"""
    print("\n" + "=" * 80)
    print(f"步骤 3: 检查表结构 - {table_name}")
    print("=" * 80)

    # 获取表结构
    structure = reader.get_table_structure(table_name)

    print(f"\n表 {table_name} 的字段:")
    print("-" * 80)
    print(f"{'字段名':<30} {'类型':<20} {'NULL':<10} {'键':<10} {'默认值':<15}")
    print("-" * 80)

    for field in structure:
        field_name = field.get('Field', '')
        field_type = field.get('Type', '')
        is_null = field.get('Null', '')
        key = field.get('Key', '')
        default = field.get('Default', '')

        print(f"{field_name:<30} {field_type:<20} {is_null:<10} {key:<10} {str(default):<15}")

    print("-" * 80)
    print(f"总计: {len(structure)} 个字段")


def test_sql_query(reader, query_name: str, params: tuple = None):
    """测试SQL查询"""
    print("\n" + "=" * 80)
    print(f"步骤 4: 执行SQL查询 - {query_name}")
    print("=" * 80)

    # 执行查询
    print(f"\n正在执行查询...")
    print(f"查询名称: {query_name}")

    if params:
        print(f"参数: {params}")

    results = reader.execute_sql_file(query_name, params)

    if results:
        print(f"\n✓ 查询成功! 返回 {len(results)} 条记录")

        # 显示前3条记录
        print("\n前3条记录预览:")
        print("-" * 80)

        for i, record in enumerate(results[:3], 1):
            print(f"\n记录 {i}:")
            for key, value in record.items():
                if value is not None:
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: NULL")

        print("-" * 80)
    else:
        print("\n✗ 查询返回空结果")

    return results


def convert_to_target_metrics(results: list) -> list:
    """将数据库查询结果转换为TargetMetric模型"""
    print("\n" + "=" * 80)
    print("步骤 5: 转换为数据模型")
    print("=" * 80)

    if not results:
        print("没有数据需要转换")
        return []

    metrics = []
    errors = []

    for i, record in enumerate(results, 1):
        try:
            # 创建TargetMetric实例
            metric = TargetMetric(
                date=datetime.strptime(str(record.get('Date')), '%Y-%m-%d').date(),
                channel=record.get('channel'),
                gmv=record.get('gmv'),
                net=record.get('net'),
                net_units=record.get('net_units'),
                gmv_units=record.get('gmv_units'),
                uv=record.get('uv'),
                buyers=record.get('buyers'),
                orders=record.get('orders'),
                paid_traffic=record.get('paid_traffic'),
                free_traffic=record.get('free_traffic'),
                cancel_amount=record.get('cancel_amount'),
                return_amount=record.get('return_amount'),
                dtc_social_net=record.get('dtc_social_net'),
                dtc_social_gmv=record.get('dtc_social_gmv'),
                dtc_social_traffic=record.get('dtc_social_traffic'),
                dtc_ff_net=record.get('dtc_ff_net'),
                dtc_ff_gmv=record.get('dtc_ff_gmv'),
                dtc_ff_traffic=record.get('dtc_ff_traffic'),
                dtc_ad_net=record.get('dtc_ad_net'),
                dtc_ad_gmv=record.get('dtc_ad_gmv'),
                dtc_ad_traffic=record.get('dtc_ad_traffic'),
                dtc_ad_spend=record.get('dtc_ad_spend'),
                dtc_organic_net=record.get('dtc_organic_net'),
                dtc_organic_gmv=record.get('dtc_organic_gmv'),
                dtc_organic_traffic=record.get('dtc_organic_traffic'),
            )

            metrics.append(metric)

        except Exception as e:
            errors.append(f"记录 {i}: {e}")
            logger.error(f"转换记录 {i} 失败: {e}")

    print(f"\n转换结果:")
    print(f"  成功: {len(metrics)} 条")
    print(f"  失败: {len(errors)} 条")

    if errors:
        print("\n转换错误:")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  - {error}")

    if metrics:
        print(f"\n成功转换的指标数据预览:")
        print("-" * 80)

        for i, metric in enumerate(metrics[:3], 1):
            print(f"\n记录 {i}:")
            print(f"  日期: {metric.date}")
            print(f"  渠道: {metric.channel}")
            print(f"  GMV: {metric.gmv:,}")
            print(f"  NET: {metric.net:,}")
            print(f"  UV: {metric.uv:,}")
            print(f"  Buyers: {metric.buyers:,}")
            print(f"  Orders: {metric.orders:,}")

        print("-" * 80)

    return metrics


def main():
    """主工作流"""
    print("\n" + "=" * 80)
    print("数据库工作流测试")
    print("=" * 80)

    # 步骤1: 连接数据库 (使用默认配置)
    print("\n提示: 使用 ~/database_config.json 中的第一个数据库配置")
    reader = test_database_connection()
    if not reader:
        return

    # 步骤2: 探索数据库
    tables = explore_database(reader)

    # 步骤3: 检查主要表结构
    # 查找daily_kpi_metrics表
    target_table = None
    for table in tables:
        if 'daily' in table.lower() and 'kpi' in table.lower():
            target_table = table
            break

    if target_table:
        inspect_table(reader, target_table)
    else:
        print("\n⚠ 未找到 daily_kpi_metrics 表")
        print("可用的表:")
        for table in tables[:10]:
            print(f"  - {table}")

    # 步骤4: 测试SQL查询
    # 使用target_metrics查询
    query_name = "target_metrics"

    # 查询最近一个月的数据
    end_date = date.today()
    start_date = date(end_date.year, end_date.month - 1, end_date.day)

    params = (
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

    results = test_sql_query(reader, query_name, params)

    # 步骤5: 转换为数据模型
    if results:
        metrics = convert_to_target_metrics(results)

        if metrics:
            print(f"\n✓ 成功转换 {len(metrics)} 条指标数据")

            # 验证数据
            print("\n数据验证:")
            print("-" * 80)

            for metric in metrics[:3]:
                # 计算衍生指标
                if metric.gmv and metric.orders:
                    aov = metric.gmv / metric.orders
                    print(f"\n{metric.date} - {metric.channel}:")
                    print(f"  AOV: {aov:,.2f}")

                    # 验证关系
                    if metric.buyers and metric.buyers > 0:
                        atv = metric.gmv / metric.buyers
                        print(f"  ATV: {atv:,.2f}")
                        print(f"  关系: ATV >= AOV ? {atv >= aov}")

            print("-" * 80)

    # 关闭连接
    reader.close()

    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        logger.error(f"程序出错: {e}", exc_info=True)
        print(f"\n✗ 程序出错: {e}")

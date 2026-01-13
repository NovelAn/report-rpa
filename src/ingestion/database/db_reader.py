"""
统一的数据读取器
结合了DatabaseReader和EnhancedDatabaseReader的功能
"""

import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .db_connection import DatabaseConnection
from .query_loader import QueryLoader

logger = logging.getLogger(__name__)


class DatabaseReader:
    """
    统一的数据库读取器
    支持SQL文件查询和直接SQL查询
    """

    def __init__(self, config: Union[int, str, Path, Dict[str, Any]] = 0):
        """
        初始化数据库读取器

        Args:
            config: 可以是以下类型之一
                - int: 数据库索引，从默认配置文件读取 (默认0)
                - dict: 数据库配置字典
                - str/Path: JSON配置文件路径

        Example:
            # 使用默认配置文件的第一个数据库
            reader = DatabaseReader()

            # 使用默认配置文件的第二个数据库
            reader = DatabaseReader(1)

            # 从配置字典
            reader = DatabaseReader({
                'host': 'localhost',
                'database': 'mbr_db',
                'user': 'root',
                'password': 'password'
            })

            # 从JSON配置文件
            reader = DatabaseReader("/path/to/config.json")
        """
        self.db = DatabaseConnection(config)
        self.query_loader = QueryLoader()

    def is_connected(self) -> bool:
        """检查数据库是否已连接"""
        return self.db.is_connected()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        return self.db.execute_query(query, params)

    def execute_sql_file(
        self,
        query_name: str,
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        执行SQL文件中的查询

        Args:
            query_name: 查询名称 (不含.sql后缀)
            params: 查询参数

        Returns:
            查询结果列表

        Example:
            reader = DatabaseReader("config.yaml")
            results = reader.execute_sql_file('target_metrics', ('2025-01-01', '2025-01-31'))
        """
        sql = self.query_loader.load(query_name)
        if not sql:
            logger.error(f"SQL查询加载失败: {query_name}")
            return []

        return self.execute_query(sql, params)

    # ========== 业务查询方法 ==========

    def read_target_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        读取目标表数据 (日度KPI)

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            日度指标数据列表
        """
        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))
        logger.info(f"读取目标表: {start_date} 至 {end_date}")
        return self.execute_sql_file('target_metrics', params)

    def read_monthly_summary(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        读取月度汇总数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            月度汇总数据列表
        """
        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))
        logger.info(f"读取月度汇总: {start_date} 至 {end_date}")
        return self.execute_sql_file('monthly_summary', params)

    def read_traffic_l1(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        读取一级流量源数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            一级流量源数据列表
        """
        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))
        logger.info(f"读取一级流量源: {start_date} 至 {end_date}")
        return self.execute_sql_file('traffic_l1', params)

    def read_traffic_l2(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        读取二级流量源数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            二级流量源数据列表
        """
        # 使用内联SQL，因为queries目录可能没有traffic_l2.sql
        query = """
        SELECT
            YEAR(dtm.date) as year,
            MONTH(dtm.date) as month,
            dtm.traffic_source_l2 as source_name,
            dtm.channel,
            dtm.traffic_type,
            SUM(dtm.uv) as uv,
            SUM(dtm.buyers) as buyers,
            ROUND(SUM(dtm.buyers) / NULLIF(SUM(dtm.uv), 0) * 100, 2) as cr,
            SUM(dtm.gmv) as gmv,
            SUM(dtm.net) as net
        FROM daily_traffic_metrics dtm
        WHERE DATE(dtm.date) BETWEEN %s AND %s
            AND dtm.source_level = 2
        GROUP BY YEAR(dtm.date), MONTH(dtm.date),
                 dtm.traffic_source_l2, dtm.channel, dtm.traffic_type
        ORDER BY year, month, SUM(dtm.uv) DESC
        """
        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))
        logger.info(f"读取二级流量源: {start_date} 至 {end_date}")
        return self.execute_query(query, params)

    def read_traffic_l3(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        读取三级流量源数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            三级流量源数据列表
        """
        query = """
        SELECT
            YEAR(dtm.date) as year,
            MONTH(dtm.date) as month,
            dtm.traffic_source_l3 as source_name,
            dtm.channel,
            dtm.traffic_type,
            SUM(dtm.uv) as uv,
            SUM(dtm.buyers) as buyers,
            ROUND(SUM(dtm.buyers) / NULLIF(SUM(dtm.uv), 0) * 100, 2) as cr,
            SUM(dtm.gmv) as gmv,
            SUM(dtm.net) as net
        FROM daily_traffic_metrics dtm
        WHERE DATE(dtm.date) BETWEEN %s AND %s
            AND dtm.source_level = 3
        GROUP BY YEAR(dtm.date), MONTH(dtm.date),
                 dtm.traffic_source_l3, dtm.channel, dtm.traffic_type
        ORDER BY year, month, SUM(dtm.uv) DESC
        """
        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))
        logger.info(f"读取三级流量源: {start_date} 至 {end_date}")
        return self.execute_query(query, params)

    def read_all_sources(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        读取所有数据源

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            所有数据的字典
        """
        result = {
            'target_metrics': self.read_target_metrics(start_date, end_date),
            'monthly_summary': self.read_monthly_summary(start_date, end_date),
            'traffic_l1': self.read_traffic_l1(start_date, end_date),
            'traffic_l2': self.read_traffic_l2(start_date, end_date),
            'traffic_l3': self.read_traffic_l3(start_date, end_date),
        }

        total_records = sum(len(v) if isinstance(v, list) else 0 for v in result.values())
        logger.info(f"✓ 总共读取 {total_records} 条记录")

        return result

    # ========== 实用方法 ==========

    def test_connection(self) -> bool:
        """测试数据库连接"""
        if not self.is_connected():
            return False

        try:
            result = self.execute_query("SELECT 1 as test")
            if result and result[0].get('test') == 1:
                logger.info("✓ 数据库连接测试成功")
                return True
        except Exception as e:
            logger.error(f"✗ 连接测试失败: {e}")

        return False

    def get_table_list(self) -> List[str]:
        """获取数据库中所有表名"""
        if not self.is_connected():
            return []

        try:
            results = self.execute_query("SHOW TABLES")
            tables = [list(row.values())[0] for row in results]
            logger.info(f"✓ 找到 {len(tables)} 张表")
            return tables
        except Exception as e:
            logger.error(f"✗ 获取表列表失败: {e}")
            return []

    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构

        Args:
            table_name: 表名

        Returns:
            字段信息列表
        """
        if not self.is_connected():
            return []

        try:
            results = self.execute_query(f"DESCRIBE {table_name}")
            logger.info(f"✓ 表 {table_name} 有 {len(results)} 个字段")
            return results
        except Exception as e:
            logger.error(f"✗ 获取表结构失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        self.db.close()


class HybridDataReader(DatabaseReader):
    """
    混合数据读取器
    支持数据库优先，Excel回退的模式
    """

    def __init__(self, config: Union[int, str, Path, Dict[str, Any]] = 0):
        """
        初始化混合数据读取器

        Args:
            config: 数据库索引、配置文件路径或配置字典 (默认0)
        """
        super().__init__(config)
        self._excel_reader = None  # TODO: 注入ExcelDataReader

    def read_target_metrics(
        self,
        start_date: date,
        end_date: date,
        excel_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """
        读取目标表数据 (数据库优先，Excel回退)

        Args:
            start_date: 开始日期
            end_date: 结束日期
            excel_fallback: 数据库不可用时是否回退到Excel

        Returns:
            日度指标数据列表
        """
        # 优先尝试数据库
        if self.is_connected():
            data = super().read_target_metrics(start_date, end_date)
            if data:
                logger.info("✓ 从数据库读取成功")
                return data
            else:
                logger.warning("数据库查询返回空结果")

        # 回退到Excel
        if excel_fallback:
            logger.info("回退到Excel读取")
            # TODO: 调用ExcelDataReader
            # if self._excel_reader:
            #     return self._excel_reader.read_target_metrics(start_date, end_date)
            pass

        return []


# ========== 便捷函数 ==========

def create_database_reader(
    config: Union[int, str, Path, Dict[str, Any]] = 0
) -> Optional[DatabaseReader]:
    """
    创建数据库读取器

    Args:
        config: 数据库索引、配置文件路径或配置字典 (默认0)

    Returns:
        DatabaseReader实例，如果连接失败则返回None

    Example:
        # 使用默认配置
        reader = create_database_reader()

        # 使用第二个数据库
        reader = create_database_reader(1)

        # 使用配置文件
        reader = create_database_reader("/path/to/config.json")
    """
    reader = DatabaseReader(config)
    if reader.is_connected():
        return reader
    return None

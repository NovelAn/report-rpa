"""
数据库连接和查询模块
支持MySQL数据库查询，用于直接从数据库读取MBR数据源
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import date
import os

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    数据库连接管理类
    支持MySQL数据库连接池
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据库连接

        Args:
            config: 数据库配置字典
                {
                    'host': 'localhost',
                    'port': 3306,
                    'database': 'mbr_db',
                    'user': 'readonly_user',
                    'password': 'password'
                }
        """
        self.config = config
        self.connection = None
        self._connect()

    def _connect(self):
        """建立数据库连接"""
        try:
            import pymysql
            from pymysql.cursors import DictCursor

            self.connection = pymysql.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 3306),
                user=self.config.get('user'),
                password=self.config.get('password'),
                database=self.config.get('database'),
                charset=self.config.get('charset', 'utf8mb4'),
                cursorclass=DictCursor,
                connect_timeout=10
            )
            logger.info(f"✓ 数据库连接成功: {self.config.get('database')}")

        except ImportError:
            logger.warning("pymysql未安装，数据库功能不可用")
            logger.info("安装: pip install pymysql")
            self.connection = None

        except Exception as e:
            logger.error(f"✗ 数据库连接失败: {e}")
            self.connection = None

    def is_connected(self) -> bool:
        """检查数据库是否已连接"""
        if self.connection is None:
            return False
        try:
            self.connection.ping(reconnect=True)
            return True
        except:
            return False

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表 (字典列表)
        """
        if not self.is_connected():
            logger.error("数据库未连接")
            return []

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                logger.info(f"✓ 查询执行成功: 返回 {len(results)} 条记录")
                return results

        except Exception as e:
            logger.error(f"✗ 查询执行失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")


class DatabaseReader:
    """
    数据库读取器
    从MySQL数据库读取MBR数据源
    """

    # SQL查询文件路径
    QUERIES_DIR = Path(__file__).parent.parent / "ingestion" / "database" / "queries"

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化数据库读取器

        Args:
            config_path: 配置文件路径
        """
        self.db_config = self._load_database_config(config_path)

        if self.db_config.get('enabled', False):
            self.db = DatabaseConnection(self.db_config.get('connection', {}))
        else:
            self.db = None
            logger.info("数据库查询未启用")

    def _load_database_config(self, config_path: str) -> Dict[str, Any]:
        """从配置文件加载数据库配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('data_sources', {}).get('database', {})
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {'enabled': False}

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
        if not self.db or not self.db.is_connected():
            logger.warning("数据库未连接，无法读取目标表数据")
            return []

        # 构建SQL查询
        query = """
        SELECT
            DATE(date) as Date,
            channel,
            gmv,
            net,
            net_units,
            gmv_units,
            uv,
            buyers,
            orders,
            paid_traffic,
            free_traffic,
            cancel_amount,
            return_amount,
            dtc_social_net,
            dtc_social_gmv,
            dtc_social_traffic,
            dtc_ff_net,
            dtc_ff_gmv,
            dtc_ff_traffic,
            dtc_ad_net,
            dtc_ad_gmv,
            dtc_ad_traffic,
            dtc_ad_spend,
            dtc_organic_net,
            dtc_organic_gmv,
            dtc_organic_traffic
        FROM daily_kpi_metrics
        WHERE DATE(date) BETWEEN %s AND %s
            AND channel IN ('PFS', 'DTC', 'TOTAL')
        ORDER BY date, channel
        """

        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))

        logger.info(f"读取目标表数据: {start_date} 至 {end_date}")
        return self.db.execute_query(query, params)

    def read_monthly_summary(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        读取全店核心数据_bymonth (月度汇总)

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            月度汇总数据列表
        """
        if not self.db or not self.db.is_connected():
            logger.warning("数据库未连接，无法读取月度汇总数据")
            return []

        query = """
        SELECT
            YEAR(date) as year,
            MONTH(date) as month,
            channel,
            SUM(gmv) as gmv,
            SUM(net) as net,
            SUM(uv) as uv,
            SUM(buyers) as buyers,
            SUM(orders) as orders,
            SUM(paid_traffic) as paid_traffic,
            SUM(free_traffic) as free_traffic
        FROM daily_kpi_metrics
        WHERE DATE(date) BETWEEN %s AND %s
        GROUP BY YEAR(date), MONTH(date), channel
        ORDER BY year, month, channel
        """

        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))

        logger.info(f"读取月度汇总数据: {start_date} 至 {end_date}")
        return self.db.execute_query(query, params)

    def read_traffic_sources(
        self,
        start_date: date,
        end_date: date,
        level: int = 1
    ) -> List[Dict[str, Any]]:
        """
        读取流量源数据 (一级/二级/三级)

        Args:
            start_date: 开始日期
            end_date: 结束日期
            level: 流量源层级 (1/2/3)

        Returns:
            流量源数据列表
        """
        if not self.db or not self.db.is_connected():
            logger.warning("数据库未连接，无法读取流量源数据")
            return []

        # 根据层级选择不同的字段
        if level == 1:
            source_field = 'traffic_source_l1'
        elif level == 2:
            source_field = 'traffic_source_l2'
        else:
            source_field = 'traffic_source_l3'

        query = f"""
        SELECT
            YEAR(date) as year,
            MONTH(date) as month,
            {source_field} as source_name,
            channel,
            traffic_type,
            SUM(uv) as uv,
            SUM(buyers) as buyers,
            SUM(gmv) as gmv,
            SUM(net) as net
        FROM daily_traffic_metrics
        WHERE DATE(date) BETWEEN %s AND %s
        GROUP BY YEAR(date), MONTH(date), {source_field}, channel, traffic_type
        ORDER BY year, month, uv DESC
        """

        params = (start_date.strftime('%Y-%m-%d'),
                 end_date.strftime('%Y-%m-%d'))

        logger.info(f"读取{level}级流量源数据: {start_date} 至 {end_date}")
        return self.db.execute_query(query, params)

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()


class HybridDataReader:
    """
    混合数据读取器
    支持数据库优先，Excel回退的模式
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化混合数据读取器

        Args:
            config_path: 配置文件路径
        """
        self.db_reader = DatabaseReader(config_path)
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}

    def read_target_metrics(
        self,
        start_date: date,
        end_date: date,
        excel_fallback: bool = True
    ):
        """
        读取目标表数据 (数据库优先)

        Args:
            start_date: 开始日期
            end_date: 结束日期
            excel_fallback: 数据库不可用时是否回退到Excel

        Returns:
            日度指标数据列表
        """
        # 优先尝试数据库
        if self.db_reader.db and self.db_reader.db.is_connected():
            data = self.db_reader.read_target_metrics(start_date, end_date)
            if data:
                logger.info("✓ 从数据库读取目标表数据成功")
                return data
            else:
                logger.warning("数据库查询返回空结果")

        # 回退到Excel
        if excel_fallback:
            logger.info("回退到Excel读取目标表数据")
            # TODO: 调用ExcelDataReader
            pass

        return []

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
            'monthly_summary': self.db_reader.read_monthly_summary(start_date, end_date),
            'traffic_l1': self.db_reader.read_traffic_sources(start_date, end_date, 1),
            'traffic_l2': self.db_reader.read_traffic_sources(start_date, end_date, 2),
            'traffic_l3': self.db_reader.read_traffic_sources(start_date, end_date, 3),
        }

        total_records = sum(len(v) if isinstance(v, list) else 0 for v in result.values())
        logger.info(f"✓ 总共读取 {total_records} 条记录")

        return result

    def close(self):
        """关闭连接"""
        self.db_reader.close()


# 便捷函数
def create_database_reader(config_path: str = "config.yaml") -> Optional[DatabaseReader]:
    """
    创建数据库读取器

    Args:
        config_path: 配置文件路径

    Returns:
        DatabaseReader实例，如果数据库未配置则返回None
    """
    reader = DatabaseReader(config_path)
    if reader.db and reader.db.is_connected():
        return reader
    return None

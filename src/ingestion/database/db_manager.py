"""
数据库管理器
支持从本地配置文件读取数据库连接信息
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import date

logger = logging.getLogger(__name__)


class DatabaseConfigManager:
    """数据库配置管理器"""

    # 本地配置文件路径
    DEFAULT_CONFIG_PATH = Path("C:/Users/jm024027/db_config.json")

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认使用用户配置
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.configs = self._load_configs()

    def _load_configs(self) -> Dict[str, Any]:
        """从JSON文件加载数据库配置"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}")
                return {}

            with open(self.config_path, 'r', encoding='utf-8') as f:
                configs = json.load(f)

            logger.info(f"✓ 成功加载数据库配置: {self.config_path}")
            logger.info(f"  可用数据库数量: {len(configs.get('databases', []))}")

            return configs

        except Exception as e:
            logger.error(f"✗ 加载配置文件失败: {e}")
            return {}

    def get_database_list(self) -> List[str]:
        """获取所有数据库名称"""
        databases = self.configs.get('databases', [])
        return [db.get('name', 'Unknown') for db in databases]

    def get_database_config(self, index: int = 1) -> Optional[Dict[str, Any]]:
        """
        获取指定索引的数据库配置

        Args:
            index: 数据库索引 (0-based)，默认1 (第二个数据库)

        Returns:
            数据库配置字典
        """
        databases = self.configs.get('databases', [])

        if index >= len(databases):
            logger.error(f"数据库索引 {index} 超出范围 (共 {len(databases)} 个)")
            return None

        db_config = databases[index]

        logger.info(f"✓ 选择数据库: {db_config.get('name', 'Unknown')}")

        # 转换为标准连接格式
        connection_config = {
            'host': db_config.get('host'),
            'port': db_config.get('port', 3306),
            'database': db_config.get('database'),
            'user': db_config.get('user'),
            'password': db_config.get('password'),
            'charset': 'utf8mb4',
        }

        return connection_config

    def print_available_databases(self):
        """打印所有可用数据库"""
        databases = self.configs.get('databases', [])

        print("\n" + "=" * 80)
        print("可用数据库列表")
        print("=" * 80)

        for i, db in enumerate(databases):
            print(f"\n[{i}] {db.get('name', 'Unknown')}")
            print(f"    类型: {db.get('type', 'Unknown')}")
            print(f"    主机: {db.get('host', 'Unknown')}")
            print(f"    数据库: {db.get('database', 'Unknown')}")

        print("\n" + "=" * 80)


class EnhancedDatabaseReader:
    """
    增强的数据库读取器
    支持从本地配置文件读取连接信息
    """

    def __init__(self, db_index: int = 1):
        """
        初始化数据库读取器

        Args:
            db_index: 数据库索引，默认1 (腾讯云数据库)
        """
        # 加载配置
        config_manager = DatabaseConfigManager()
        self.db_config = config_manager.get_database_config(db_index)

        # 初始化连接
        self.connection = None
        if self.db_config:
            self._connect()
        else:
            logger.error("无法获取数据库配置")

    def _connect(self):
        """建立数据库连接"""
        try:
            import pymysql
            from pymysql.cursors import DictCursor

            self.connection = pymysql.connect(
                host=self.db_config.get('host'),
                port=self.db_config.get('port', 3306),
                user=self.db_config.get('user'),
                password=self.db_config.get('password'),
                database=self.db_config.get('database'),
                charset=self.db_config.get('charset', 'utf8mb4'),
                cursorclass=DictCursor,
                connect_timeout=10
            )

            logger.info(f"✓ 数据库连接成功: {self.db_config.get('database')}")
            logger.info(f"  主机: {self.db_config.get('host')}")

        except ImportError:
            logger.error("pymysql未安装，请运行: pip install pymysql")
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

    def test_connection(self) -> bool:
        """测试数据库连接"""
        if not self.is_connected():
            logger.error("数据库未连接")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                if result and result.get('test') == 1:
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
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                results = cursor.fetchall()
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
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                results = cursor.fetchall()
                logger.info(f"✓ 表 {table_name} 有 {len(results)} 个字段")
                return results
        except Exception as e:
            logger.error(f"✗ 获取表结构失败: {e}")
            return []

    def read_sql_file(self, sql_path: str) -> str:
        """
        读取SQL文件

        Args:
            sql_path: SQL文件路径

        Returns:
            SQL查询字符串
        """
        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            logger.info(f"✓ 读取SQL文件: {sql_path}")
            return sql
        except Exception as e:
            logger.error(f"✗ 读取SQL文件失败: {e}")
            return ""

    def execute_sql_file(
        self,
        sql_path: str,
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        执行SQL文件中的查询

        Args:
            sql_path: SQL文件路径
            params: 查询参数

        Returns:
            查询结果列表
        """
        sql = self.read_sql_file(sql_path)
        if not sql:
            return []

        return self.execute_query(sql, params)

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")


# 便捷函数
def create_database_reader(db_index: int = 0) -> Optional[EnhancedDatabaseReader]:
    """
    创建数据库读取器

    Args:
        db_index: 数据库索引，默认0 (第一个数据库 - 本地localhost)

    Returns:
        EnhancedDatabaseReader实例，如果连接失败则返回None
    """
    reader = EnhancedDatabaseReader(db_index)
    if reader.is_connected():
        return reader
    return None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 80)
    print("数据库连接测试")
    print("=" * 80)

    # 显示可用数据库
    config_manager = DatabaseConfigManager()
    config_manager.print_available_databases()

    # 连接第一个数据库 (本地localhost)
    print("\n正在连接第一个数据库 (本地localhost)...")
    reader = create_database_reader(db_index=0)

    if reader:
        # 测试连接
        if reader.test_connection():
            print("\n✓ 数据库连接成功!")

            # 获取表列表
            print("\n获取数据库表列表...")
            tables = reader.get_table_list()
            print(f"\n找到 {len(tables)} 张表:")
            for i, table in enumerate(tables[:20], 1):  # 只显示前20个
                print(f"  {i}. {table}")

            if len(tables) > 20:
                print(f"  ... 还有 {len(tables) - 20} 张表")

        reader.close()
    else:
        print("\n✗ 数据库连接失败")
        print("\n请检查:")
        print("  1. 配置文件路径是否正确: C:\\Users\\jm024027\\db_config.json")
        print("  2. pymysql是否已安装: pip install pymysql")
        print("  3. 数据库是否可以访问")

    print("\n" + "=" * 80)

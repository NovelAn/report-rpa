"""
数据库连接管理器
统一的MySQL连接处理，支持JSON配置
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


# 默认配置文件路径：用户根目录下的 database_config.json
DEFAULT_CONFIG_PATH = Path.home() / "database_config.json"


class DatabaseConnection:
    """
    统一的数据库连接管理类
    支持从字典或配置文件创建连接
    """

    def __init__(self, config: Union[str, Path, Dict[str, Any], int] = 0):
        """
        初始化数据库连接

        Args:
            config: 可以是以下类型之一
                - int: 数据库索引，从默认配置文件中读取 (默认0，即第一个数据库)
                - dict: 数据库配置字典
                - str/Path: JSON配置文件路径

        Example:
            # 使用默认配置文件的第一个数据库
            conn = DatabaseConnection()

            # 使用默认配置文件的第二个数据库
            conn = DatabaseConnection(1)

            # 使用配置字典
            conn = DatabaseConnection({'host': 'localhost', 'user': 'root'})

            # 使用自定义配置文件
            conn = DatabaseConnection("/path/to/config.json")
        """
        self.config = self._resolve_config(config)
        self.connection = None

        if self.config:
            self._connect()

    def _resolve_config(self, config: Union[str, Path, Dict[str, Any], int]) -> Optional[Dict[str, Any]]:
        """
        解析配置

        支持以下类型:
        - int: 从默认配置文件读取指定索引的数据库
        - dict: 直接使用配置字典
        - str/Path: 从指定JSON文件读取第一个数据库
        """
        # 如果是整数，从默认配置文件读取
        if isinstance(config, int):
            return self._load_from_default(config)

        # 如果是字典，直接返回
        if isinstance(config, dict):
            return config

        # 如果是路径，从JSON文件读取
        config_path = Path(config)
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return None

        if config_path.suffix == '.json':
            return self._load_json(config_path, db_index=0)
        else:
            logger.error(f"不支持的配置文件格式: {config_path.suffix}")
            return None

    def _load_from_default(self, db_index: int = 0) -> Optional[Dict[str, Any]]:
        """
        从默认配置文件加载数据库配置

        Args:
            db_index: 数据库索引 (默认0)

        Returns:
            数据库配置字典
        """
        return self._load_json(DEFAULT_CONFIG_PATH, db_index)

    def _load_json(self, path: Path, db_index: int = 0) -> Optional[Dict[str, Any]]:
        """
        从JSON文件加载数据库配置

        Args:
            path: JSON配置文件路径
            db_index: 数据库索引

        Returns:
            数据库配置字典

        JSON格式:
        {
            "databases": [
                {
                    "name": "本地数据库",
                    "host": "localhost",
                    "port": 3306,
                    "database": "mbr_db",
                    "user": "root",
                    "password": "${DB_PASSWORD}"
                },
                {
                    "name": "生产数据库",
                    "host": "prod.example.com",
                    "database": "production",
                    "user": "readonly",
                    "password": "${PROD_DB_PASSWORD}"
                }
            ]
        }
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            databases = data.get('databases', [])

            if not databases:
                logger.error(f"配置文件中没有数据库: {path}")
                return None

            if db_index >= len(databases):
                logger.error(f"数据库索引 {db_index} 超出范围 (共 {len(databases)} 个)")
                return None

            db_config = databases[db_index]
            db_name = db_config.get('name', f'数据库#{db_index}')

            logger.info(f"使用配置: {db_name}")

            # 转换为标准连接格式
            return {
                'host': db_config.get('host'),
                'port': db_config.get('port', 3306),
                'database': db_config.get('database'),
                'user': db_config.get('user'),
                'password': db_config.get('password'),
                'charset': 'utf8mb4',
            }

        except FileNotFoundError:
            logger.error(f"配置文件不存在: {path}")
            logger.info(f"请在 {path} 创建配置文件")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}")
            return None
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return None

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
            查询结果列表
        """
        if not self.is_connected():
            logger.error("数据库未连接")
            return []

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                logger.info(f"✓ 查询成功: {len(results)} 条记录")
                return results

        except Exception as e:
            logger.error(f"✗ 查询失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

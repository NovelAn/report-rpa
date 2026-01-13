"""
SQL查询加载器
从queries目录统一管理SQL查询
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class QueryLoader:
    """
    SQL查询加载器
    从queries目录加载.sql文件
    """

    def __init__(self, queries_dir: Optional[Path] = None):
        """
        初始化查询加载器

        Args:
            queries_dir: SQL文件目录，默认使用本模块的queries目录
        """
        if queries_dir is None:
            queries_dir = Path(__file__).parent / "queries"

        self.queries_dir = Path(queries_dir)
        self._cache = {}

        if not self.queries_dir.exists():
            logger.warning(f"SQL查询目录不存在: {self.queries_dir}")

    def load(self, query_name: str) -> str:
        """
        加载SQL查询

        Args:
            query_name: 查询名称 (不含.sql后缀)

        Returns:
            SQL查询字符串

        Example:
            loader = QueryLoader()
            sql = loader.load('target_metrics')
        """
        # 检查缓存
        if query_name in self._cache:
            return self._cache[query_name]

        # 构建文件路径
        sql_file = self.queries_dir / f"{query_name}.sql"

        if not sql_file.exists():
            logger.error(f"SQL文件不存在: {sql_file}")
            return ""

        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            # 缓存查询
            self._cache[query_name] = sql
            logger.debug(f"✓ 加载SQL: {query_name}")
            return sql

        except Exception as e:
            logger.error(f"✗ 读取SQL文件失败 {query_name}: {e}")
            return ""

    def reload(self, query_name: str) -> str:
        """
        重新加载SQL查询（清除缓存）

        Args:
            query_name: 查询名称

        Returns:
            SQL查询字符串
        """
        if query_name in self._cache:
            del self._cache[query_name]
        return self.load(query_name)

    def clear_cache(self):
        """清除所有缓存"""
        self._cache.clear()

    def list_queries(self) -> list:
        """列出所有可用的SQL查询"""
        if not self.queries_dir.exists():
            return []

        return [
            f.stem for f in self.queries_dir.glob("*.sql")
            if f.is_file()
        ]

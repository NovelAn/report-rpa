"""
数据摄入引擎
统一管理多源数据摄入 (Excel, Database, CSV等)
"""

from pathlib import Path
from typing import List, Union, Optional
import logging

from .excel_reader import ExcelDataReader
from ..models.data_schema import UnifiedReportData

logger = logging.getLogger(__name__)


class DataIngestionEngine:
    """
    数据摄入引擎
    支持多种数据源的统一摄入
    """

    def __init__(self):
        self.data_sources = []

    def add_excel_source(self, file_path: Union[str, Path]) -> 'DataIngestionEngine':
        """
        添加Excel数据源

        Args:
            file_path: Excel文件路径

        Returns:
            self (支持链式调用)
        """
        self.data_sources.append({
            'type': 'excel',
            'path': Path(file_path)
        })
        return self

    def add_csv_source(self, file_path: Union[str, Path]) -> 'DataIngestionEngine':
        """添加CSV数据源 (暂未实现)"""
        self.data_sources.append({
            'type': 'csv',
            'path': Path(file_path)
        })
        return self

    def add_database_source(self, connection_string: str) -> 'DataIngestionEngine':
        """添加数据库源 (暂未实现)"""
        self.data_sources.append({
            'type': 'database',
            'connection': connection_string
        })
        return self

    def ingest(self) -> List[UnifiedReportData]:
        """
        执行数据摄入

        Returns:
            UnifiedReportData对象列表

        Raises:
            ValueError: 如果没有配置数据源或数据源类型不支持
        """
        if not self.data_sources:
            raise ValueError("No data sources configured")

        results = []

        for source in self.data_sources:
            if source['type'] == 'excel':
                reader = ExcelDataReader(source['path'])
                data = reader.parse_all()
                results.append(data)
            elif source['type'] == 'csv':
                logger.warning("CSV source not yet implemented")
            elif source['type'] == 'database':
                logger.warning("Database source not yet implemented")
            else:
                raise ValueError(f"Unsupported data source type: {source['type']}")

        logger.info(f"Ingested data from {len(results)} sources")
        return results

    def ingest_first(self) -> Optional[UnifiedReportData]:
        """
        仅摄入第一个数据源

        Returns:
            UnifiedReportData对象或None
        """
        results = self.ingest()
        return results[0] if results else None

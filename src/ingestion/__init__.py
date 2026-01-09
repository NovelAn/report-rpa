"""
数据摄入模块
负责从各种数据源读取数据 (Excel, Database, CSV, JSON等)
"""

from .excel_reader import ExcelDataReader
from .data_ingestion import DataIngestionEngine

__all__ = [
    'ExcelDataReader',
    'DataIngestionEngine'
]

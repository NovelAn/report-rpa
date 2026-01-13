"""
数据摄入模块
负责从各种数据源读取数据 (Excel, Database, CSV, JSON等)
"""

from .excel_reader import ExcelDataReader
from .data_ingestion import DataIngestionEngine
from .get_monthly_targets import (
    get_monthly_targets,
    get_monthly_targets_dict,
    get_ytd_targets,
    get_ytd_targets_dict
)

__all__ = [
    'ExcelDataReader',
    'DataIngestionEngine',
    'get_monthly_targets',
    'get_monthly_targets_dict',
    'get_ytd_targets',
    'get_ytd_targets_dict'
]

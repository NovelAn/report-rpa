"""
MBR数据模型模块
定义所有数据结构和类型
"""

from .data_schema import (
    ChannelType,
    MetricType,
    TargetMetric,
    TrafficMetrics,
    CampaignEvent,
    MonthlyMetrics,
    UnifiedReportData,
    SalesOverview,
    CompetitorTraffic,
    MemberData
)

__all__ = [
    'ChannelType',
    'MetricType',
    'TargetMetric',
    'TrafficMetrics',
    'CampaignEvent',
    'MonthlyMetrics',
    'UnifiedReportData',
    'SalesOverview',
    'CompetitorTraffic',
    'MemberData'
]

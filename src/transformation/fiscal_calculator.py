"""
财年聚合计算器
支持按财年维度进行数据聚合和计算
"""

import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import date
import logging

from ..models.data_schema import (
    TargetMetric,
    MonthlyMetrics,
    ChannelType,
    FiscalYear
)

logger = logging.getLogger(__name__)


class FiscalYearAggregator:
    """
    财年聚合器
    提供按财年维度聚合数据的功能
    """

    def __init__(self, daily_metrics: List[TargetMetric]):
        """
        初始化财年聚合器

        Args:
            daily_metrics: 日度指标列表
        """
        self.daily_metrics = daily_metrics
        self.df = pd.DataFrame([m.dict() for m in daily_metrics])

        if not self.df.empty:
            # 转换日期列
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['year'] = self.df['date'].dt.year
                self.df['month'] = self.df['date'].dt.month

                # 添加财年相关字段
                self.df['fiscal_year'] = self.df['date'].apply(
                    lambda x: FiscalYear.get_fiscal_year(x.date())
                )
                # fiscal_month 就是 calendar month (使用自然月)
                self.df['fiscal_month'] = self.df['month']

    def aggregate_fiscal_year_monthly(
        self,
        fiscal_year: int,
        fiscal_month: int,
        channel: ChannelType
    ) -> Optional[MonthlyMetrics]:
        """
        聚合指定财年月的日度数据

        Args:
            fiscal_year: 财年 (如2025表示FY25)
            fiscal_month: 财月 (1-12, 使用自然月)
            channel: 渠道

        Returns:
            MonthlyMetrics对象, 如果没有数据则返回None
        """
        if self.df.empty:
            return None

        # 根据财年和财月计算日历年
        # 规则: 4月及以后属于(fiscal_year - 1), 1-3月属于fiscal_year
        if fiscal_month >= 4:
            cal_year = fiscal_year - 1
        else:
            cal_year = fiscal_year
        cal_month = fiscal_month

        # 过滤数据
        channel_str = channel.value if isinstance(channel, ChannelType) else channel
        monthly_df = self.df[
            (self.df['year'] == cal_year) &
            (self.df['month'] == cal_month) &
            (self.df['channel'] == channel_str)
        ]

        if monthly_df.empty:
            logger.debug(
                f"No data found for FY{fiscal_year % 100}-Month {fiscal_month:02d} {channel}"
            )
            return None

        # 计算聚合指标
        gmv = monthly_df['gmv'].fillna(0).sum()
        net = monthly_df['net'].fillna(0).sum()
        uv = int(monthly_df['uv'].fillna(0).sum())
        buyers = int(monthly_df['buyers'].fillna(0).sum())

        # 处理non_paid_traffic字段
        non_paid_traffic = 0
        if 'non_paid_traffic' in monthly_df.columns:
            non_paid_traffic = int(monthly_df['non_paid_traffic'].fillna(0).sum())
        elif 'free_traffic' in monthly_df.columns:
            non_paid_traffic = int(monthly_df['free_traffic'].fillna(0).sum())

        paid_traffic = int(monthly_df['paid_traffic'].fillna(0).sum())
        free_traffic = int(monthly_df['free_traffic'].fillna(0).sum())

        # 计算派生指标
        aov = net / buyers if buyers > 0 else 0.0
        cr = (buyers / uv * 100) if uv > 0 else 0.0

        return MonthlyMetrics(
            year=cal_year,
            month=cal_month,
            channel=channel,
            gmv=gmv,
            net=net,
            uv=uv,
            buyers=buyers,
            aov=aov,
            cr=cr,
            paid_traffic=paid_traffic,
            free_traffic=free_traffic,
            non_paid_traffic=non_paid_traffic
        )

    def calculate_fiscal_ytd(
        self,
        fiscal_year: int,
        channel: ChannelType,
        through_fiscal_month: Optional[int] = None
    ) -> Optional[MonthlyMetrics]:
        """
        计算财年年初至今 (Fiscal Year-to-Date) 数据

        Args:
            fiscal_year: 财年
            channel: 渠道
            through_fiscal_month: 截止财月 (1-12), 如果为None则使用当前数据中的最大财月

        Returns:
            MonthlyMetrics对象, 如果没有数据则返回None
        """
        if self.df.empty:
            return None

        # 确定截止财月
        if through_fiscal_month is None:
            channel_df = self.df[
                (self.df['fiscal_year'] == fiscal_year) &
                (self.df['channel'] == channel.value)
            ]
            if channel_df.empty:
                return None
            through_fiscal_month = channel_df['fiscal_month'].max()

        # 收集财年内所有月份的数据
        monthly_metrics = []
        for fm in range(1, through_fiscal_month + 1):
            metric = self.aggregate_fiscal_year_monthly(
                fiscal_year, fm, channel
            )
            if metric:
                monthly_metrics.append(metric)

        if not monthly_metrics:
            return None

        # 聚合FYTD指标
        gmv = sum(m.gmv for m in monthly_metrics)
        net = sum(m.net for m in monthly_metrics)
        uv = sum(m.uv for m in monthly_metrics)
        buyers = sum(m.buyers for m in monthly_metrics)
        paid_traffic = sum(m.paid_traffic for m in monthly_metrics)
        non_paid_traffic = sum(m.non_paid_traffic for m in monthly_metrics)
        free_traffic = sum(m.free_traffic for m in monthly_metrics)

        aov = net / buyers if buyers > 0 else 0.0
        cr = (buyers / uv * 100) if uv > 0 else 0.0

        # 使用最后一个日历月作为标记
        last_metric = monthly_metrics[-1]

        return MonthlyMetrics(
            year=last_metric.year,
            month=last_metric.month,
            channel=channel,
            gmv=gmv,
            net=net,
            uv=uv,
            buyers=buyers,
            aov=aov,
            cr=cr,
            paid_traffic=paid_traffic,
            free_traffic=free_traffic,
            non_paid_traffic=non_paid_traffic
        )

    def calculate_all_fiscal_months(
        self,
        fiscal_year: Optional[int] = None,
        channels: Optional[List[ChannelType]] = None
    ) -> List[MonthlyMetrics]:
        """
        计算财年内所有月份的聚合数据

        Args:
            fiscal_year: 财年, 如果为None则使用数据中的所有财年
            channels: 要计算的渠道列表

        Returns:
            MonthlyMetrics列表 (按财月排序)
        """
        if self.df.empty:
            return []

        # 确定财年范围
        if fiscal_year is None:
            fiscal_years = self.df['fiscal_year'].unique()
        else:
            fiscal_years = [fiscal_year]

        # 确定渠道
        if channels is None:
            unique_channels = self.df['channel'].unique()
            channels = [
                ChannelType(ch) for ch in unique_channels
                if ch in ChannelType.__members__
            ]

        monthly_metrics = []

        for fy in fiscal_years:
            for fm in range(1, 13):  # 财月1-12
                for channel in channels:
                    metric = self.aggregate_fiscal_year_monthly(fy, fm, channel)
                    if metric:
                        monthly_metrics.append(metric)

        logger.info(
            f"Calculated {len(monthly_metrics)} fiscal monthly metrics "
            f"for {len(fiscal_years)} fiscal years"
        )
        return monthly_metrics

    def calculate_fiscal_yoy(
        self,
        current_metric: MonthlyMetrics,
        all_metrics: List[MonthlyMetrics]
    ) -> Optional[float]:
        """
        计算财年同比增长率

        Args:
            current_metric: 当前月份指标
            all_metrics: 所有月份指标列表

        Returns:
            同比增长率 (%)
        """
        # 找到去年同期
        last_fiscal_year = current_metric.fiscal_year - 1
        last_fiscal_month = current_metric.fiscal_month

        for metric in all_metrics:
            if (metric.fiscal_year == last_fiscal_year and
                metric.fiscal_month == last_fiscal_month and
                metric.channel == current_metric.channel):
                if metric.net > 0:
                    return ((current_metric.net - metric.net) / metric.net * 100)
                return None

        return None

    def calculate_fiscal_mom(
        self,
        current_metric: MonthlyMetrics,
        all_metrics: List[MonthlyMetrics]
    ) -> Optional[float]:
        """
        计算财年环比增长率

        Args:
            current_metric: 当前月份指标
            all_metrics: 所有月份指标列表

        Returns:
            环比增长率 (%)
        """
        # 找到上一个财月
        if current_metric.fiscal_month == 1:
            # 财年第1个月,上一财月是去年第12个月
            last_fiscal_year = current_metric.fiscal_year - 1
            last_fiscal_month = 12
        else:
            last_fiscal_year = current_metric.fiscal_year
            last_fiscal_month = current_metric.fiscal_month - 1

        for metric in all_metrics:
            if (metric.fiscal_year == last_fiscal_year and
                metric.fiscal_month == last_fiscal_month and
                metric.channel == current_metric.channel):
                if metric.net > 0:
                    return ((current_metric.net - metric.net) / metric.net * 100)
                return None

        return None

    def calculate_fiscal_yoy_for_all(
        self,
        monthly_metrics: List[MonthlyMetrics]
    ) -> List[MonthlyMetrics]:
        """
        为所有月度数据计算财年YoY增长率

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            更新后的月度指标列表
        """
        for metric in monthly_metrics:
            yoy = self.calculate_fiscal_yoy(metric, monthly_metrics)
            if yoy is not None:
                # 覆盖日历YoY为财年YoY
                metric.yoy_growth = yoy

        return monthly_metrics

    def calculate_fiscal_mom_for_all(
        self,
        monthly_metrics: List[MonthlyMetrics]
    ) -> List[MonthlyMetrics]:
        """
        为所有月度数据计算财年MoM增长率

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            更新后的月度指标列表
        """
        for metric in monthly_metrics:
            mom = self.calculate_fiscal_mom(metric, monthly_metrics)
            if mom is not None:
                # 覆盖日历MoM为财年MoM
                metric.mom_growth = mom

        return monthly_metrics

"""
业务逻辑计算器
实现Excel中的公式逻辑,包括YoY、MoM、聚合等计算
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import date
import logging

from ..models.data_schema import (
    TargetMetric,
    MonthlyMetrics,
    ChannelType
)

logger = logging.getLogger(__name__)


class MetricCalculator:
    """
    指标计算器
    提供各种业务指标的计算方法
    """

    @staticmethod
    def calculate_yoy(
        current_value: Optional[float],
        last_year_value: Optional[float]
    ) -> Optional[float]:
        """
        计算同比增长率 (Year-over-Year)

        Args:
            current_value: 当期值
            last_year_value: 去年同期值

        Returns:
            同比增长率 (%), 如果输入无效则返回None
        """
        if current_value is None or last_year_value is None:
            return None

        if last_year_value == 0:
            # 去年同期为0的情况
            if current_value == 0:
                return 0.0
            return None  # 无限增长,返回None

        growth_rate = ((current_value - last_year_value) / last_year_value) * 100
        return round(growth_rate, 2)

    @staticmethod
    def calculate_mom(
        current_value: Optional[float],
        last_month_value: Optional[float]
    ) -> Optional[float]:
        """
        计算环比增长率 (Month-over-Month)

        Args:
            current_value: 当月值
            last_month_value: 上月值

        Returns:
            环比增长率 (%), 如果输入无效则返回None
        """
        if current_value is None or last_month_value is None:
            return None

        if last_month_value == 0:
            if current_value == 0:
                return 0.0
            return None

        growth_rate = ((current_value - last_month_value) / last_month_value) * 100
        return round(growth_rate, 2)

    @staticmethod
    def calculate_cr(buyers: Optional[int], uv: Optional[int]) -> Optional[float]:
        """
        计算转化率 (Conversion Rate)

        Args:
            buyers: 购买人数
            uv: 访客数

        Returns:
            转化率 (%), 如果输入无效则返回None
        """
        if buyers is None or uv is None or uv == 0:
            return None

        cr = (buyers / uv) * 100
        return round(cr, 2)

    @staticmethod
    def calculate_aov(gmv: Optional[float], orders: Optional[int]) -> Optional[float]:
        """
        计算平均订单价值 (Average Order Value)

        Args:
            gmv: GMV
            orders: 订单数

        Returns:
            AOV, 如果输入无效则返回None
        """
        if gmv is None or orders is None or orders == 0:
            return None

        aov = gmv / orders
        return round(aov, 2)

    @staticmethod
    def calculate_atv(gmv: Optional[float], buyers: Optional[int]) -> Optional[float]:
        """
        计算平均交易价值 (Average Transaction Value)

        Args:
            gmv: GMV
            buyers: 购买人数

        Returns:
            ATV, 如果输入无效则返回None
        """
        if gmv is None or buyers is None or buyers == 0:
            return None

        atv = gmv / buyers
        return round(atv, 2)

    @staticmethod
    def calculate_aur(gmv: Optional[float], gmv_units: Optional[int]) -> Optional[float]:
        """
        计算件单价 (Average Unit Price)

        Args:
            gmv: GMV
            gmv_units: GMV件数

        Returns:
            AUR, 如果输入无效则返回None
        """
        if gmv is None or gmv_units is None or gmv_units == 0:
            return None

        aur = gmv / gmv_units
        return round(aur, 2)

    @staticmethod
    def calculate_rrc(
        return_amount: Optional[float],
        cancel_amount: Optional[float],
        gmv: Optional[float]
    ) -> Optional[float]:
        """
        计算总退款率 (Refund Rate = 取消退款 + 退货退款)

        Args:
            return_amount: 退货退款金额
            cancel_amount: 取消退款金额
            gmv: GMV

        Returns:
            总退款率 (%), 如果输入无效则返回None
        """
        if return_amount is None or cancel_amount is None or gmv is None or gmv == 0:
            return None

        total_refund = return_amount + cancel_amount
        rrc = (total_refund / gmv) * 100
        return round(rrc, 2)

    @staticmethod
    def calculate_cancel_rate(
        cancel_amount: Optional[float],
        gmv: Optional[float]
    ) -> Optional[float]:
        """
        计算取消率 (Cancel Rate)

        Args:
            cancel_amount: 取消退款金额
            gmv: GMV

        Returns:
            取消率 (%), 如果输入无效则返回None
        """
        if cancel_amount is None or gmv is None or gmv == 0:
            return None

        cancel_rate = (cancel_amount / gmv) * 100
        return round(cancel_rate, 2)

    @staticmethod
    def calculate_return_rate(
        return_amount: Optional[float],
        gmv: Optional[float]
    ) -> Optional[float]:
        """
        计算退货退款率 (Return Rate)

        Args:
            return_amount: 退货退款金额
            gmv: GMV

        Returns:
            退货率 (%), 如果输入无效则返回None
        """
        if return_amount is None or gmv is None or gmv == 0:
            return None

        return_rate = (return_amount / gmv) * 100
        return round(return_rate, 2)

    @staticmethod
    def calculate_rrc_after_cancel(
        return_amount: Optional[float],
        gmv: Optional[float],
        cancel_amount: Optional[float]
    ) -> Optional[float]:
        """
        计算取消后退款率 (RRC After Cancel)

        Args:
            return_amount: 退货退款金额
            gmv: GMV
            cancel_amount: 取消金额

        Returns:
            取消后退款率 (%), 如果输入无效则返回None
        """
        if return_amount is None or gmv is None or cancel_amount is None:
            return None

        gmv_after_cancel = gmv - cancel_amount
        if gmv_after_cancel == 0:
            return None

        rrc_after_cancel = (return_amount / gmv_after_cancel) * 100
        return round(rrc_after_cancel, 2)


class DataAggregator:
    """
    数据聚合器
    将日度数据聚合为月度数据
    """

    def __init__(self, daily_metrics: List[TargetMetric]):
        """
        初始化聚合器

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

    def aggregate_monthly(
        self,
        year: int,
        month: int,
        channel: ChannelType
    ) -> Optional[MonthlyMetrics]:
        """
        聚合指定月份和渠道的数据

        Args:
            year: 年份
            month: 月份 (1-12)
            channel: 渠道

        Returns:
            MonthlyMetrics对象, 如果没有数据则返回None
        """
        if self.df.empty:
            return None

        # 过滤数据
        channel_str = channel.value if isinstance(channel, ChannelType) else channel
        monthly_df = self.df[
            (self.df['year'] == year) &
            (self.df['month'] == month) &
            (self.df['channel'] == channel_str)
        ]

        if monthly_df.empty:
            logger.warning(f"No data found for {year}-{month:02d} {channel}")
            return None

        # 计算聚合指标
        gmv = monthly_df['gmv'].fillna(0).sum()
        net = monthly_df['net'].fillna(0).sum()
        uv = int(monthly_df['uv'].fillna(0).sum())
        buyers = int(monthly_df['buyers'].fillna(0).sum())
        paid_traffic = int(monthly_df['paid_traffic'].fillna(0).sum())
        free_traffic = int(monthly_df['free_traffic'].fillna(0).sum())

        # 计算派生指标
        orders = int(monthly_df['orders'].fillna(0).sum()) if 'orders' in monthly_df.columns else None
        gmv_units = int(monthly_df['gmv_units'].fillna(0).sum()) if 'gmv_units' in monthly_df.columns else None
        aov = MetricCalculator.calculate_aov(gmv, orders) or 0.0 if orders else 0.0
        atv = MetricCalculator.calculate_atv(gmv, buyers)
        aur = MetricCalculator.calculate_aur(gmv, gmv_units)
        cr = MetricCalculator.calculate_cr(buyers, uv) or 0.0

        # 计算退款相关字段
        cancel_amount = monthly_df['cancel_amount'].fillna(0).sum() if 'cancel_amount' in monthly_df.columns else None
        return_amount = monthly_df['return_amount'].fillna(0).sum() if 'return_amount' in monthly_df.columns else None

        # 计算退款率
        rrc = None
        cancel_rate = None
        return_rate_val = None
        rrc_after_cancel_val = None

        if cancel_amount is not None and return_amount is not None and gmv > 0:
            rrc = MetricCalculator.calculate_rrc(return_amount, cancel_amount, gmv)
            cancel_rate = MetricCalculator.calculate_cancel_rate(cancel_amount, gmv)
            return_rate_val = MetricCalculator.calculate_return_rate(return_amount, gmv)
            rrc_after_cancel_val = MetricCalculator.calculate_rrc_after_cancel(return_amount, gmv, cancel_amount)

        return MonthlyMetrics(
            year=year,
            month=month,
            channel=channel,
            gmv=gmv,
            net=net,
            uv=uv,
            buyers=buyers,
            orders=orders,
            gmv_units=gmv_units,
            aov=aov,
            atv=atv,
            aur=aur,
            cr=cr,
            paid_traffic=paid_traffic,
            free_traffic=free_traffic,
            cancel_amount=cancel_amount,
            return_amount=return_amount,
            total_refund_amount=(cancel_amount or 0) + (return_amount or 0) if cancel_amount is not None and return_amount is not None else None,
            cancel_rate=cancel_rate,
            return_rate=return_rate_val,
            rrc=rrc,
            rrc_after_cancel=rrc_after_cancel_val
        )

    def calculate_ytd(
        self,
        year: int,
        channel: ChannelType,
        through_month: Optional[int] = None
    ) -> Optional[MonthlyMetrics]:
        """
        计算年初至今 (Year-to-Date) 数据

        Args:
            year: 年份
            channel: 渠道
            through_month: 截止月份 (如果为None则使用当前数据中的最大月份)

        Returns:
            MonthlyMetrics对象, 如果没有数据则返回None
        """
        if self.df.empty:
            return None

        # 确定截止月份
        if through_month is None:
            channel_df = self.df[
                (self.df['year'] == year) &
                (self.df['channel'] == channel.value)
            ]
            if channel_df.empty:
                return None
            through_month = channel_df['month'].max()

        # 过滤YTD数据
        channel_str = channel.value if isinstance(channel, ChannelType) else channel
        ytd_df = self.df[
            (self.df['year'] == year) &
            (self.df['month'] <= through_month) &
            (self.df['channel'] == channel_str)
        ]

        if ytd_df.empty:
            return None

        # 聚合YTD指标
        gmv = ytd_df['gmv'].fillna(0).sum()
        net = ytd_df['net'].fillna(0).sum()
        uv = int(ytd_df['uv'].fillna(0).sum())
        buyers = int(ytd_df['buyers'].fillna(0).sum())
        orders = int(ytd_df['orders'].fillna(0).sum()) if 'orders' in ytd_df.columns else None
        gmv_units = int(ytd_df['gmv_units'].fillna(0).sum()) if 'gmv_units' in ytd_df.columns else None
        paid_traffic = int(ytd_df['paid_traffic'].fillna(0).sum())
        free_traffic = int(ytd_df['free_traffic'].fillna(0).sum())

        # 计算退款相关字段
        cancel_amount = ytd_df['cancel_amount'].fillna(0).sum() if 'cancel_amount' in ytd_df.columns else None
        return_amount = ytd_df['return_amount'].fillna(0).sum() if 'return_amount' in ytd_df.columns else None

        aov = MetricCalculator.calculate_aov(gmv, orders) or 0.0 if orders else 0.0
        atv = MetricCalculator.calculate_atv(gmv, buyers)
        aur = MetricCalculator.calculate_aur(gmv, gmv_units)
        cr = MetricCalculator.calculate_cr(buyers, uv) or 0.0

        # 计算退款率
        rrc = None
        cancel_rate = None
        return_rate_val = None
        rrc_after_cancel_val = None

        if cancel_amount is not None and return_amount is not None and gmv > 0:
            rrc = MetricCalculator.calculate_rrc(return_amount, cancel_amount, gmv)
            cancel_rate = MetricCalculator.calculate_cancel_rate(cancel_amount, gmv)
            return_rate_val = MetricCalculator.calculate_return_rate(return_amount, gmv)
            rrc_after_cancel_val = MetricCalculator.calculate_rrc_after_cancel(return_amount, gmv, cancel_amount)

        return MonthlyMetrics(
            year=year,
            month=through_month,
            channel=channel,
            gmv=gmv,
            net=net,
            uv=uv,
            buyers=buyers,
            orders=orders,
            gmv_units=gmv_units,
            aov=aov,
            atv=atv,
            aur=aur,
            cr=cr,
            paid_traffic=paid_traffic,
            free_traffic=free_traffic,
            cancel_amount=cancel_amount,
            return_amount=return_amount,
            total_refund_amount=(cancel_amount or 0) + (return_amount or 0) if cancel_amount is not None and return_amount is not None else None,
            cancel_rate=cancel_rate,
            return_rate=return_rate_val,
            rrc=rrc,
            rrc_after_cancel=rrc_after_cancel_val
        )

    def calculate_all_monthly(
        self,
        channels: Optional[List[ChannelType]] = None
    ) -> List[MonthlyMetrics]:
        """
        计算所有月份的聚合数据

        Args:
            channels: 要计算的渠道列表,如果为None则计算所有渠道

        Returns:
            MonthlyMetrics列表
        """
        if self.df.empty:
            return []

        # 确定要计算的渠道
        if channels is None:
            # 从数据中提取所有唯一渠道
            unique_channels = self.df['channel'].unique()
            channels = [ChannelType(ch) for ch in unique_channels if ch in ChannelType.__members__]

        # 获取所有年月组合
        year_months = self.df[['year', 'month']].drop_duplicates().sort_values(['year', 'month'])

        monthly_metrics = []

        for _, row in year_months.iterrows():
            year = int(row['year'])
            month = int(row['month'])

            for channel in channels:
                metric = self.aggregate_monthly(year, month, channel)
                if metric:
                    monthly_metrics.append(metric)

        logger.info(f"Calculated {len(monthly_metrics)} monthly metrics")
        return monthly_metrics

    def calculate_yoy_for_all(
        self,
        monthly_metrics: List[MonthlyMetrics]
    ) -> List[MonthlyMetrics]:
        """
        为所有月度数据计算YoY增长率

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            更新后的月度指标列表 (包含yoy_growth字段)
        """
        # 按渠道和月份组织数据
        data_by_channel: Dict[ChannelType, Dict[str, MonthlyMetrics]] = {}

        for metric in monthly_metrics:
            channel = metric.channel
            period = metric.period

            if channel not in data_by_channel:
                data_by_channel[channel] = {}

            data_by_channel[channel][period] = metric

        # 计算YoY
        for channel, periods_data in data_by_channel.items():
            for period, current_metric in periods_data.items():
                # 计算去年同期
                last_year_period = f"{current_metric.year - 1}-{current_metric.month:02d}"

                if last_year_period in periods_data:
                    last_year_metric = periods_data[last_year_period]

                    # 计算YoY
                    current_metric.yoy_growth = MetricCalculator.calculate_yoy(
                        current_metric.net,
                        last_year_metric.net
                    )

                    # 保存去年数据
                    current_metric.ly_net = last_year_metric.net
                    current_metric.ly_gmv = last_year_metric.gmv
                    current_metric.ly_uv = last_year_metric.uv

        return monthly_metrics

    def calculate_mom_for_all(
        self,
        monthly_metrics: List[MonthlyMetrics]
    ) -> List[MonthlyMetrics]:
        """
        为所有月度数据计算MoM增长率

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            更新后的月度指标列表 (包含mom_growth字段)
        """
        # 按渠道和月份组织数据
        data_by_channel: Dict[ChannelType, List[MonthlyMetrics]] = {}

        for metric in monthly_metrics:
            channel = metric.channel
            if channel not in data_by_channel:
                data_by_channel[channel] = []
            data_by_channel[channel].append(metric)

        # 计算MoM (每个渠道内按时间排序)
        for channel, metrics in data_by_channel.items():
            # 按时间排序
            metrics.sort(key=lambda m: (m.year, m.month))

            for i in range(1, len(metrics)):
                current = metrics[i]
                previous = metrics[i - 1]

                # 计算MoM
                current.mom_growth = MetricCalculator.calculate_mom(
                    current.net,
                    previous.net
                )

        return monthly_metrics

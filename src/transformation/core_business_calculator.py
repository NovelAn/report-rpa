"""
核心业务计算器
实现DTC渠道剔除逻辑和Core Business核心业务指标计算

业务场景:
1. FF (员工福利) 剔除: 员工内部促销,折扣率高,销售滞销商品,需剔除以便分析正常业务
2. SC (社群推广) 剔除: 买量承诺ROI渠道,与常规广告投放不同,需剔除以便分析核心业务
3. Core Business = PFS + DTC_EXCL_FF_SC: 核心业务指标,用于评估主要业务表现
"""

import logging
from typing import List, Optional, Dict, Set
from datetime import date
import pandas as pd

from ..models.data_schema import (
    TargetMetric,
    MonthlyMetrics,
    ChannelType
)

logger = logging.getLogger(__name__)


class CoreBusinessCalculator:
    """
    核心业务计算器
    实现渠道剔除和派生渠道计算
    """

    def __init__(
        self,
        exclude_ff: bool = False,
        exclude_social: bool = False,
        calculate_derived: bool = True
    ):
        """
        初始化计算器

        Args:
            exclude_ff: 是否剔除FF (员工福利)
            exclude_social: 是否剔除SC (社群推广)
            calculate_derived: 是否计算派生渠道 (DTC_EXCL_FF, DTC_EXCL_FF_SC, CORE_BUSINESS)
        """
        self.exclude_ff = exclude_ff
        self.exclude_social = exclude_social
        self.calculate_derived = calculate_derived

    @staticmethod
    def calculate_dtc_excl_ff(dtc_metric: MonthlyMetrics) -> Optional[MonthlyMetrics]:
        """
        计算DTC剔除FF后的指标

        DTC_EXCL_FF = DTC - FF

        注意: 该方法用于从已聚合的DTC月度数据中剔除FF部分
        FF数据需要从原始TargetMetric中提取

        Args:
            dtc_metric: DTC渠道月度数据

        Returns:
            DTC_EXCL_FF月度数据,如果没有DTC数据则返回None
        """
        if not dtc_metric:
            return None

        # 从DTC数据复制基本字段
        # 注意: 这里假设FF数据已经从原始数据中减去
        # 实际使用时应该使用 aggregate_monthly_with_exclusion 方法
        excl_metric = MonthlyMetrics(
            year=dtc_metric.year,
            month=dtc_metric.month,
            channel=ChannelType.DTC_EXCL_FF,
            gmv=dtc_metric.gmv,
            net=dtc_metric.net,
            uv=dtc_metric.uv,
            buyers=dtc_metric.buyers,
            orders=dtc_metric.orders,
            gmv_units=dtc_metric.gmv_units,
            aov=dtc_metric.aov,
            atv=dtc_metric.atv,
            aur=dtc_metric.aur,
            cr=dtc_metric.cr,
            paid_traffic=dtc_metric.paid_traffic,
            free_traffic=dtc_metric.free_traffic,
            non_paid_traffic=dtc_metric.non_paid_traffic,
            cancel_amount=dtc_metric.cancel_amount,
            return_amount=dtc_metric.return_amount,
            total_refund_amount=dtc_metric.total_refund_amount,
            cancel_rate=dtc_metric.cancel_rate,
            return_rate=dtc_metric.return_rate,
            rrc=dtc_metric.rrc,
            rrc_after_cancel=dtc_metric.rrc_after_cancel
        )

        return excl_metric

    @staticmethod
    def calculate_dtc_excl_ff_sc(dtc_metric: MonthlyMetrics) -> Optional[MonthlyMetrics]:
        """
        计算DTC剔除FF和SC后的指标

        DTC_EXCL_FF_SC = DTC - FF - SC

        注意: 该方法用于从已聚合的DTC月度数据中剔除FF和SC部分
        FF和SC数据需要从原始TargetMetric中提取

        Args:
            dtc_metric: DTC渠道月度数据

        Returns:
            DTC_EXCL_FF_SC月度数据,如果没有DTC数据则返回None
        """
        if not dtc_metric:
            return None

        # 从DTC数据复制基本字段
        # 注意: 这里假设FF和SC数据已经从原始数据中减去
        # 实际使用时应该使用 aggregate_monthly_with_exclusion 方法
        excl_metric = MonthlyMetrics(
            year=dtc_metric.year,
            month=dtc_metric.month,
            channel=ChannelType.DTC_EXCL_FF_SC,
            gmv=dtc_metric.gmv,
            net=dtc_metric.net,
            uv=dtc_metric.uv,
            buyers=dtc_metric.buyers,
            orders=dtc_metric.orders,
            gmv_units=dtc_metric.gmv_units,
            aov=dtc_metric.aov,
            atv=dtc_metric.atv,
            aur=dtc_metric.aur,
            cr=dtc_metric.cr,
            paid_traffic=dtc_metric.paid_traffic,
            free_traffic=dtc_metric.free_traffic,
            non_paid_traffic=dtc_metric.non_paid_traffic,
            cancel_amount=dtc_metric.cancel_amount,
            return_amount=dtc_metric.return_amount,
            total_refund_amount=dtc_metric.total_refund_amount,
            cancel_rate=dtc_metric.cancel_rate,
            return_rate=dtc_metric.return_rate,
            rrc=dtc_metric.rrc,
            rrc_after_cancel=dtc_metric.rrc_after_cancel
        )

        return excl_metric

    @staticmethod
    def calculate_core_business(
        pfs_metric: Optional[MonthlyMetrics],
        dtc_excl_ff_sc_metric: Optional[MonthlyMetrics]
    ) -> Optional[MonthlyMetrics]:
        """
        计算核心业务指标

        CORE_BUSINESS = PFS + DTC_EXCL_FF_SC

        Args:
            pfs_metric: PFS渠道月度数据
            dtc_excl_ff_sc_metric: DTC剔除FF和SC后的月度数据

        Returns:
            CORE_BUSINESS月度数据,如果输入不完整则返回None
        """
        if not pfs_metric or not dtc_excl_ff_sc_metric:
            logger.warning("Cannot calculate CORE_BUSINESS: missing PFS or DTC_EXCL_FF_SC data")
            return None

        # 确保期间一致
        if (pfs_metric.year != dtc_excl_ff_sc_metric.year or
            pfs_metric.month != dtc_excl_ff_sc_metric.month):
            logger.warning(
                f"Period mismatch: PFS ({pfs_metric.year}-{pfs_metric.month}) != "
                f"DTC_EXCL_FF_SC ({dtc_excl_ff_sc_metric.year}-{dtc_excl_ff_sc_metric.month})"
            )
            return None

        # 合并数据
        gmv = pfs_metric.gmv + dtc_excl_ff_sc_metric.gmv
        net = pfs_metric.net + dtc_excl_ff_sc_metric.net
        uv = pfs_metric.uv + dtc_excl_ff_sc_metric.uv
        buyers = pfs_metric.buyers + dtc_excl_ff_sc_metric.buyers
        paid_traffic = pfs_metric.paid_traffic + dtc_excl_ff_sc_metric.paid_traffic
        free_traffic = pfs_metric.free_traffic + dtc_excl_ff_sc_metric.free_traffic
        non_paid_traffic = pfs_metric.non_paid_traffic + dtc_excl_ff_sc_metric.non_paid_traffic

        # 合并订单数
        orders = None
        if pfs_metric.orders is not None and dtc_excl_ff_sc_metric.orders is not None:
            orders = pfs_metric.orders + dtc_excl_ff_sc_metric.orders

        # 合并GMV件数
        gmv_units = None
        if pfs_metric.gmv_units is not None and dtc_excl_ff_sc_metric.gmv_units is not None:
            gmv_units = pfs_metric.gmv_units + dtc_excl_ff_sc_metric.gmv_units

        # 合并退款相关字段
        cancel_amount = None
        return_amount = None
        if (pfs_metric.cancel_amount is not None and
            dtc_excl_ff_sc_metric.cancel_amount is not None):
            cancel_amount = pfs_metric.cancel_amount + dtc_excl_ff_sc_metric.cancel_amount

        if (pfs_metric.return_amount is not None and
            dtc_excl_ff_sc_metric.return_amount is not None):
            return_amount = pfs_metric.return_amount + dtc_excl_ff_sc_metric.return_amount

        # 创建CORE_BUSINESS数据
        core_business = MonthlyMetrics(
            year=pfs_metric.year,
            month=pfs_metric.month,
            channel=ChannelType.CORE_BUSINESS,
            gmv=gmv,
            net=net,
            uv=uv,
            buyers=buyers,
            orders=orders,
            gmv_units=gmv_units,
            aov=0.0,  # 需要重新计算
            atv=None,  # 需要重新计算
            aur=None,  # 需要重新计算
            cr=0.0,  # 需要重新计算
            paid_traffic=paid_traffic,
            free_traffic=free_traffic,
            non_paid_traffic=non_paid_traffic,
            cancel_amount=cancel_amount,
            return_amount=return_amount,
            total_refund_amount=(cancel_amount or 0) + (return_amount or 0)
                                 if cancel_amount and return_amount else None,
            cancel_rate=None,
            return_rate=None,
            rrc=None,
            rrc_after_cancel=None
        )

        # 重新计算派生指标
        if orders and orders > 0:
            core_business.aov = core_business.gmv / orders

        if buyers and buyers > 0:
            core_business.atv = core_business.gmv / buyers

        if gmv_units and gmv_units > 0:
            core_business.aur = core_business.gmv / gmv_units

        if uv and uv > 0:
            core_business.cr = (buyers / uv) * 100

        # 计算退款率
        if cancel_amount and return_amount and gmv > 0:
            from .calculator import MetricCalculator
            core_business.cancel_rate = MetricCalculator.calculate_cancel_rate(
                cancel_amount, gmv
            )
            core_business.return_rate = MetricCalculator.calculate_return_rate(
                return_amount, gmv
            )
            core_business.rrc = MetricCalculator.calculate_rrc(
                return_amount, cancel_amount, gmv
            )
            core_business.rrc_after_cancel = MetricCalculator.calculate_rrc_after_cancel(
                return_amount, gmv, cancel_amount
            )

        return core_business

    def aggregate_monthly_with_exclusion(
        self,
        daily_metrics: List[TargetMetric],
        year: int,
        month: int,
        channel: ChannelType,
        exclusion_config: Optional[Dict[str, bool]] = None
    ) -> Optional[MonthlyMetrics]:
        """
        聚合指定月份的数据,支持渠道剔除

        Args:
            daily_metrics: 日度指标列表
            year: 年份
            month: 月份 (1-12)
            channel: 渠道
            exclusion_config: 剔除配置字典
                {
                    'exclude_ff': bool,  # 是否剔除FF
                    'exclude_social': bool  # 是否剔除SC
                }

        Returns:
            MonthlyMetrics对象,如果没有数据则返回None
        """
        if not daily_metrics:
            return None

        # 创建DataFrame
        df = pd.DataFrame([m.dict() for m in daily_metrics])

        # 转换日期列
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
        else:
            return None

        # 设置剔除配置
        if exclusion_config is None:
            exclusion_config = {
                'exclude_ff': self.exclude_ff,
                'exclude_social': self.exclude_social
            }

        # 过滤数据
        channel_str = channel.value if isinstance(channel, ChannelType) else channel
        monthly_df = df[
            (df['year'] == year) &
            (df['month'] == month) &
            (df['channel'] == channel_str)
        ]

        if monthly_df.empty:
            logger.warning(f"No data found for {year}-{month:02d} {channel}")
            return None

        # === 应用渠道剔除逻辑 ===
        # 对于DTC渠道,剔除FF和SC数据
        if channel == ChannelType.DTC and (exclusion_config['exclude_ff'] or exclusion_config['exclude_social']):
            # 剔除FF
            if exclusion_config['exclude_ff']:
                ff_net = monthly_df['dtc_ff_net'].fillna(0).sum()
                ff_gmv = monthly_df['dtc_ff_gmv'].fillna(0).sum()
                ff_uv = monthly_df['dtc_ff_traffic'].fillna(0).sum()

                # 从总数据中减去FF部分
                monthly_df['net'] = monthly_df['net'] - ff_net
                monthly_df['gmv'] = monthly_df['gmv'] - ff_gmv
                monthly_df['uv'] = monthly_df['uv'] - ff_uv

                logger.info(f"Excluded FF from DTC: FF_NET={ff_net:.2f}, FF_GMV={ff_gmv:.2f}, FF_UV={ff_uv}")

            # 剔除SC (Social)
            if exclusion_config['exclude_social']:
                sc_net = monthly_df['dtc_social_net'].fillna(0).sum()
                sc_gmv = monthly_df['dtc_social_gmv'].fillna(0).sum()
                sc_uv = monthly_df['dtc_social_traffic'].fillna(0).sum()

                # 从总数据中减去SC部分
                monthly_df['net'] = monthly_df['net'] - sc_net
                monthly_df['gmv'] = monthly_df['gmv'] - sc_gmv
                monthly_df['uv'] = monthly_df['uv'] - sc_uv

                logger.info(f"Excluded SC from DTC: SC_NET={sc_net:.2f}, SC_GMV={sc_gmv:.2f}, SC_UV={sc_uv}")

        # 计算聚合指标
        gmv = monthly_df['gmv'].fillna(0).sum()
        net = monthly_df['net'].fillna(0).sum()
        uv = int(max(0, monthly_df['uv'].fillna(0).sum()))  # 确保UV不为负
        buyers = int(monthly_df['buyers'].fillna(0).sum())
        paid_traffic = int(monthly_df['paid_traffic'].fillna(0).sum())
        free_traffic = int(monthly_df['free_traffic'].fillna(0).sum())
        non_paid_traffic = int(monthly_df.get('non_paid_traffic', pd.Series()).fillna(0).sum())

        # 计算派生指标
        orders = int(monthly_df['orders'].fillna(0).sum()) if 'orders' in monthly_df.columns else None
        gmv_units = int(monthly_df['gmv_units'].fillna(0).sum()) if 'gmv_units' in monthly_df.columns else None

        # 导入MetricCalculator
        from .calculator import MetricCalculator

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

        # 确定返回的渠道类型
        result_channel = channel
        if channel == ChannelType.DTC:
            if exclusion_config['exclude_ff'] and exclusion_config['exclude_social']:
                result_channel = ChannelType.DTC_EXCL_FF_SC
            elif exclusion_config['exclude_ff']:
                result_channel = ChannelType.DTC_EXCL_FF

        return MonthlyMetrics(
            year=year,
            month=month,
            channel=result_channel,
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
            non_paid_traffic=non_paid_traffic,
            cancel_amount=cancel_amount,
            return_amount=return_amount,
            total_refund_amount=(cancel_amount or 0) + (return_amount or 0)
                                 if cancel_amount is not None and return_amount is not None else None,
            cancel_rate=cancel_rate,
            return_rate=return_rate_val,
            rrc=rrc,
            rrc_after_cancel=rrc_after_cancel_val
        )

    def calculate_all_derived_channels(
        self,
        monthly_metrics: List[MonthlyMetrics]
    ) -> List[MonthlyMetrics]:
        """
        计算所有派生渠道指标

        Args:
            monthly_metrics: 已计算的月度指标列表

        Returns:
            包含派生渠道指标的完整列表
        """
        if not self.calculate_derived:
            return monthly_metrics

        # 按期间组织数据
        metrics_by_period: Dict[str, Dict[ChannelType, MonthlyMetrics]] = {}
        for metric in monthly_metrics:
            period = metric.period
            if period not in metrics_by_period:
                metrics_by_period[period] = {}
            metrics_by_period[period][metric.channel] = metric

        result = list(monthly_metrics)

        # 为每个期间计算派生渠道
        for period, channels in metrics_by_period.items():
            pfs = channels.get(ChannelType.PFS)
            dtc = channels.get(ChannelType.DTC)

            if not dtc:
                continue

            # 计算DTC_EXCL_FF_SC (如果已通过聚合生成则跳过)
            if ChannelType.DTC_EXCL_FF_SC not in channels:
                dtc_excl_ff_sc = self.calculate_dtc_excl_ff_sc(dtc)
                if dtc_excl_ff_sc:
                    result.append(dtc_excl_ff_sc)
                    channels[ChannelType.DTC_EXCL_FF_SC] = dtc_excl_ff_sc

            # 计算CORE_BUSINESS
            if pfs:
                dtc_excl_ff_sc = channels.get(ChannelType.DTC_EXCL_FF_SC, dtc)
                core_business = self.calculate_core_business(pfs, dtc_excl_ff_sc)
                if core_business:
                    result.append(core_business)

        logger.info(f"Calculated {len(result) - len(monthly_metrics)} derived channel metrics")
        return result

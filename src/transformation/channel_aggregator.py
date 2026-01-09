"""
渠道汇总计算器
实现渠道层级汇总逻辑: TOTAL = PFS + DTC, DTC = WBTQ + OFS
"""

from typing import List, Optional, Dict
from ..models.data_schema import MonthlyMetrics, ChannelType


class ChannelAggregator:
    """
    渠道汇总器
    计算渠道层级关系和汇总数据
    """

    @staticmethod
    def calculate_total_channel(
        pfs_metric: Optional[MonthlyMetrics],
        dtc_metric: Optional[MonthlyMetrics]
    ) -> Optional[MonthlyMetrics]:
        """
        计算TOTAL渠道 = PFS + DTC

        Args:
            pfs_metric: PFS渠道月度数据
            dtc_metric: DTC渠道月度数据

        Returns:
            TOTAL渠道月度数据，如果输入不完整则返回None
        """
        if not pfs_metric or not dtc_metric:
            return None

        # 确保期间一致
        if (pfs_metric.year != dtc_metric.year or
            pfs_metric.month != dtc_metric.month):
            return None

        # 合并退款相关字段
        cancel_amount = None
        return_amount = None
        if (pfs_metric.cancel_amount is not None and
            dtc_metric.cancel_amount is not None):
            cancel_amount = (pfs_metric.cancel_amount +
                           dtc_metric.cancel_amount)

        if (pfs_metric.return_amount is not None and
            dtc_metric.return_amount is not None):
            return_amount = (pfs_metric.return_amount +
                            dtc_metric.return_amount)

        # 计算订单数
        orders = None
        if pfs_metric.orders is not None and dtc_metric.orders is not None:
            orders = pfs_metric.orders + dtc_metric.orders

        # 创建TOTAL渠道数据
        total = MonthlyMetrics(
            year=pfs_metric.year,
            month=pfs_metric.month,
            channel=ChannelType.TOTAL,
            gmv=pfs_metric.gmv + dtc_metric.gmv,
            net=pfs_metric.net + dtc_metric.net,
            uv=pfs_metric.uv + dtc_metric.uv,
            buyers=pfs_metric.buyers + dtc_metric.buyers,
            orders=orders,
            aov=0.0,  # 需要重新计算
            atv=None,  # 需要重新计算
            cr=0.0,  # 需要重新计算
            paid_traffic=pfs_metric.paid_traffic + dtc_metric.paid_traffic,
            free_traffic=pfs_metric.free_traffic + dtc_metric.free_traffic,
            non_paid_traffic=pfs_metric.non_paid_traffic + dtc_metric.non_paid_traffic,
            cancel_amount=cancel_amount,
            return_amount=return_amount,
            total_refund_amount=(cancel_amount or 0) + (return_amount or 0) if cancel_amount and return_amount else None,
            cancel_rate=None,
            return_rate=None,
            rrc=None,
            rrc_after_cancel=None
        )

        # 重新计算派生指标
        if total.orders and total.orders > 0:
            total.aov = total.gmv / total.orders

        if total.buyers and total.buyers > 0:
            total.atv = total.gmv / total.buyers

        if total.uv and total.uv > 0:
            total.cr = (total.buyers / total.uv) * 100

        # 计算退款率
        if cancel_amount and return_amount and total.gmv > 0:
            from .calculator import MetricCalculator
            total.cancel_rate = MetricCalculator.calculate_cancel_rate(
                cancel_amount, total.gmv
            )
            total.return_rate = MetricCalculator.calculate_return_rate(
                return_amount, total.gmv
            )
            total.rrc = MetricCalculator.calculate_rrc(
                return_amount, cancel_amount, total.gmv
            )
            total.rrc_after_cancel = MetricCalculator.calculate_rrc_after_cancel(
                return_amount, total.gmv, cancel_amount
            )

        return total

    @staticmethod
    def calculate_dtc_channel(
        wbtq_metric: Optional[MonthlyMetrics],
        ofs_metric: Optional[MonthlyMetrics]
    ) -> Optional[MonthlyMetrics]:
        """
        计算DTC渠道 = WBTQ + OFS

        Args:
            wbtq_metric: WBTQ渠道月度数据
            ofs_metric: OFS渠道月度数据

        Returns:
            DTC渠道月度数据，如果输入不完整则返回None
        """
        if not wbtq_metric or not ofs_metric:
            return None

        # 确保期间一致
        if (wbtq_metric.year != ofs_metric.year or
            wbtq_metric.month != ofs_metric.month):
            return None

        # 合并退款相关字段
        cancel_amount = None
        return_amount = None
        if (wbtq_metric.cancel_amount is not None and
            ofs_metric.cancel_amount is not None):
            cancel_amount = (wbtq_metric.cancel_amount +
                           ofs_metric.cancel_amount)

        if (wbtq_metric.return_amount is not None and
            ofs_metric.return_amount is not None):
            return_amount = (wbtq_metric.return_amount +
                            ofs_metric.return_amount)

        # 计算订单数
        orders = None
        if wbtq_metric.orders is not None and ofs_metric.orders is not None:
            orders = wbtq_metric.orders + ofs_metric.orders

        # 创建DTC渠道数据
        dtc = MonthlyMetrics(
            year=wbtq_metric.year,
            month=wbtq_metric.month,
            channel=ChannelType.DTC,
            gmv=wbtq_metric.gmv + ofs_metric.gmv,
            net=wbtq_metric.net + ofs_metric.net,
            uv=wbtq_metric.uv + ofs_metric.uv,
            buyers=wbtq_metric.buyers + ofs_metric.buyers,
            orders=orders,
            aov=0.0,  # 需要重新计算
            atv=None,  # 需要重新计算
            cr=0.0,  # 需要重新计算
            paid_traffic=wbtq_metric.paid_traffic + ofs_metric.paid_traffic,
            free_traffic=wbtq_metric.free_traffic + ofs_metric.free_traffic,
            non_paid_traffic=wbtq_metric.non_paid_traffic + ofs_metric.non_paid_traffic,
            cancel_amount=cancel_amount,
            return_amount=return_amount,
            total_refund_amount=(cancel_amount or 0) + (return_amount or 0) if cancel_amount and return_amount else None,
            cancel_rate=None,
            return_rate=None,
            rrc=None,
            rrc_after_cancel=None
        )

        # 重新计算派生指标
        if dtc.orders and dtc.orders > 0:
            dtc.aov = dtc.gmv / dtc.orders

        if dtc.buyers and dtc.buyers > 0:
            dtc.atv = dtc.gmv / dtc.buyers

        if dtc.uv and dtc.uv > 0:
            dtc.cr = (dtc.buyers / dtc.uv) * 100

        # 计算退款率
        if cancel_amount and return_amount and dtc.gmv > 0:
            from .calculator import MetricCalculator
            dtc.cancel_rate = MetricCalculator.calculate_cancel_rate(
                cancel_amount, dtc.gmv
            )
            dtc.return_rate = MetricCalculator.calculate_return_rate(
                return_amount, dtc.gmv
            )
            dtc.rrc = MetricCalculator.calculate_rrc(
                return_amount, cancel_amount, dtc.gmv
            )
            dtc.rrc_after_cancel = MetricCalculator.calculate_rrc_after_cancel(
                return_amount, dtc.gmv, cancel_amount
            )

        return dtc

    @staticmethod
    def calculate_channel_breakdown(
        monthly_metrics: List[MonthlyMetrics]
    ) -> Dict[ChannelType, MonthlyMetrics]:
        """
        计算所有渠道的完整层级关系

        Args:
            monthly_metrics: 月度指标列表(包含各渠道数据)

        Returns:
            按渠道类型组织的字典，包含计算出的TOTAL和DTC
        """
        # 按渠道组织数据
        channels_by_type: Dict[ChannelType, MonthlyMetrics] = {}
        for metric in monthly_metrics:
            channels_by_type[metric.channel] = metric

        result = channels_by_type.copy()

        # 计算DTC = WBTQ + OFS
        wbtq = channels_by_type.get(ChannelType.WBTQ)
        ofs = channels_by_type.get(ChannelType.OFS)

        if wbtq and ofs:
            dtc = ChannelAggregator.calculate_dtc_channel(wbtq, ofs)
            if dtc:
                result[ChannelType.DTC] = dtc

        # 计算TOTAL = PFS + DTC
        pfs = channels_by_type.get(ChannelType.PFS)
        dtc = result.get(ChannelType.DTC)

        if pfs and dtc:
            total = ChannelAggregator.calculate_total_channel(pfs, dtc)
            if total:
                result[ChannelType.TOTAL] = total

        return result

    @staticmethod
    def validate_channel_hierarchy(
        monthly_metrics: List[MonthlyMetrics]
    ) -> List[str]:
        """
        验证渠道层级关系是否正确

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            错误信息列表，如果为空则验证通过
        """
        errors = []

        # 按渠道和期间组织
        metrics_by_period: Dict[str, Dict[ChannelType, MonthlyMetrics]] = {}
        for metric in monthly_metrics:
            period = f"{metric.year}-{metric.month:02d}"
            if period not in metrics_by_period:
                metrics_by_period[period] = {}
            metrics_by_period[period][metric.channel] = metric

        # 验证每个期间
        for period, channels in metrics_by_period.items():
            pfs = channels.get(ChannelType.PFS)
            dtc = channels.get(ChannelType.DTC)
            total = channels.get(ChannelType.TOTAL)

            # 验证 TOTAL = PFS + DTC
            if total and pfs and dtc:
                expected_net = pfs.net + dtc.net
                if abs(total.net - expected_net) > 0.01:  # 允许0.01的舍入误差
                    errors.append(
                        f"{period}: TOTAL.net ({total.net}) != "
                        f"PFS.net ({pfs.net}) + DTC.net ({dtc.net}) = {expected_net}"
                    )

                expected_gmv = pfs.gmv + dtc.gmv
                if abs(total.gmv - expected_gmv) > 0.01:
                    errors.append(
                        f"{period}: TOTAL.gmv ({total.gmv}) != "
                        f"PFS.gmv ({pfs.gmv}) + DTC.gmv ({dtc.gmv}) = {expected_gmv}"
                    )

            # 验证 DTC = WBTQ + OFS
            wbtq = channels.get(ChannelType.WBTQ)
            ofs = channels.get(ChannelType.OFS)

            if dtc and wbtq and ofs:
                expected_net = wbtq.net + ofs.net
                if abs(dtc.net - expected_net) > 0.01:
                    errors.append(
                        f"{period}: DTC.net ({dtc.net}) != "
                        f"WBTQ.net ({wbtq.net}) + OFS.net ({ofs.net}) = {expected_net}"
                    )

        return errors

    @staticmethod
    def calculate_channel_share(
        monthly_metrics: List[MonthlyMetrics]
    ) -> Dict[str, Dict[ChannelType, float]]:
        """
        计算各渠道的销售额占比

        Args:
            monthly_metrics: 月度指标列表

        Returns:
            按期间组织的渠道占比字典
        """
        shares: Dict[str, Dict[ChannelType, float]] = {}

        # 按期间组织
        metrics_by_period: Dict[str, Dict[ChannelType, MonthlyMetrics]] = {}
        for metric in monthly_metrics:
            period = f"{metric.year}-{metric.month:02d}"
            if period not in metrics_by_period:
                metrics_by_period[period] = {}
            metrics_by_period[period][metric.channel] = metric

        # 计算占比
        for period, channels in metrics_by_period.items():
            total = channels.get(ChannelType.TOTAL)
            if not total or total.net == 0:
                continue

            shares[period] = {}
            for channel, metric in channels.items():
                if channel == ChannelType.TOTAL:
                    continue
                share = (metric.net / total.net) * 100
                shares[period][channel] = round(share, 2)

        return shares

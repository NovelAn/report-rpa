"""
数据验证器
验证数据完整性、一致性和业务规则
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging

from pydantic import ValidationError

from ..models.data_schema import UnifiedReportData, TargetMetric, MonthlyMetrics, ChannelType

logger = logging.getLogger(__name__)


class ValidationResult:
    """验证结果类"""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.score: float = 100.0  # 数据质量评分 (0-100)

    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
        self.score = max(0, self.score - 10)  # 每个错误扣10分

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
        self.score = max(0, self.score - 2)  # 每个警告扣2分

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'score': round(self.score, 2)
        }


class DataValidator:
    """
    数据验证器
    """

    def __init__(self, strict_mode: bool = False):
        """
        初始化验证器

        Args:
            strict_mode: 严格模式,警告也会导致验证失败
        """
        self.strict_mode = strict_mode

    def validate_report_data(self, data: UnifiedReportData) -> ValidationResult:
        """
        验证完整的报告数据

        Args:
            data: 统一报告数据

        Returns:
            ValidationResult对象
        """
        result = ValidationResult()

        logger.info("Starting data validation")

        # 1. 检查数据完整性
        self._validate_completeness(data, result)

        # 2. 检查日期范围
        self._validate_date_coverage(data, result)

        # 3. 检查指标一致性
        self._validate_metric_consistency(data, result)

        # 4. 检查渠道覆盖
        self._validate_channel_coverage(data, result)

        # 5. 检查业务规则
        self._validate_business_rules(data, result)

        # 6. 检查月度数据
        self._validate_monthly_metrics(data, result)

        # 严格模式: 有警告也视为失败
        if self.strict_mode and result.warnings:
            result.is_valid = False

        logger.info(
            f"Validation completed: "
            f"is_valid={result.is_valid}, "
            f"errors={len(result.errors)}, "
            f"warnings={len(result.warnings)}, "
            f"score={result.score}"
        )

        return result

    def _validate_completeness(
        self,
        data: UnifiedReportData,
        result: ValidationResult
    ):
        """验证数据完整性"""
        # 检查日度指标
        if not data.target_metrics:
            result.add_error("No target metrics found")
        else:
            logger.debug(f"Found {len(data.target_metrics)} target metrics")

        # 检查月度指标
        if not data.monthly_metrics:
            result.add_warning("No monthly metrics calculated yet")

    def _validate_date_coverage(
        self,
        data: UnifiedReportData,
        result: ValidationResult
    ):
        """验证日期覆盖范围"""
        if not data.target_metrics:
            return

        dates = [m.date for m in data.target_metrics]
        unique_dates = set(dates)
        date_range = len(unique_dates)

        # 期望至少有20天的数据 (可根据实际情况调整)
        min_days = 20
        if date_range < min_days:
            result.add_warning(
                f"Limited date coverage: only {date_range} unique dates, "
                f"expected at least {min_days} days"
            )

        # 检查日期连续性
        sorted_dates = sorted(unique_dates)
        if len(sorted_dates) > 1:
            gaps = []
            for i in range(1, len(sorted_dates)):
                prev_date = sorted_dates[i - 1]
                curr_date = sorted_dates[i]
                delta = (curr_date - prev_date).days
                if delta > 1:
                    gaps.append(f"{prev_date} to {curr_date} ({delta} days)")

            if gaps:
                result.add_warning(
                    f"Date gaps detected: {', '.join(gaps[:3])}"
                    + ("..." if len(gaps) > 3 else "")
                )

    def _validate_metric_consistency(
        self,
        data: UnifiedReportData,
        result: ValidationResult
    ):
        """验证指标一致性"""
        for metric in data.target_metrics:
            # 检查UV和Buyers的关系
            if metric.uv and metric.uv > 0:
                if metric.buyers and metric.buyers > metric.uv:
                    result.add_error(
                        f"Invalid metric on {metric.date}: "
                        f"buyers ({metric.buyers}) cannot exceed UV ({metric.uv})"
                    )

            # 检查GMV和NET的关系
            if metric.gmv and metric.net:
                if metric.net > metric.gmv:
                    result.add_warning(
                        f"Unusual metric on {metric.date}: "
                        f"net ({metric.net}) exceeds GMV ({metric.gmv})"
                    )

            # 检查转化率
            if metric.cr is not None:
                calculated_cr = (
                    (metric.buyers / metric.uv * 100) if metric.uv and metric.buyers else None
                )
                if calculated_cr and abs(calculated_cr - metric.cr) > 1:
                    result.add_warning(
                        f"CR mismatch on {metric.date}: "
                        f"provided {metric.cr}%, calculated {calculated_cr:.2f}%"
                    )

    def _validate_channel_coverage(
        self,
        data: UnifiedReportData,
        result: ValidationResult
    ):
        """验证渠道覆盖"""
        if not data.target_metrics:
            return

        channels = set(m.channel for m in data.target_metrics)
        required_channels = {ChannelType.PFS, ChannelType.DTC, ChannelType.TOTAL}
        missing = required_channels - channels

        if missing:
            result.add_warning(
                f"Missing channels: {', '.join([c.value for c in missing])}"
            )

    def _validate_business_rules(
        self,
        data: UnifiedReportData,
        result: ValidationResult
    ):
        """验证业务规则"""
        for metric in data.target_metrics:
            # 检查负值
            if metric.net and metric.net < 0:
                result.add_error(f"Negative NET on {metric.date}: {metric.net}")

            if metric.gmv and metric.gmv < 0:
                result.add_error(f"Negative GMV on {metric.date}: {metric.gmv}")

            if metric.uv and metric.uv < 0:
                result.add_error(f"Negative UV on {metric.date}: {metric.uv}")

    def _validate_monthly_metrics(
        self,
        data: UnifiedReportData,
        result: ValidationResult
    ):
        """验证月度指标"""
        if not data.monthly_metrics:
            return

        # 检查是否有重复的月份
        seen = {}
        for metric in data.monthly_metrics:
            key = (metric.channel.value, metric.year, metric.month)
            if key in seen:
                result.add_error(
                    f"Duplicate monthly metric for {metric.channel.value} "
                    f"{metric.year}-{metric.month:02d}"
                )
            seen[key] = metric

        # 检查YoY增长率的合理性
        for metric in data.monthly_metrics:
            if metric.yoy_growth is not None:
                if abs(metric.yoy_growth) > 1000:  # 超过1000%的增长可能是异常
                    result.add_warning(
                        f"Extreme YoY growth for {metric.channel.value} "
                        f"{metric.year}-{metric.month:02d}: {metric.yoy_growth:.2f}%"
                    )

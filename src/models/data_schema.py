"""
MBR数据模型定义
使用Pydantic进行类型验证和数据管理
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime
from enum import Enum
import pandas as pd


class FiscalYear:
    """
    财年处理类
    财年定义: 每年4月开始,次年3月结束

    规则:
    - 2025-04-01: Fiscal Year = 2026 (FY26), Month = 4, Fiscal Quarter = Q1, Period = FY26-Q1-04
    - 2025-06-30: Fiscal Year = 2026 (FY26), Month = 6, Fiscal Quarter = Q1, Period = FY26-Q1-06
    - 2025-07-01: Fiscal Year = 2026 (FY26), Month = 7, Fiscal Quarter = Q2, Period = FY26-Q2-07
    - 2026-03-31: Fiscal Year = 2026 (FY26), Month = 3, Fiscal Quarter = Q4, Period = FY26-Q4-03
    """

    @staticmethod
    def get_fiscal_year(date_value: date) -> int:
        """
        获取日期所属财年

        规则: 4月1日开始新财年(年份+1)
        例如: 2025-04-01 -> 2026 (FY26)
              2026-03-31 -> 2026 (FY26)

        Args:
            date_value: 日期

        Returns:
            财年 (完整年份, 如2026)
        """
        year = date_value.year
        month = date_value.month

        # 4月及以后属于下一年财年
        # 1-3月属于当年财年
        # 例如: 2025年4月及以后属于FY26, 2026年1-3月属于FY26
        if month >= 4:
            return year + 1
        else:
            return year

    @staticmethod
    def get_fiscal_year_str(date_value: date) -> str:
        """
        获取财年字符串表示

        Returns:
            财年字符串, 如 "FY25"
        """
        fy = FiscalYear.get_fiscal_year(date_value)
        return f"FY{fy % 100}"  # 取后两位,如2025->25

    @staticmethod
    def get_fiscal_quarter(date_value: date) -> int:
        """
        获取财季度 (Q1-Q4)
        4-6月=Q1, 7-9月=Q2, 10-12月=Q3, 1-3月=Q4

        Returns:
            财季度 (1-4)
        """
        month = date_value.month
        if 4 <= month <= 6:
            return 1  # Q1
        elif 7 <= month <= 9:
            return 2  # Q2
        elif 10 <= month <= 12:
            return 3  # Q3
        else:  # 1-3月
            return 4  # Q4

    @staticmethod
    def get_fiscal_quarter_str(date_value: date) -> str:
        """
        获取财季字符串

        Returns:
            财季字符串, 如 "Q1"
        """
        fq = FiscalYear.get_fiscal_quarter(date_value)
        return f"Q{fq}"

    @staticmethod
    def get_fiscal_period(date_value: date) -> str:
        """
        获取完整财期字符串 (财年-财季-月)

        Returns:
            财期字符串, 如 "FY25-Q1-04" (2025年4月)
        """
        fy = FiscalYear.get_fiscal_year(date_value)
        fq = FiscalYear.get_fiscal_quarter(date_value)
        month = date_value.month
        return f"FY{fy % 100}-Q{fq}-{month:02d}"

    @staticmethod
    def parse_fiscal_period(fiscal_period: str) -> Tuple[int, int, int]:
        """
        解析财期字符串

        Args:
            fiscal_period: 财期字符串, 如 "FY25-Q1-04"

        Returns:
            (财年, 财季, 月) 元组
        """
        parts = fiscal_period.split('-')
        fy_str = parts[0].replace('FY', '')
        fy = 2000 + int(fy_str) if int(fy_str) < 50 else 1900 + int(fy_str)
        fq = int(parts[1].replace('Q', ''))
        month = int(parts[2])
        return (fy, fq, month)


class ChannelType(str, Enum):
    """渠道类型枚举

    渠道层级结构:
    TOTAL (全渠道) = PFS + DTC

    PFS (Platform Full Service - 平台渠道):
        - TMALL (天猫)
        - JD (京东)
        - 其他第三方平台

    DTC (Direct to Consumer - 直营渠道):
        - WBTQ (微信小程序)
        - OFS (线下门店+官网)
        - 销售来源: Social + FF + Organic
    """
    PFS = "PFS"  # Platform Full Service (天猫/京东等第三方平台)
    DTC = "DTC"  # Direct to Consumer (直营渠道: WBTQ + OFS)
    WBTQ = "WBTQ"  # WeChat Mini Program (微信小程序)
    OFS = "OFS"  # Offline Store + Official Website (线下门店+官网)
    TOTAL = "TOTAL"  # 全渠道汇总 (PFS + DTC)
    TMALL = "TMALL"  # 天猫 (PFS子渠道)


class MetricType(str, Enum):
    """指标类型枚举"""
    GMV = "gmv"
    NET = "net"
    UV = "uv"
    BUYERS = "buyers"
    UNITS = "units"
    CR = "cr"
    AOV = "aov"
    ATV = "atv"
    UPT = "upt"
    TRAFFIC_PAID = "paid_traffic"
    TRAFFIC_NON_PAID = "non_paid_traffic"
    
class TargetMetric(BaseModel):
    """
    目标表 - 日度KPI指标
    对应Excel工作表: 目标表
    """
    date: date
    channel: ChannelType = Field(default=ChannelType.TOTAL)

    # 核心销售指标
    gmv: Optional[float] = Field(default=None, description="商品交易总额")
    net: Optional[float] = Field(default=None, description="净销售额")
    net_units: Optional[int] = Field(default=None, description="净销售件数")
    gmv_units: Optional[int] = Field(default=None, description="GMV件数")
    rrc: Optional[float] = Field(default=None, description="总退款率")
    rrc_after_cancel: Optional[float] = Field(default=None, description="取消后退款率")
    upt: Optional[float] = Field(default=None, description="连带率")

    # 流量指标
    uv: Optional[int] = Field(default=None, description="访客数")
    cr: Optional[float] = Field(default=None, description="转化率")
    aov: Optional[float] = Field(default=None, description="平均订单价值 (GMV/Orders)")
    atv: Optional[float] = Field(default=None, description="平均交易价值 (GMV/Buyers)")
    aur: Optional[float] = Field(default=None, description="件单价 (GMV/GMV_Units)")
    buyers: Optional[int] = Field(default=None, description="购买人数")
    orders: Optional[int] = Field(default=None, description="订单数")

    # 流量来源
    free_traffic: Optional[int] = Field(default=None, description="免费流量")
    paid_traffic: Optional[int] = Field(default=None, description="付费流量")

    # 退款相关字段
    cancel_amount: Optional[float] = Field(default=None, description="取消金额")
    return_amount: Optional[float] = Field(default=None, description="退货退款金额")
    total_refund_amount: Optional[float] = Field(default=None, description="总退款金额")
    cancel_rate: Optional[float] = Field(default=None, description="取消率")
    return_rate: Optional[float] = Field(default=None, description="退货率")

    # DTC Social 渠道 (社群推广)
    dtc_social_net: Optional[float] = Field(default=None, description="DTC社群推广净销售")
    dtc_social_gmv: Optional[float] = Field(default=None, description="DTC社群推广GMV")
    dtc_social_rrc: Optional[float] = Field(default=None, description="DTC社群推广退款率")
    dtc_social_traffic: Optional[int] = Field(default=None, description="DTC社群推广流量")

    # DTC Ad/Paid 渠道 (广告推广) - 朋友圈广告、Banner、小红书、KOL/KOC付费等
    dtc_ad_net: Optional[float] = Field(default=None, description="DTC广告推广净销售")
    dtc_ad_gmv: Optional[float] = Field(default=None, description="DTC广告推广GMV")
    dtc_ad_rrc: Optional[float] = Field(default=None, description="DTC广告推广退款率")
    dtc_ad_traffic: Optional[int] = Field(default=None, description="DTC广告推广流量")
    dtc_ad_spend: Optional[float] = Field(default=None, description="DTC广告推广花费")

    # DTC Organic 渠道 (自然流量)
    dtc_organic_net: Optional[float] = Field(default=None, description="DTC自然渠道净销售")
    dtc_organic_gmv: Optional[float] = Field(default=None, description="DTC自然渠道GMV")
    dtc_organic_rrc: Optional[float] = Field(default=None, description="DTC自然渠道退款率")
    dtc_organic_traffic: Optional[int] = Field(default=None, description="DTC自然渠道流量")

    @field_validator('cr', 'rrc')
    @classmethod
    def validate_percentage(cls, v):
        """验证百分比字段在合理范围内"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError(f'Percentage value must be between 0 and 100, got {v}')
        return v

    @field_validator('aov', 'atv')
    @classmethod
    def validate_positive_value(cls, v):
        """验证AOV/ATV为非负数"""
        if v is not None and v < 0:
            raise ValueError(f'Value must be non-negative, got {v}')
        return v

    @field_validator('buyers')
    @classmethod
    def validate_buyers_not_exceed_uv(cls, v, info):
        """验证购买人数不应超过访客数"""
        if v is not None:
            uv_value = info.data.get('uv')
            if uv_value and v > uv_value:
                raise ValueError(f'Buyers ({v}) cannot exceed UV ({uv_value})')
        return v

    @property
    def fiscal_year(self) -> int:
        """获取财年"""
        return FiscalYear.get_fiscal_year(self.date)

    @property
    def fiscal_year_str(self) -> str:
        """获取财年字符串 (如 'FY26')"""
        return FiscalYear.get_fiscal_year_str(self.date)

    @property
    def fiscal_month(self) -> int:
        """获取财月 (1-12, 使用自然月)"""
        return self.date.month

    @property
    def fiscal_period(self) -> str:
        """获取财期字符串 (如 'FY26-Q1-04')"""
        return FiscalYear.get_fiscal_period(self.date)


class TrafficMetrics(BaseModel):
    """
    流量指标 - 多层级流量源数据
    对应Excel工作表: 一级流量源, 二级流量源, 三级流量源
    """
    source_name: str = Field(description="流量源名称")
    source_level: int = Field(ge=1, le=3, description="流量源层级 (1-3)")
    traffic_type: str = Field(description="流量类型 (paid/free/organic)")
    channel: ChannelType = Field(default=ChannelType.TOTAL)

    # 核心指标
    uv: Optional[int] = Field(default=None, description="UV")
    buyers: Optional[int] = Field(default=None, description="购买人数")
    cr: Optional[float] = Field(default=None, description="转化率")
    gmv: Optional[float] = Field(default=None, description="GMV")
    net: Optional[float] = Field(default=None, description="净销售")

    # 时间维度
    year: Optional[int] = Field(default=None)
    month: Optional[int] = Field(default=None, ge=1, le=12)


class CampaignEvent(BaseModel):
    """
    活动事件 - Campaign时间线和业绩
    对应Excel工作表: Campaign
    """
    campaign_name: str = Field(description="活动名称")
    start_date: date = Field(description="开始日期")
    end_date: date = Field(description="结束日期")
    channel: ChannelType = Field(default=ChannelType.PFS)

    # 业绩数据
    gmv: Optional[float] = Field(default=None, description="活动GMV")
    net: Optional[float] = Field(default=None, description="活动净销售")
    uv: Optional[int] = Field(default=None, description="活动UV")
    buyers: Optional[int] = Field(default=None, description="活动购买人数")
    aov: Optional[float] = Field(default=None, description="活动AOV")
    atv: Optional[float] = Field(default=None, description="活动ATV")
    rrc: Optional[float] = Field(default=None, description="活动退款率")
    cr: Optional[float] = Field(default=None, description="活动转化率")
    md_net_share: Optional[float] = Field(default=None, description="活动md商品净销售占比")

    # 其他信息
    highlights: List[str] = Field(default_factory=list, description="活动亮点")
    campaign_type: Optional[str] = Field(default=None, description="活动类型")


class MonthlyMetrics(BaseModel):
    """
    月度指标 - 聚合后的月度数据
    用于YTD和月度分析
    """
    year: int
    month: int = Field(ge=1, le=12)
    channel: ChannelType

    # 核心指标
    gmv: float = Field(ge=0)
    net: float = Field(ge=0)
    uv: int = Field(ge=0)
    buyers: int = Field(ge=0)
    orders: Optional[int] = Field(default=None, ge=0, description="订单数")
    gmv_units: Optional[int] = Field(default=None, ge=0, description="GMV件数")
    aov: float = Field(ge=0, description="平均订单价值 (GMV/Orders)")
    atv: Optional[float] = Field(default=None, ge=0, description="平均交易价值 (GMV/Buyers)")
    aur: Optional[float] = Field(default=None, ge=0, description="件单价 (GMV/GMV_Units)")
    cr: float = Field(ge=0, le=100)
    paid_traffic: int = Field(ge=0)
    non_paid_traffic: int = Field(ge=0)
    free_traffic: int = Field(ge=0)

    # 退款相关字段
    cancel_amount: Optional[float] = Field(default=None, ge=0, description="取消金额")
    return_amount: Optional[float] = Field(default=None, ge=0, description="退货退款金额")
    total_refund_amount: Optional[float] = Field(default=None, ge=0, description="总退款金额")
    cancel_rate: Optional[float] = Field(default=None, ge=0, le=100, description="取消率")
    return_rate: Optional[float] = Field(default=None, ge=0, le=100, description="退货率")
    rrc: Optional[float] = Field(default=None, ge=0, le=100, description="总退款率")
    rrc_after_cancel: Optional[float] = Field(default=None, ge=0, le=100, description="取消后退款率")

    # 同期对比 (计算后填充)
    ly_gmv: Optional[float] = Field(default=None, description="去年同月GMV")
    ly_net: Optional[float] = Field(default=None, description="去年同月净销售")
    ly_uv: Optional[int] = Field(default=None, description="去年同月UV")
    yoy_growth: Optional[float] = Field(default=None, description="同比增长率")
    mom_growth: Optional[float] = Field(default=None, description="环比增长率")

    @property
    def period(self) -> str:
        """返回期间字符串 (YYYY-MM)"""
        return f"{self.year}-{self.month:02d}"

    @property
    def fiscal_year(self) -> int:
        """获取财年"""
        # 创建日期对象以计算财年
        date_value = date(self.year, self.month, 1)
        return FiscalYear.get_fiscal_year(date_value)

    @property
    def fiscal_year_str(self) -> str:
        """获取财年字符串 (如 'FY26')"""
        date_value = date(self.year, self.month, 1)
        return FiscalYear.get_fiscal_year_str(date_value)

    @property
    def fiscal_month(self) -> int:
        """获取财月 (1-12, 使用自然月)"""
        return self.month

    @property
    def fiscal_period(self) -> str:
        """获取财期字符串 (如 'FY26-Q1-04')"""
        date_value = date(self.year, self.month, 1)
        return FiscalYear.get_fiscal_period(date_value)

    @property
    def is_first_fiscal_month(self) -> bool:
        """是否是财年第1个月 (4月)"""
        return self.month == 4

    @property
    def is_last_fiscal_month(self) -> bool:
        """是否是财年最后1个月 (次年3月)"""
        return self.month == 3


class SalesOverview(BaseModel):
    """
    销售总览
    对应Excel工作表: SalesOverview
    """
    period: str
    bu: str = Field(default="BU26", description="业务单元")

    # 渠道销售数据
    pfs_net: Optional[float] = Field(default=None)
    dtc_net: Optional[float] = Field(default=None)
    total_net: Optional[float] = Field(default=None)

    # 活动贡献
    campaign_contribution: Optional[float] = Field(default=None, description="活动贡献率")

    # 日期范围
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)


class CompetitorTraffic(BaseModel):
    """
    竞品流量数据
    对应Excel工作表: 竞店流量summary, 竞店流量取数_月度
    """
    competitor_name: str
    period: str

    # 流量数据
    traffic: Optional[int] = Field(default=None, description="竞品UV")
    yoy_growth: Optional[float] = Field(default=None, description="同比增长率")

    # 购买数据
    buyers: Optional[int] = Field(default=None)
    cvr: Optional[float] = Field(default=None, description="转化率")


class MemberData(BaseModel):
    """
    会员数据
    对应Excel工作表: fans&member, 会员源, 粉丝源
    """
    period: str

    # 会员数量
    total_members: Optional[int] = Field(default=None, description="总会员数")
    vic_count: Optional[int] = Field(default=None, description="VIC会员数")
    new_members: Optional[int] = Field(default=None, description="新增会员数")

    # 会员消费
    member_net: Optional[float] = Field(default=None, description="会员净销售")
    member_net_ratio: Optional[float] = Field(default=None, description="会员销售占比")

    # 粉丝数据
    total_fans: Optional[int] = Field(default=None, description="总粉丝数")
    new_fans: Optional[int] = Field(default=None, description="新增粉丝数")

    # 城市分布
    top_cities: Optional[List[Dict[str, Any]]] = Field(default=None, description="Top城市分布")


class UnifiedReportData(BaseModel):
    """
    统一报告数据容器
    包含生成MBR报告所需的所有数据
    """
    # 报告基本信息
    report_period: str = Field(description="报告期间 (YYYY-MM)")
    brand: str = Field(default="dunhill", description="品牌")
    bu: str = Field(default="BU26", description="业务单元")

    # 数据源信息
    data_source_version: Optional[str] = Field(default=None, description="数据版本")
    generated_at: datetime = Field(default_factory=datetime.now)

    # 核心数据
    target_metrics: List[TargetMetric] = Field(default_factory=list)
    monthly_metrics: List[MonthlyMetrics] = Field(default_factory=list)
    campaigns: List[CampaignEvent] = Field(default_factory=list)

    # 流量数据 (按渠道和层级组织)
    traffic_sources: Dict[str, List[TrafficMetrics]] = Field(
        default_factory=dict,
        description="流量源数据, key为channel名称"
    )

    # 其他数据
    sales_overview: Optional[SalesOverview] = Field(default=None)
    competitor_data: Optional[List[CompetitorTraffic]] = Field(default=None)
    member_data: Optional[MemberData] = Field(default=None)

    # 渠道映射
    channel_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="渠道名称映射表"
    )

    def get_channel_metrics(
        self,
        channel: ChannelType,
        period: str
    ) -> Optional[MonthlyMetrics]:
        """获取指定渠道和期间的数据"""
        for metric in self.monthly_metrics:
            if metric.channel == channel and metric.period == period:
                return metric
        return None

    def get_traffic_by_channel(
        self,
        channel: ChannelType
    ) -> List[TrafficMetrics]:
        """获取指定渠道的流量数据"""
        return self.traffic_sources.get(channel.value, [])

    def get_campaigns_by_period(
        self,
        period: str
    ) -> List[CampaignEvent]:
        """获取指定期间的活动"""
        result = []
        for campaign in self.campaigns:
            campaign_period = f"{campaign.start_date.year}-{campaign.start_date.month:02d}"
            if campaign_period == period:
                result.append(campaign)
        return result

    def calculate_total_net(self) -> float:
        """计算总净销售"""
        return sum(m.net for m in self.monthly_metrics)

    def calculate_ytd_net(self, through_month: int) -> float:
        """计算年初至今净销售"""
        year = int(self.report_period.split('-')[0])
        ytd_metrics = [
            m for m in self.monthly_metrics
            if m.year == year and m.month <= through_month
        ]
        return sum(m.net for m in ytd_metrics)


# 辅助函数
def dataframe_to_target_metrics(df: pd.DataFrame) -> List[TargetMetric]:
    """
    将DataFrame转换为TargetMetric列表

    Args:
        df: 包含目标表数据的DataFrame

    Returns:
        TargetMetric对象列表
    """
    metrics = []

    for _, row in df.iterrows():
        try:
            # 处理日期
            if 'Date' in row and pd.notna(row['Date']):
                date_value = pd.to_datetime(row['Date']).date()
            else:
                continue

            # 提取渠道 (如果存在)
            channel = row.get('channel', ChannelType.TOTAL)
            if isinstance(channel, str):
                try:
                    channel = ChannelType(channel)
                except ValueError:
                    channel = ChannelType.TOTAL

            metric = TargetMetric(
                date=date_value,
                channel=channel,
                gmv=row.get('gmv') if pd.notna(row.get('gmv')) else None,
                net=row.get('net') if pd.notna(row.get('net')) else None,
                net_units=int(row.get('net_units')) if pd.notna(row.get('net_units')) else None,
                gmv_units=int(row.get('gmv_units')) if pd.notna(row.get('gmv_units')) else None,
                rrc=row.get('rrc') if pd.notna(row.get('rrc')) else None,
                uv=int(row.get('uv')) if pd.notna(row.get('uv')) else None,
                cr=row.get('cr') if pd.notna(row.get('cr')) else None,
                aov=row.get('aov') if pd.notna(row.get('aov')) else None,
                atv=row.get('atv') if pd.notna(row.get('atv')) else None,
                buyers=int(row.get('buyers')) if pd.notna(row.get('buyers')) else None,
                free_traffic=int(row.get('free_traffic')) if pd.notna(row.get('free_traffic')) else None,
                paid_traffic=int(row.get('paid_traffic')) if pd.notna(row.get('paid_traffic')) else None,
                dtc_social_net=row.get('dtc_social_net') if pd.notna(row.get('dtc_social_net')) else None,
                dtc_social_gmv=row.get('dtc_social_gmv') if pd.notna(row.get('dtc_social_gmv')) else None,
                dtc_social_rrc=row.get('dtc_social_rrc') if pd.notna(row.get('dtc_social_rrc')) else None,
                dtc_social_traffic=int(row.get('dtc_social_traffic')) if pd.notna(row.get('dtc_social_traffic')) else None,
                dtc_organic_net=row.get('dtc_organic_net') if pd.notna(row.get('dtc_organic_net')) else None,
                dtc_organic_gmv=row.get('dtc_organic_gmv') if pd.notna(row.get('dtc_organic_gmv')) else None,
                dtc_organic_rrc=row.get('dtc_organic_rrc') if pd.notna(row.get('dtc_organic_rrc')) else None,
                dtc_organic_traffic=int(row.get('dtc_organic_traffic')) if pd.notna(row.get('dtc_organic_traffic')) else None,
            )
            metrics.append(metric)
        except Exception as e:
            # 跳过无效行,继续处理
            print(f"Warning: Failed to parse row: {e}")
            continue

    return metrics

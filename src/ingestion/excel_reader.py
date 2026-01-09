"""
Excel数据读取器
读取MBR Excel模板文件并解析为统一数据模型
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..models.data_schema import (
    UnifiedReportData,
    TargetMetric,
    MonthlyMetrics,
    CampaignEvent,
    TrafficMetrics,
    SalesOverview,
    CompetitorTraffic,
    MemberData,
    ChannelType,
    dataframe_to_target_metrics
)

logger = logging.getLogger(__name__)


class ExcelDataReader:
    """
    Excel MBR模板读取器
    读取22个工作表并解析为结构化数据
    """

    # 必需的工作表
    REQUIRED_SHEETS = ['目标表']
    # 可选的工作表
    OPTIONAL_SHEETS = [
        'Campaign', 'SalesOverview', '全店核心数据_bymonth',
        'PFS_流量呈现', 'dunhill traffic pivot', '竞店流量summary',
        '竞店流量取数_月度', '一级流量源', '二级流量源', '三级流量源',
        '其他猜你喜欢源', '竞店一级数据源', '竞店PAID三级数据源',
        'fans&member', 'dtc_channel_show', '公众号', '会员源', '粉丝源',
        'dtc_channel源', 'channel Mapping', '买家画像对比'
    ]

    def __init__(self, file_path: Path):
        """
        初始化Excel读取器

        Args:
            file_path: Excel文件路径
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        self.excel_file: Optional[pd.ExcelFile] = None
        self.sheet_data: Dict[str, pd.DataFrame] = {}
        self._load_excel()

    def _load_excel(self):
        """加载Excel文件"""
        try:
            self.excel_file = pd.ExcelFile(self.file_path)
            logger.info(f"Loaded Excel file: {self.file_path}")
            logger.info(f"Available sheets: {self.excel_file.sheet_names}")
        except Exception as e:
            raise ValueError(f"Failed to load Excel file: {e}")

    def read_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        读取所有工作表

        Returns:
            字典, key为sheet名称, value为DataFrame
        """
        if not self.excel_file:
            self._load_excel()

        for sheet_name in self.excel_file.sheet_names:
            try:
                df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
                self.sheet_data[sheet_name] = df
                logger.debug(f"Read sheet '{sheet_name}': {df.shape}")
            except Exception as e:
                logger.warning(f"Failed to read sheet '{sheet_name}': {e}")
                self.sheet_data[sheet_name] = pd.DataFrame()

        return self.sheet_data

    def parse_target_table(self) -> List[TargetMetric]:
        """
        解析目标表工作表

        Returns:
            TargetMetric对象列表
        """
        if '目标表' not in self.sheet_data:
            logger.warning("Sheet '目标表' not found")
            return []

        df = self.sheet_data['目标表']

        # 清洗数据
        df = df.dropna(how='all')  # 删除全空行

        if df.empty:
            logger.warning("Sheet '目标表' is empty")
            return []

        logger.info(f"Parsing '目标表' with {len(df)} rows")

        # 使用辅助函数转换
        metrics = dataframe_to_target_metrics(df)

        logger.info(f"Parsed {len(metrics)} target metrics")
        return metrics

    def parse_campaign_sheet(self) -> List[CampaignEvent]:
        """
        解析Campaign工作表

        Returns:
            CampaignEvent对象列表
        """
        if 'Campaign' not in self.sheet_data:
            return []

        df = self.sheet_data['Campaign']
        df = df.dropna(how='all')

        campaigns = []
        for _, row in df.iterrows():
            try:
                # 提取活动名称
                campaign_name = row.get('Campaign', row.get('campaign', ''))
                if not campaign_name or pd.isna(campaign_name):
                    continue

                # 提取日期 (可能在不同列)
                start_date = None
                end_date = None

                # 尝试从多个可能的列名提取日期
                date_cols = ['Start Date', 'start_date', 'Date', 'date']
                for col in date_cols:
                    if col in row and pd.notna(row[col]):
                        try:
                            start_date = pd.to_datetime(row[col]).date()
                            break
                        except:
                            pass

                # 如果找不到明确的日期列,使用索引
                if not start_date:
                    for col in df.columns:
                        if pd.notna(row[col]):
                            try:
                                date_val = pd.to_datetime(row[col])
                                if hasattr(date_val, 'date'):
                                    start_date = date_val.date()
                                    break
                            except:
                                continue

                if not start_date:
                    continue

                # 创建活动对象
                campaign = CampaignEvent(
                    campaign_name=str(campaign_name),
                    start_date=start_date,
                    end_date=end_date or start_date,  # 默认当天
                    gmv=row.get('GMV', row.get('gmv')) if pd.notna(row.get('GMV', row.get('gmv'))) else None,
                    net=row.get('NET', row.get('net')) if pd.notna(row.get('NET', row.get('net'))) else None,
                    uv=int(row.get('UV', row.get('uv', 0))) if pd.notna(row.get('UV', row.get('uv'))) else None,
                    buyers=int(row.get('Buyers', row.get('buyers', 0))) if pd.notna(row.get('Buyers', row.get('buyers'))) else None,
                )
                campaigns.append(campaign)
            except Exception as e:
                logger.debug(f"Failed to parse campaign row: {e}")
                continue

        logger.info(f"Parsed {len(campaigns)} campaigns")
        return campaigns

    def parse_traffic_sources(self) -> Dict[str, List[TrafficMetrics]]:
        """
        解析流量源工作表 (一级、二级、三级)

        Returns:
            字典, key为channel, value为TrafficMetrics列表
        """
        traffic_data = {}

        # 检查各级流量源工作表
        traffic_sheets = {
            '一级': '一级流量源',
            '二级': '二级流量源',
            '三级': '三级流量源'
        }

        for level_name, sheet_name in traffic_sheets.items():
            if sheet_name not in self.sheet_data:
                continue

            df = self.sheet_data[sheet_name]
            df = df.dropna(how='all')

            if df.empty:
                continue

            # 提取流量源数据
            for _, row in df.iterrows():
                try:
                    # 获取流量源名称
                    source_name_col = None
                    for col in df.columns:
                        if 'source' in col.lower() or 'name' in col.lower() or '流量源' in col:
                            source_name_col = col
                            break

                    if not source_name_col:
                        continue

                    source_name = row.get(source_name_col)
                    if pd.isna(source_name):
                        continue

                    # 创建TrafficMetrics对象
                    level = int(level_name.replace('级', ''))

                    metric = TrafficMetrics(
                        source_name=str(source_name),
                        source_level=level,
                        traffic_type='unknown',  # 需要根据数据推断
                        uv=int(row.get('UV', 0)) if pd.notna(row.get('UV')) else None,
                        buyers=int(row.get('Buyers', 0)) if pd.notna(row.get('Buyers')) else None,
                        gmv=row.get('GMV', row.get('gmv')) if pd.notna(row.get('GMV', row.get('gmv'))) else None,
                        net=row.get('NET', row.get('net')) if pd.notna(row.get('NET', row.get('net'))) else None,
                    )

                    # 按渠道分组 (这里简化处理,实际需要根据数据结构调整)
                    channel_key = 'TOTAL'
                    if channel_key not in traffic_data:
                        traffic_data[channel_key] = []
                    traffic_data[channel_key].append(metric)

                except Exception as e:
                    logger.debug(f"Failed to parse traffic row: {e}")
                    continue

        logger.info(f"Parsed traffic data for {len(traffic_data)} channels")
        return traffic_data

    def parse_sales_overview(self) -> Optional[SalesOverview]:
        """
        解析SalesOverview工作表

        Returns:
            SalesOverview对象或None
        """
        if 'SalesOverview' not in self.sheet_data:
            return None

        df = self.sheet_data['SalesOverview']
        # SalesOverview结构较复杂,这里简化处理
        # 实际需要根据具体数据结构调整

        return SalesOverview(
            period="2025-12",  # 需要从数据中提取
            bu="BU26"
        )

    def parse_competitor_traffic(self) -> Optional[List[CompetitorTraffic]]:
        """
        解析竞品流量数据

        Returns:
            CompetitorTraffic列表或None
        """
        if '竞店流量summary' not in self.sheet_data:
            return None

        df = self.sheet_data['竞店流量summary']
        df = df.dropna(how='all')

        if df.empty:
            return None

        competitors = []
        # 解析竞品数据逻辑...
        # 需要根据实际数据结构调整

        return competitors

    def parse_member_data(self) -> Optional[MemberData]:
        """
        解析会员数据

        Returns:
            MemberData对象或None
        """
        if 'fans&member' not in self.sheet_data:
            return None

        df = self.sheet_data['fans&member']
        # 解析会员数据逻辑...
        # 需要根据实际数据结构调整

        return MemberData(period="2025-12")

    def parse_all(self) -> UnifiedReportData:
        """
        解析所有工作表并返回统一报告数据

        Returns:
            UnifiedReportData对象
        """
        logger.info("Starting to parse all sheets from Excel")

        # 确保所有sheet已读取
        if not self.sheet_data:
            self.read_all_sheets()

        # 解析各个工作表
        target_metrics = self.parse_target_table()
        campaigns = self.parse_campaign_sheet()
        traffic_sources = self.parse_traffic_sources()
        sales_overview = self.parse_sales_overview()
        competitor_data = self.parse_competitor_traffic()
        member_data = self.parse_member_data()

        # 提取报告期间 (从目标表推断)
        report_period = "2025-12"  # 默认值
        if target_metrics:
            # 使用最后一个日期的年月
            last_metric = target_metrics[-1]
            report_period = f"{last_metric.date.year}-{last_metric.date.month:02d}"

        # 创建统一数据对象
        report_data = UnifiedReportData(
            report_period=report_period,
            target_metrics=target_metrics,
            campaigns=campaigns,
            traffic_sources=traffic_sources,
            sales_overview=sales_overview,
            competitor_data=competitor_data,
            member_data=member_data,
            monthly_metrics=[]  # 将由transformation模块填充
        )

        logger.info(f"Parsed complete report data for period: {report_period}")
        logger.info(f"  - Target metrics: {len(target_metrics)}")
        logger.info(f"  - Campaigns: {len(campaigns)}")
        logger.info(f"  - Traffic sources: {sum(len(v) for v in traffic_sources.values())}")

        return report_data


def read_excel_template(file_path: Path) -> UnifiedReportData:
    """
    便捷函数: 读取Excel模板文件

    Args:
        file_path: Excel文件路径

    Returns:
        UnifiedReportData对象
    """
    reader = ExcelDataReader(file_path)
    return reader.parse_all()

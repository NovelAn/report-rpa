"""
获取月度目标和YTD目标数据（简化版）
- 从数据库读取PFS/DTC的月度汇总目标和YTD累计目标
- 用pandas读取Excel的FF月度目标和YTD累计目标
- 合并两个DataFrame
"""

import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd

from .database import DatabaseReader

logger = logging.getLogger(__name__)


def _get_fy_start_date(current_year: int, current_month: int) -> date:
    """
    获取财年开始日期（财年从4月1日开始）

    Args:
        current_year: 当前年份
        current_month: 当前月份

    Returns:
        财年开始日期

    Examples:
        _get_fy_start_date(2025, 11) -> date(2025, 4, 1)
        _get_fy_start_date(2025, 2)  -> date(2024, 4, 1)  # 跨年
    """
    if current_month >= 4:
        # 4月及以后，财年开始于当年4月
        return date(current_year, 4, 1)
    else:
        # 1-3月，财年开始于去年4月
        return date(current_year - 1, 4, 1)


def get_monthly_targets(
    year: int,
    month: int,
    db_config: Union[int, str, Path, Dict[str, Any]] = 1,
    excel_path: Optional[str] = None
) -> pd.DataFrame:
    """
    获取月度目标数据（DataFrame格式）

    Args:
        year: 年份（如2025）
        month: 月份（1-12）
        db_config: 数据库配置
        excel_path: Excel文件路径（用于FF目标）

    Returns:
        月度目标DataFrame，包含以下渠道：
        - PFS, DTC（从数据库）
        - DTC_FF（从Excel）
        - DTC_EXCL_FF, TOTAL（计算得出）

    Example:
        df = get_monthly_targets(2025, 12, excel_path="data.xlsx")
        print(df[['channel', 'gmv', 'net']])
    """
    # 1. 从数据库读取月度汇总（PFS + DTC）
    df_db = _read_monthly_from_db(year, month, db_config)

    if df_db is None or df_db.empty:
        logger.warning(f"数据库中没有 {year}年{month}月 的数据")
        return None

    # 2. 从Excel读取FF月度目标
    df_ff = _read_ff_from_excel(year, month, excel_path)

    # 3. 合并并计算衍生指标
    df_final = _merge_and_calculate(df_db, df_ff)

    return df_final


def _read_monthly_from_db(
    year: int,
    month: int,
    db_config: Union[int, str, Path, Dict[str, Any]] = 1
) -> Optional[pd.DataFrame]:
    """从数据库读取月度汇总目标"""
    try:
        reader = DatabaseReader(db_config)

        if not reader.is_connected():
            logger.error("数据库连接失败")
            return None

        # 计算月份范围
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        # 执行月度汇总SQL
        params = (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        data = reader.execute_sql_file('monthly_target_summary', params)
        reader.close()

        if not data:
            return None

        # 转换为DataFrame
        df = pd.DataFrame(data)

        # 添加计算列
        df['source'] = 'database'

        logger.info(f"从数据库读取 {len(df)} 条月度汇总记录")
        return df

    except Exception as e:
        logger.error(f"从数据库读取失败: {e}")
        return None


def _read_ff_from_excel(
    year: int,
    month: int,
    excel_path: Optional[str]
) -> Optional[pd.DataFrame]:
    """从Excel/CSV读取FF月度目标"""
    if not excel_path:
        logger.info("未指定Excel，跳过FF目标")
        return None

    try:
        # 判断文件类型并读取
        if excel_path.endswith('.csv'):
            # 读取CSV文件
            df = pd.read_csv(excel_path)
        else:
            # 读取Excel文件
            excel_file = pd.ExcelFile(excel_path)

            # 查找包含FF目标的工作表
            sheet_name = None
            for name in excel_file.sheet_names:
                if '目标' in name or 'target' in name.lower():
                    sheet_name = name
                    break

            if not sheet_name:
                logger.info(f"Excel中未找到目标相关工作表，可用: {excel_file.sheet_names}")
                return None

            # 读取工作表
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

        # 查找FF数据（支持中英文列名）
        # 标准化列名映射
        column_map = {
            '年份': 'year',
            '月份': 'month',
            '渠道': 'channel',
            'year': 'year',
            'month': 'month',
            'channel': 'channel'
        }

        # 重命名列名为标准格式
        df_standardized = df.rename(columns=column_map)

        df_ff = df_standardized[
            (df_standardized['year'] == year) &
            (df_standardized['month'] == month) &
            (df_standardized['channel'].isin(['FF', 'DTC_FF']))
        ]

        if df_ff.empty:
            logger.info(f"文件中没有 {year}年{month}月 的FF目标")
            return None

        # 标准化列名（支持中英文列名）
        column_mapping = {}
        for col in df_ff.columns:
            if col == 'GMV目标' or col == 'gmv':
                column_mapping[col] = 'gmv'
            elif col == 'NET目标' or col == 'net':
                column_mapping[col] = 'net'
            elif col == 'UV目标' or col == 'uv':
                column_mapping[col] = 'uv'
            elif col == 'Buyers目标' or col == 'buyers':
                column_mapping[col] = 'buyers'
            elif col == 'GMV单位' or col == 'gmv_units':
                column_mapping[col] = 'gmv_units'
            elif col == 'NET单位' or col == 'net_units':
                column_mapping[col] = 'net_units'

        if column_mapping:
            df_ff = df_ff.rename(columns=column_mapping)

        # 添加渠道标识
        df_ff['channel'] = 'DTC_FF'
        df_ff['year'] = year
        df_ff['month'] = month
        df_ff['source'] = 'excel'

        # 只保留需要的列
        required_cols = ['year', 'month', 'channel', 'gmv', 'net']
        df_ff = df_ff[required_cols + [col for col in ['uv', 'buyers', 'gmv_units', 'net_units'] if col in df_ff.columns]]

        logger.info(f"从Excel读取FF目标: GMV={df_ff.iloc[0]['gmv']:,.0f}")
        return df_ff

    except FileNotFoundError:
        logger.warning(f"Excel文件不存在: {excel_path}")
        return None
    except Exception as e:
        logger.warning(f"读取Excel FF目标失败: {e}")
        return None


def _merge_and_calculate(
    df_db: pd.DataFrame,
    df_ff: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    合并数据库和Excel数据，并计算衍生指标

    Args:
        df_db: 数据库月度汇总（PFS, DTC）
        df_ff: Excel FF月度目标

    Returns:
        完整的月度目标DataFrame，包含：
        - PFS, DTC
        - DTC_FF (如果有)
        - DTC_EXCL_FF (计算得出)
        - TOTAL (计算得出)
    """
    # 1. 合并数据库和FF数据
    if df_ff is not None and not df_ff.empty:
        df_merged = pd.concat([df_db, df_ff], ignore_index=True)
    else:
        df_merged = df_db.copy()

    # 2. 计算DTC_EXCL_FF
    if 'DTC' in df_merged['channel'].values:
        dtc = df_merged[df_merged['channel'] == 'DTC'].iloc[0]

        dtc_excl_ff = {
            'year': dtc['year'],
            'month': dtc['month'],
            'channel': 'DTC_EXCL_FF',
            'gmv': dtc['gmv'] - (df_ff.iloc[0]['gmv'] if df_ff is not None else 0),
            'net': dtc['net'] - (df_ff.iloc[0]['net'] if df_ff is not None else 0),
            'net_units': dtc['net_units'],
            'gmv_units': dtc['gmv_units'],
            'uv': dtc['uv'] - (df_ff.iloc[0]['uv'] if df_ff is not None else 0),
            'buyers': dtc['buyers'],
            'free_traffic': dtc['free_traffic'],
            'paid_traffic': dtc['paid_traffic'],
            'days': dtc['days'],
            'source': 'calculated'
        }

        df_merged = pd.concat([df_merged, pd.DataFrame([dtc_excl_ff])], ignore_index=True)

    # 3. 计算TOTAL (PFS + DTC)
    if 'PFS' in df_merged['channel'].values and 'DTC' in df_merged['channel'].values:
        pfs = df_merged[df_merged['channel'] == 'PFS'].iloc[0]
        dtc = df_merged[df_merged['channel'] == 'DTC'].iloc[0]

        total = {
            'year': pfs['year'],
            'month': pfs['month'],
            'channel': 'TOTAL',
            'gmv': pfs['gmv'] + dtc['gmv'],
            'net': pfs['net'] + dtc['net'],
            'net_units': pfs['net_units'] + dtc['net_units'],
            'gmv_units': pfs['gmv_units'] + dtc['gmv_units'],
            'uv': pfs['uv'] + dtc['uv'],
            'buyers': pfs['buyers'] + dtc['buyers'],
            'free_traffic': pfs['free_traffic'] + dtc['free_traffic'],
            'paid_traffic': pfs['paid_traffic'] + dtc['paid_traffic'],
            'days': max(pfs['days'], dtc['days']),
            'source': 'calculated'
        }

        df_merged = pd.concat([df_merged, pd.DataFrame([total])], ignore_index=True)

    # 4. 排序
    df_merged = df_merged.sort_values(['channel'])

    logger.info(f"月度目标合并完成，渠道: {list(df_merged['channel'].values)}")
    return df_merged


# 便捷函数：转换为字典格式（兼容旧代码）
def get_monthly_targets_dict(
    year: int,
    month: int,
    db_config: Union[int, str, Path, Dict[str, Any]] = 1,
    excel_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    获取月度目标（字典格式）

    Returns:
        {
            'PFS': {'gmv': 1000000, 'net': 800000, ...},
            'DTC': {...},
            'DTC_FF': {...},
            'DTC_EXCL_FF': {...},
            'TOTAL': {...}
        }
    """
    df = get_monthly_targets(year, month, db_config, excel_path)

    if df is None:
        return {}

    # 转换为字典格式
    result = {}
    for _, row in df.iterrows():
        channel = row['channel']
        result[channel] = row.to_dict()

    return result


# ==================== YTD目标读取功能 ====================

def get_ytd_targets(
    year: int,
    month: int,
    db_config: Union[int, str, Path, Dict[str, Any]] = 1,
    excel_path: Optional[str] = None
) -> pd.DataFrame:
    """
    获取YTD（年初至今）累计目标数据（DataFrame格式）

    财年从4月开始，YTD = 从财年4月到指定月份的累计

    Args:
        year: 年份（如2025）
        month: 月份（1-12）
        db_config: 数据库配置
        excel_path: Excel文件路径（用于FF目标）

    Returns:
        YTD累计目标DataFrame，包含以下渠道：
        - PFS, DTC（从数据库）
        - DTC_FF（从Excel）
        - DTC_EXCL_FF, TOTAL（计算得出）

    Examples:
        # 2025年11月的YTD = 2025年4月到11月的累计
        df = get_ytd_targets(2025, 11, excel_path="data.xlsx")
        print(df[['channel', 'gmv', 'net']])

        # 2025年2月的YTD = 2024年4月到2025年2月的累计（跨年）
        df = get_ytd_targets(2025, 2, excel_path="data.xlsx")
    """
    # 1. 从数据库读取YTD累计（PFS + DTC）
    df_db = _read_ytd_from_db(year, month, db_config)

    if df_db is None or df_db.empty:
        logger.warning(f"数据库中没有 {year}年{month}月 的YTD数据")
        return None

    # 2. 从Excel读取FF的YTD累计目标
    df_ff = _read_ytd_ff_from_excel(year, month, excel_path)

    # 3. 合并并计算衍生指标
    df_final = _merge_and_calculate_ytd(df_db, df_ff)

    return df_final


def _read_ytd_from_db(
    year: int,
    month: int,
    db_config: Union[int, str, Path, Dict[str, Any]] = 1
) -> Optional[pd.DataFrame]:
    """
    从数据库读取YTD累计目标

    YTD = 从财年4月到指定月份的累计
    """
    try:
        reader = DatabaseReader(db_config)

        if not reader.is_connected():
            logger.error("数据库连接失败")
            return None

        # 计算YTD日期范围
        fy_start_date = _get_fy_start_date(year, month)

        import calendar
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)

        # 查询YTD数据（不GROUP BY，直接汇总所有数据）
        params = (
            fy_start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # 执行SQL - 需要一个能返回原始数据然后按channel聚合的查询
        # 这里我们直接构建SQL进行聚合
        sql = """
        SELECT
            %s as year,
            %s as month,
            channel,
            SUM(gmv) as gmv,
            SUM(net) as net,
            SUM(net_units) as net_units,
            SUM(gmv_units) as gmv_units,
            SUM(uv) as uv,
            SUM(buyers) as buyers,
            SUM(free_traffic) as free_traffic,
            SUM(paid_traffic) as paid_traffic,
            SUM(dtc_social_net) as dtc_social_net,
            SUM(dtc_social_gmv) as dtc_social_gmv,
            SUM(dtc_social_traffic) as dtc_social_traffic,
            SUM(dtc_organic_net) as dtc_organic_net,
            SUM(dtc_organic_gmv) as dtc_organic_gmv,
            SUM(dtc_organic_traffic) as dtc_organic_traffic,
            COUNT(DISTINCT Date) as days
        FROM dunhill_pfs_target
        WHERE Date BETWEEN %s AND %s
        GROUP BY channel
        ORDER BY channel;
        """

        # 参数：year, month, start_date, end_date
        query_params = (year, month) + params

        data = reader.execute_query(sql, query_params)
        reader.close()

        if not data:
            return None

        # 转换为DataFrame
        df = pd.DataFrame(data)

        # 添加计算列
        df['source'] = 'database'

        logger.info(f"从数据库读取YTD数据: {fy_start_date} 到 {end_date}，共 {len(df)} 条记录")
        return df

    except Exception as e:
        logger.error(f"从数据库读取YTD失败: {e}")
        return None


def _read_ytd_ff_from_excel(
    year: int,
    month: int,
    excel_path: Optional[str]
) -> Optional[pd.DataFrame]:
    """
    从Excel/CSV读取FF的YTD累计目标

    YTD = 从财年4月到指定月份的累计
    """
    if not excel_path:
        logger.info("未指定Excel，跳过FF目标")
        return None

    try:
        # 判断文件类型并读取
        if excel_path.endswith('.csv'):
            # 读取CSV文件
            df = pd.read_csv(excel_path)
        else:
            # 读取Excel文件
            excel_file = pd.ExcelFile(excel_path)

            # 查找包含FF目标的工作表
            sheet_name = None
            for name in excel_file.sheet_names:
                if '目标' in name or 'target' in name.lower():
                    sheet_name = name
                    break

            if not sheet_name:
                logger.info(f"Excel中未找到目标相关工作表")
                return None

            # 读取工作表
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

        # 确定YTD的月份范围
        fy_start_date = _get_fy_start_date(year, month)

        # 构建需要读取的月份列表
        months_to_sum = []
        current_year = fy_start_date.year
        current_month = fy_start_date.month

        # 从财年开始月到目标月的所有月份
        while True:
            if current_year == year and current_month > month:
                break

            months_to_sum.append((current_year, current_month))

            # 移动到下一个月
            if current_month == 12:
                current_year += 1
                current_month = 1
            else:
                current_month += 1

            # 如果已经超过目标年月，退出
            if current_year > year or (current_year == year and current_month > month):
                break

        # 筛选并累加FF数据（支持中英文列名）
        # 标准化列名映射
        column_map = {
            '年份': 'year',
            '月份': 'month',
            '渠道': 'channel',
            'year': 'year',
            'month': 'month',
            'channel': 'channel'
        }

        # 重命名列名为标准格式
        df_standardized = df.rename(columns=column_map)

        df_ff_list = []
        for yr, mth in months_to_sum:
            df_filtered = df_standardized[
                (df_standardized['year'] == yr) &
                (df_standardized['month'] == mth) &
                (df_standardized['channel'].isin(['FF', 'DTC_FF']))
            ]
            if not df_filtered.empty:
                df_ff_list.append(df_filtered)

        if not df_ff_list:
            logger.info(f"Excel中没有 {fy_start_date} 到 {year}年{month}月 的FF目标")
            return None

        # 合并所有月份的FF数据
        df_ff_all = pd.concat(df_ff_list, ignore_index=True)

        # 累加所有指标
        ff_summary = {
            'year': year,
            'month': month,
            'channel': 'DTC_FF',
            'gmv': df_ff_all['gmv'].sum(),
            'net': df_ff_all['net'].sum(),
            'net_units': df_ff_all.get('net_units', 0).sum(),
            'gmv_units': df_ff_all.get('gmv_units', 0).sum(),
            'uv': df_ff_all.get('uv', 0).sum(),
            'buyers': df_ff_all.get('buyers', 0).sum(),
            'free_traffic': 0,
            'paid_traffic': 0,
            'days': len(months_to_sum),  # 月份数
            'source': 'excel'
        }

        df_result = pd.DataFrame([ff_summary])

        logger.info(f"从Excel读取YTD FF目标: GMV={ff_summary['gmv']:,.0f}，共{len(months_to_sum)}个月")
        return df_result

    except FileNotFoundError:
        logger.warning(f"Excel文件不存在: {excel_path}")
        return None
    except Exception as e:
        logger.warning(f"读取Excel YTD FF目标失败: {e}")
        return None


def _merge_and_calculate_ytd(
    df_db: pd.DataFrame,
    df_ff: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    合并YTD数据库和Excel数据，并计算衍生指标

    Args:
        df_db: 数据库YTD累计（PFS, DTC）
        df_ff: Excel FF的YTD累计目标

    Returns:
        完整的YTD目标DataFrame
    """
    # 1. 合并数据库和FF数据
    if df_ff is not None and not df_ff.empty:
        df_merged = pd.concat([df_db, df_ff], ignore_index=True)
    else:
        df_merged = df_db.copy()

    # 2. 计算DTC_EXCL_FF (YTD)
    if 'DTC' in df_merged['channel'].values:
        dtc = df_merged[df_merged['channel'] == 'DTC'].iloc[0]

        dtc_excl_ff = {
            'year': dtc['year'],
            'month': dtc['month'],
            'channel': 'DTC_EXCL_FF',
            'gmv': dtc['gmv'] - (df_ff.iloc[0]['gmv'] if df_ff is not None else 0),
            'net': dtc['net'] - (df_ff.iloc[0]['net'] if df_ff is not None else 0),
            'net_units': dtc['net_units'] - (df_ff.iloc[0]['net_units'] if df_ff is not None and 'net_units' in df_ff.iloc[0] else 0),
            'gmv_units': dtc['gmv_units'] - (df_ff.iloc[0]['gmv_units'] if df_ff is not None and 'gmv_units' in df_ff.iloc[0] else 0),
            'uv': dtc['uv'] - (df_ff.iloc[0]['uv'] if df_ff is not None else 0),
            'buyers': dtc['buyers'] - (df_ff.iloc[0]['buyers'] if df_ff is not None and 'buyers' in df_ff.iloc[0] else 0),
            'free_traffic': dtc['free_traffic'],
            'paid_traffic': dtc['paid_traffic'],
            'days': dtc['days'],
            'source': 'calculated'
        }

        df_merged = pd.concat([df_merged, pd.DataFrame([dtc_excl_ff])], ignore_index=True)

    # 3. 计算TOTAL (YTD)
    if 'PFS' in df_merged['channel'].values and 'DTC' in df_merged['channel'].values:
        pfs = df_merged[df_merged['channel'] == 'PFS'].iloc[0]
        dtc = df_merged[df_merged['channel'] == 'DTC'].iloc[0]

        total = {
            'year': pfs['year'],
            'month': pfs['month'],
            'channel': 'TOTAL',
            'gmv': pfs['gmv'] + dtc['gmv'],
            'net': pfs['net'] + dtc['net'],
            'net_units': pfs['net_units'] + dtc['net_units'],
            'gmv_units': pfs['gmv_units'] + dtc['gmv_units'],
            'uv': pfs['uv'] + dtc['uv'],
            'buyers': pfs['buyers'] + dtc['buyers'],
            'free_traffic': pfs['free_traffic'] + dtc['free_traffic'],
            'paid_traffic': pfs['paid_traffic'] + dtc['paid_traffic'],
            'days': max(pfs['days'], dtc['days']),
            'source': 'calculated'
        }

        df_merged = pd.concat([df_merged, pd.DataFrame([total])], ignore_index=True)

    # 4. 排序
    df_merged = df_merged.sort_values(['channel'])

    logger.info(f"YTD目标合并完成，渠道: {list(df_merged['channel'].values)}")
    return df_merged


def get_ytd_targets_dict(
    year: int,
    month: int,
    db_config: Union[int, str, Path, Dict[str, Any]] = 1,
    excel_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    获取YTD目标（字典格式）

    Returns:
        {
            'PFS': {'gmv': 10000000, 'net': 8000000, ...},
            'DTC': {...},
            'DTC_FF': {...},
            'DTC_EXCL_FF': {...},
            'TOTAL': {...}
        }
    """
    df = get_ytd_targets(year, month, db_config, excel_path)

    if df is None:
        return {}

    # 转换为字典格式
    result = {}
    for _, row in df.iterrows():
        channel = row['channel']
        result[channel] = row.to_dict()

    return result

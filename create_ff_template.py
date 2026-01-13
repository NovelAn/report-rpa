"""
生成FF目标填报示例模板
使用CSV格式以避免依赖问题
"""

import pandas as pd
import os

def create_ff_target_template():
    """创建FF目标填报模板（CSV格式）"""

    # 定义2025财年（2025年4月-2026年3月）的月份列表
    fiscal_year_months = []

    # 2025年4月-12月
    for month in range(4, 13):
        fiscal_year_months.append((2025, month))

    # 2026年1月-3月
    for month in range(1, 4):
        fiscal_year_months.append((2026, month))

    # 示例数据结构
    template_data = []

    for year, month in fiscal_year_months:
        # 每个月创建一行FF目标数据
        template_data.append({
            '年份': year,
            '月份': month,
            '渠道': 'DTC_FF',
            'gmv': 0,  # 填写该月的GMV目标
            'net': 0,  # 填写该月的NET目标
            'gmv_units': 0,  # 可选
            'net_units': 0,  # 可选
            'uv': 0,   # 可选
            'buyers': 0,  # 可选
            'free_traffic': 0,  # 可选，记录该月有几场FF活动
            'paid_traffic': 0,  # 可选，记录该月有几场FF活动
            'days': 0,  # 可选，记录该月有几天FF活动
            'source': 'excel'  # 可选，记录活动名称等
        })

    # 创建DataFrame
    df = pd.DataFrame(template_data)

    # 确保目录存在
    output_dir = 'data/input'
    os.makedirs(output_dir, exist_ok=True)

    # 保存到CSV
    output_file = f'{output_dir}/FF目标填报模板_2025财年.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 创建说明文件
    instructions_file = f'{output_dir}/FF目标填报说明.txt'
    instructions_text = """
FF目标填报模板说明
================================================================================

文件：FF目标填报模板_2025财年.csv
格式：CSV（可用Excel打开编辑）

================================================================================
列填写说明
================================================================================

【年份】
  - 填写年份，如2025、2026

【月份】
  - 填写月份（1-12）
  - 财年范围：2025年4月 - 2026年3月

【渠道】
  - 必须填写 "DTC_FF" 或 "FF"
  - 两者皆可，系统会自动识别

【GMV目标】
  - 必填
  - 该月FF的GMV目标值（单位：元）
  - 无FF活动的月份填写0

【NET目标】
  - 必填
  - 该月FF的NET目标值（单位：元）
  - 无FF活动的月份填写0

【GMV单位】
  - 可选
  - 该月FF的GMV单位数（商品件数）

【NET单位】
  - 可选
  - 该月FF的NET单位数（有效订单件数）

【UV目标】
  - 可选
  - 该月FF的UV目标（用户数）

【Buyers目标】
  - 可选
  - 该月FF的Buyers目标（购买用户数）

【活动场次】
  - 可选
  - 记录该月有几场FF活动
  - 例如：BU26通常每月有2场

【备注】
  - 可选
  - 记录活动名称、日期等信息
  - 例如："BU26双11：11月10日和11月25日"

================================================================================
填写示例
================================================================================

示例1：有FF活动的月份
  年份,月份,渠道,gmv,net,gmv_units,net_units,uv,buyers,free_traffic,paid_traffic,days,source
  2025,11,DTC_FF,600000,480000,3000,2400,15000,750,2,2,2,BU26双11

示例2：无FF活动的月份
  年份,月份,渠道,gmv,net,gmv_units,net_units,uv,buyers,free_traffic,paid_traffic,days,source
  2025,5,DTC_FF,0,0,0,0,0,0,0,0,5月无FF活动

================================================================================
YTD累计说明
================================================================================

系统会自动计算YTD（年初至今）累计目标：
  - 财年开始：4月1日
  - YTD = 从4月到指定月份的累计
  - 例如：11月YTD = 4月+5月+...+11月

示例：
  - 4月FF: 300,000
  - 6月FF: 450,000
  - 11月FF: 600,000
  - 11月YTD = 300,000 + 450,000 + 600,000 = 1,350,000

================================================================================
使用步骤
================================================================================

1. 用Excel打开CSV文件
2. 填写每月的FF目标数据
3. 保存文件（可选择另存为Excel格式）
4. 如果保存为Excel，注意：
   - 工作表名称可以任意
   - 代码会自动查找包含FF数据的列

================================================================================
注意事项
================================================================================

1. 必须填写GMV目标和NET目标（无活动填0）
2. 渠道列必须是"DTC_FF"或"FF"
3. 年份和月份必须正确填写
4. 保存时使用UTF-8编码（Excel会自动处理）
5. 系统会自动读取并计算YTD累计

================================================================================
"""

    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions_text)

    print(f"✓ 模板已生成: {output_file}")
    print(f"✓ 说明文件已生成: {instructions_file}")
    print(f"\n模板包含:")
    print(f"  - 12行数据（2025年4月-2026年3月）")
    print(f"  - CSV格式，可用Excel打开编辑")
    print(f"\n财年范围: 2025年4月 - 2026年3月（共12个月）")
    print(f"\n使用方法:")
    print(f"  1. 用Excel打开CSV文件")
    print(f"  2. 填写每月的FF目标数据")
    print(f"  3. 保存文件（可另存为.xlsx格式）")
    print(f"  4. 代码将自动读取并计算YTD累计")


def create_ff_example_filled():
    """创建填写了示例数据的版本（供测试）"""

    # 示例数据
    example_data = [
        {
            '年份': 2025,
            '月份': 4,
            '渠道': 'DTC_FF',
            'GMV目标': 300000,
            'NET目标': 240000,
            'GMV单位': 1500,
            'NET单位': 1200,
            'UV目标': 8000,
            'Buyers目标': 400,
            '活动场次': 1,
            '备注': '4月春季内卖'
        },
        {
            '年份': 2025,
            '月份': 5,
            '渠道': 'DTC_FF',
            'GMV目标': 0,
            'NET目标': 0,
            'GMV单位': 0,
            'NET单位': 0,
            'UV目标': 0,
            'Buyers目标': 0,
            '活动场次': 0,
            '备注': '5月无FF活动'
        },
        {
            '年份': 2025,
            '月份': 6,
            '渠道': 'DTC_FF',
            'GMV目标': 450000,
            'NET目标': 360000,
            'GMV单位': 2250,
            'NET单位': 1800,
            'UV目标': 12000,
            'Buyers目标': 600,
            '活动场次': 1,
            '备注': '6月618内卖'
        },
        {
            '年份': 2025,
            '月份': 11,
            '渠道': 'FF',
            'GMV目标': 600000,
            'NET目标': 480000,
            'GMV单位': 3000,
            'NET单位': 2400,
            'UV目标': 15000,
            'Buyers目标': 750,
            '活动场次': 2,
            '备注': 'BU26双11：第一场11月10日，第二场11月25日'
        }
    ]

    df = pd.DataFrame(example_data)

    # 保存示例文件
    output_dir = 'data/input'
    os.makedirs(output_dir, exist_ok=True)
    output_file = f'{output_dir}/FF目标填报模板_示例已填写.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n✓ 示例文件已生成: {output_file}")
    print(f"  包含4个月份的示例数据：")
    print(f"    - 4月: 30万 GMV（春季内卖）")
    print(f"    - 5月: 0（无FF活动）")
    print(f"    - 6月: 45万 GMV（618内卖）")
    print(f"    - 11月: 60万 GMV（BU26双11，两场）")
    print(f"  11月的YTD累计 = 30万 + 45万 + 60万 = 135万")


def show_template_preview():
    """显示模板预览"""
    print("\n" + "="*80)
    print("模板预览（前5行）")
    print("="*80)

    # 预览数据
    preview_data = [
        {'年份': 2025, '月份': 4, '渠道': 'DTC_FF', 'gmv': 0, 'net': 0,
         'gmv_units': 0, 'net_units': 0, 'uv': 0, 'buyers': 0, 'free_traffic': 0, 'paid_traffic': 0, 'days': 0, 'source': ''},
        {'年份': 2025, '月份': 5, '渠道': 'DTC_FF', 'gmv': 0, 'net': 0,
         'gmv_units': 0, 'net_units': 0, 'uv': 0, 'buyers': 0, 'free_traffic': 0, 'paid_traffic': 0, 'days': 0, 'source': ''},
        {'年份': 2025, '月份': 6, '渠道': 'DTC_FF', 'gmv': 0, 'net': 0,
         'gmv_units': 0, 'net_units': 0, 'uv': 0, 'buyers': 0, 'free_traffic': 0, 'paid_traffic': 0, 'days': 0, 'source': ''},  
        {'年份': 2025, '月份': 7, '渠道': 'DTC_FF', 'GMV目标': 0, 'NET目标': 0,
         'GMV单位': 0, 'NET单位': 0, 'UV目标': 0, 'Buyers目标': 0, '活动场次': 0, '备注': ''},
        {'年份': 2025, '月份': 8, '渠道': 'DTC_FF', 'GMV目标': 0, 'NET目标': 0,
         'GMV单位': 0, 'NET单位': 0, 'UV目标': 0, 'Buyers目标': 0, '活动场次': 0, '备注': ''},
    ]

    df = pd.DataFrame(preview_data)
    print(df.to_string(index=False))

    print("\n" + "="*80)
    print("填写示例")
    print("="*80)

    example_data = [
        {'年份': 2025, '月份': 11, '渠道': 'DTC_FF', 'gmv': 600000, 'net': 480000,
         'gmv_units': 3000, 'net_units': 2400, 'uv': 15000, 'buyers': 750, 'free_traffic': 2,
         'paid_traffic': 2, 'days': 2, 'source': 'BU26双11'},
    ]

    df_example = pd.DataFrame(example_data)
    print(df_example.to_string(index=False))


if __name__ == '__main__':
    print("="*80)
    print("FF目标填报模板生成器")
    print("="*80)

    # 生成空模板
    create_ff_target_template()

    print("\n" + "="*80)

    # 生成示例已填写版本
    create_ff_example_filled()

    # 显示预览
    show_template_preview()

    print("\n" + "="*80)
    print("完成!")
    print("="*80)
    print("\n提示：")
    print("  - CSV文件可用Excel直接打开编辑")
    print("  - 编辑后可另存为Excel格式(.xlsx)")
    print("  - 代码会自动读取CSV或Excel格式")
    print("="*80)

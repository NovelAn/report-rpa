# 渠道剔除与Core Business核心业务指标功能说明

## 📋 功能概述

本功能实现了**灵活的渠道剔除机制**和**Core Business核心业务指标计算**,支持业务分析中的多维度数据对比。

### 业务场景

1. **FF (员工福利) 渠道剔除**
   - FF是内部员工促销渠道,折扣率高、价格低
   - 主要销售滞销、过季商品
   - 日常分析时需要剔除,以便反映正常业务表现

2. **SC (社群推广) 渠道剔除**
   - SC是买量承诺ROI的推广渠道
   - 与常规广告投放(不承诺ROI)性质不同
   - 分析核心业务能力时需要剔除

3. **Core Business 核心业务指标**
   - **定义**: `Core Business = PFS + DTC_EXCL_FF_SC`
   - **用途**: 反映剔除特殊渠道后的核心业务表现
   - **价值**: 更准确地评估业务真实增长和能力

---

## 🏗️ 架构设计

### 1. 数据模型层 ([data_schema.py](../src/models/data_schema.py))

#### 新增FF字段
```python
# DTC FF 渠道 (员工福利 - Friends & Family)
dtc_ff_net: Optional[float] = Field(default=None, description="DTC员工福利净销售")
dtc_ff_gmv: Optional[float] = Field(default=None, description="DTC员工福利GMV")
dtc_ff_rrc: Optional[float] = Field(default=None, description="DTC员工福利退款率")
dtc_ff_traffic: Optional[int] = Field(default=None, description="DTC员工福利流量")
```

#### 新增渠道类型
```python
class ChannelType(str, Enum):
    # 原有渠道
    PFS = "PFS"
    DTC = "DTC"
    TOTAL = "TOTAL"

    # 新增派生渠道
    DTC_EXCL_FF = "DTC_EXCL_FF"           # DTC剔除FF
    DTC_EXCL_FF_SC = "DTC_EXCL_FF_SC"     # DTC剔除FF和SC
    CORE_BUSINESS = "CORE_BUSINESS"       # 核心业务 = PFS + DTC_EXCL_FF_SC
```

### 2. 配置层 ([config.yaml](../config.yaml))

```yaml
processing:
  # 渠道剔除配置
  channel_exclusion:
    enabled: true

    dtc_exclusions:
      exclude_ff: false          # 剔除FF
      exclude_social: false      # 剔除SC
      exclude_ff_and_social: false  # 同时剔除FF和SC

    # 自动计算派生渠道指标
    calculate_derived_channels:
      - DTC_EXCL_FF
      - DTC_EXCL_FF_SC
      - CORE_BUSINESS
```

### 3. 计算层

#### 核心业务计算器 ([core_business_calculator.py](../src/transformation/core_business_calculator.py))
- `calculate_dtc_excl_ff()`: 计算DTC剔除FF后的指标
- `calculate_dtc_excl_ff_sc()`: 计算DTC剔除FF和SC后的指标
- `calculate_core_business()`: 计算Core Business指标
- `aggregate_monthly_with_exclusion()`: 支持渠道剔除的聚合方法

#### 数据聚合器 ([calculator.py](../src/transformation/calculator.py))
- `aggregate_monthly_with_exclusion()`: 新增方法,支持灵活的渠道剔除配置

#### 渠道汇总器 ([channel_aggregator.py](../src/transformation/channel_aggregator.py))
- `calculate_core_business()`: 计算Core Business指标

---

## 📊 使用方法

### 方法1: 基础用法

```python
from src.transformation.calculator import DataAggregator
from src.models.data_schema import ChannelType

# 创建聚合器
aggregator = DataAggregator(daily_metrics)

# 场景1: 不剔除 (默认)
dtc_full = aggregator.aggregate_monthly(2025, 12, ChannelType.DTC)
# DTC = Social + FF + Ad + Organic

# 场景2: 剔除FF (员工福利)
dtc_excl_ff = aggregator.aggregate_monthly_with_exclusion(
    year=2025,
    month=12,
    channel=ChannelType.DTC,
    exclude_ff=True,
    exclude_social=False
)
# DTC_EXCL_FF = DTC - FF

# 场景3: 剔除FF和SC (社群推广)
dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
    year=2025,
    month=12,
    channel=ChannelType.DTC,
    exclude_ff=True,
    exclude_social=True
)
# DTC_EXCL_FF_SC = DTC - FF - SC
```

### 方法2: 使用CoreBusinessCalculator

```python
from src.transformation.calculator import DataAggregator
from src.transformation.core_business_calculator import CoreBusinessCalculator
from src.models.data_schema import ChannelType

aggregator = DataAggregator(daily_metrics)
calc = CoreBusinessCalculator()

# 步骤1: 聚合PFS数据
pfs_metric = aggregator.aggregate_monthly(2025, 12, ChannelType.PFS)

# 步骤2: 聚合DTC并剔除FF和SC
dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
    2025, 12, ChannelType.DTC,
    exclude_ff=True,
    exclude_social=True
)

# 步骤3: 计算Core Business
core_business = calc.calculate_core_business(pfs_metric, dtc_excl_ff_sc)

# 输出结果
print(f"Core Business净销售: {core_business.net:,.2f}")
print(f"  - PFS: {pfs_metric.net:,.2f}")
print(f"  - DTC excl FF&SC: {dtc_excl_ff_sc.net:,.2f}")
```

### 方法3: 基于配置文件

```python
import yaml
from src.transformation.calculator import DataAggregator
from src.transformation.core_business_calculator import CoreBusinessCalculator

# 加载配置
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

exclusion = config['processing']['channel_exclusion']['dtc_exclusions']

# 创建计算器
calc = CoreBusinessCalculator(
    exclude_ff=exclusion['exclude_ff'],
    exclude_social=exclusion['exclude_social'],
    calculate_derived=True
)

# 使用配置进行聚合
dtc_metric = calc.aggregate_monthly_with_exclusion(
    daily_metrics=daily_metrics,
    year=2025,
    month=12,
    channel=ChannelType.DTC,
    exclusion_config={
        'exclude_ff': exclusion['exclude_ff'],
        'exclude_social': exclusion['exclude_social']
    }
)

# 自动计算所有派生渠道
all_metrics = calc.calculate_all_derived_channels([dtc_metric, pfs_metric])
```

---

## 📈 数据对比示例

假设2025年12月的数据:

| 指标 | TOTAL | DTC | DTC_EXCL_FF | DTC_EXCL_FF_SC | CORE_BUSINESS |
|------|-------|-----|-------------|---------------|---------------|
| NET销售 | 10,000,000 | 6,000,000 | 5,700,000 | 5,000,000 | 8,500,000 |
| YoY增长 | +15.2% | +18.5% | +19.3% | +21.2% | +16.8% |
| UV | 500,000 | 300,000 | 285,000 | 250,000 | 420,000 |
| CR (%) | 3.2 | 3.5 | 3.6 | 3.8 | 3.4 |
| AOV | 2,000 | 2,100 | 2,120 | 2,200 | 2,050 |

**分析洞察**:
1. FF渠道贡献: 300K (5% of DTC)
2. SC渠道贡献: 700K (11.7% of DTC)
3. 剔除FF&SC后,CR和AOV显著提升,反映核心业务质量更高
4. Core Business YoY +16.8%,体现真实业务增长

---

## 🔧 完整工作流示例

```python
# 完整工作流: 从Excel读取到Core Business计算
import yaml
from src.ingestion.excel_reader import ExcelDataReader
from src.transformation.calculator import DataAggregator
from src.transformation.core_business_calculator import CoreBusinessCalculator
from src.models.data_schema import ChannelType

# 1. 加载配置
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 2. 读取Excel数据
reader = ExcelDataReader("MBR数据模板.xlsx")
unified_data = reader.parse_all()
daily_metrics = unified_data.target_metrics

# 3. 创建聚合器
aggregator = DataAggregator(daily_metrics)
calc = CoreBusinessCalculator(
    exclude_ff=config['processing']['channel_exclusion']['dtc_exclusions']['exclude_ff'],
    exclude_social=config['processing']['channel_exclusion']['dtc_exclusions']['exclude_social'],
    calculate_derived=True
)

# 4. 聚合各渠道数据
pfs = aggregator.aggregate_monthly(2025, 12, ChannelType.PFS)
dtc = aggregator.aggregate_monthly(2025, 12, ChannelType.DTC)
dtc_excl_ff = aggregator.aggregate_monthly_with_exclusion(
    2025, 12, ChannelType.DTC,
    exclude_ff=True,
    exclude_social=False
)
dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
    2025, 12, ChannelType.DTC,
    exclude_ff=True,
    exclude_social=True
)

# 5. 计算Core Business
core_business = calc.calculate_core_business(pfs, dtc_excl_ff_sc)

# 6. 输出报告
print(f"\nPFS: {pfs.net:>15,.2f}")
print(f"DTC (完整): {dtc.net:>15,.2f}")
print(f"DTC excl FF: {dtc_excl_ff.net:>15,.2f}")
print(f"DTC excl FF&SC: {dtc_excl_ff_sc.net:>15,.2f}")
print(f"CORE BUSINESS: {core_business.net:>15,.2f}")

# 7. 自动计算所有派生渠道
monthly_metrics = [pfs, dtc, dtc_excl_ff, dtc_excl_ff_sc, core_business]
all_metrics = calc.calculate_all_derived_channels(monthly_metrics)
```

---

## 📁 相关文件

| 文件 | 说明 |
|------|------|
| [src/models/data_schema.py](../src/models/data_schema.py) | 数据模型定义 (FF字段、渠道类型枚举) |
| [src/transformation/core_business_calculator.py](../src/transformation/core_business_calculator.py) | 核心业务计算器 |
| [src/transformation/calculator.py](../src/transformation/calculator.py) | 数据聚合器 (支持渠道剔除) |
| [src/transformation/channel_aggregator.py](../src/transformation/channel_aggregator.py) | 渠道汇总器 |
| [config.yaml](../config.yaml) | 配置文件 (渠道剔除配置) |
| [examples/core_business_usage.py](../examples/core_business_usage.py) | 使用示例代码 |

---

## ✅ 功能清单

- [x] 在数据模型中添加FF相关字段
- [x] 扩展ChannelType枚举,添加派生渠道类型
- [x] 在配置文件中添加渠道剔除配置
- [x] 创建CoreBusinessCalculator核心业务计算器
- [x] 更新DataAggregator支持渠道剔除
- [x] 更新ChannelAggregator支持Core Business计算
- [x] 提供完整的使用示例和文档

---

## 🚀 后续扩展

1. **UI集成**: 在Web界面中添加渠道剔除选项
2. **报告生成**: 在PPT报告中自动包含Core Business指标
3. **AI洞察**: 让AI分析Core Business vs TOTAL的差异
4. **历史对比**: 支持Core Business的历史趋势分析

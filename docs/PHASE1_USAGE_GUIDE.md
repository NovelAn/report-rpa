# MBR自动化系统 - 使用指南

## 📋 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [系统运行](#系统运行)
4. [数据源配置](#数据源配置)
5. [功能说明](#功能说明)
6. [测试验证](#测试验证)
7. [常见问题](#常见问题)

---

## 系统概述

MBR自动化系统是一个将手动制作月报流程转换为AI驱动的半自动化系统的Python项目。

### 核心功能

✅ **数据读取**: 支持Excel、CSV、数据库等多源数据读取
✅ **业务计算**: 实现20个核心业务指标计算 (GMV、NET、UV、CR、AOV等)
✅ **渠道剔除**: 灵活的FF(员工福利)和SC(社群推广)渠道剔除
✅ **Core Business**: 核心业务指标计算 (PFS + DTC_EXCL_FF_SC)
✅ **数据验证**: 完整性检查和质量评分

### 技术栈

- Python 3.11+
- Pandas (数据处理)
- Pydantic (数据验证)
- openpyxl (Excel读取)

---

## 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd mbr-rpa

# 安装依赖
pip install -r requirements.txt
```

### 2. 测试系统功能

**使用模拟数据快速测试** (推荐先运行):

```bash
python test_phase1.py --mock
```

这将运行所有Phase 1功能的测试,包括:
- ✅ 数据聚合
- ✅ 渠道剔除 (FF、SC)
- ✅ Core Business计算
- ✅ YoY/MoM增长率计算
- ✅ 数据验证

**预期输出**:
```
================================================================================
MBR自动化系统 - Phase 1 功能测试
================================================================================
创建 31 天的模拟数据...
✓ 创建了 62 条日度数据

================================================================================
测试1: 数据聚合功能
================================================================================

✓ DTC月度聚合:
  GMV:             6,265,000.00
  NET:             5,638,500.00
  UV:                  160,495
  ...
```

### 3. 运行完整处理流程

使用实际Excel数据:

```bash
# 方式1: 使用默认配置
python main.py --input data/input/MBR数据模板.xlsx

# 方式2: 指定报告期间
python main.py --input data/input/MBR数据模板.xlsx --period 2025-12

# 方式3: 使用自定义配置
python main.py --config config.yaml --input data/input/MBR数据模板.xlsx
```

---

## 系统运行

### 主入口文件: `main.py`

**功能**:
- 数据读取
- 数据聚合
- 渠道汇总
- Core Business计算
- 数据验证
- 报告摘要生成

**运行示例**:

```bash
# 基本用法
python main.py --input your_data.xlsx

# 指定期间
python main.py --input your_data.xlsx --period 2025-12

# 查看帮助
python main.py --help
```

### 处理流程

```
Step 1: 数据读取
  ↓ 读取Excel文件,解析所有工作表

Step 2: 数据聚合
  ↓ 将日度数据聚合为月度数据

Step 3: 渠道汇总
  ↓ 计算渠道层级关系 (TOTAL, DTC)

Step 4: Core Business计算
  ↓ 计算核心业务指标

Step 5: 数据验证
  ↓ 验证数据完整性和质量

Step 6: 生成报告摘要
  ↓ 输出处理结果和统计信息

✓ 完成!
```

---

## 数据源配置

### Excel数据源

**文件位置**: `data/input/MBR数据模板.xlsx`

**必需工作表**:
- `目标表`: 日度KPI数据

**可选工作表**:
- `Campaign`: 活动数据
- `一级流量源`: 流量源数据
- `二级流量源`: 流量源数据
- `三级流量源`: 流量源数据
- 等等...

**Excel数据格式** (目标表示例):

| Date | channel | gmv | net | uv | buyers | orders | dtc_social_net | dtc_ff_net | dtc_ad_net | dtc_organic_net |
|------|---------|-----|-----|-----|--------|--------|----------------|------------|------------|-----------------|
| 2025-12-01 | DTC | 200000 | 180000 | 5000 | 175 | 180 | 15000 | 8000 | 25000 | 132000 |
| 2025-12-02 | DTC | 201000 | 180900 | 5050 | 176 | 181 | 15100 | 8050 | 25150 | 132600 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**重要字段说明**:

| 字段 | 说明 | 是否必需 |
|------|------|----------|
| Date | 日期 | ✅ 必需 |
| channel | 渠道 (PFS/DTC/TOTAL) | ✅ 必需 |
| gmv | 商品交易总额 | ✅ 必需 |
| net | 净销售额 | ✅ 必需 |
| uv | 访客数 | ✅ 必需 |
| buyers | 购买人数 | ✅ 必需 |
| dtc_social_net | 社群推广净销售 | ⚠️ 剔除功能需要 |
| dtc_ff_net | 员工福利净销售 | ⚠️ 剔除功能需要 |
| dtc_ad_net | 广告推广净销售 | 可选 |
| dtc_organic_net | 自然渠道净销售 | 可选 |

### 数据库配置 (可选)

如需使用数据库,在 `.env` 文件中配置:

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/mbr_db
```

### 配置文件: `config.yaml`

```yaml
# 数据源配置
data_sources:
  excel:
    default_path: "data/input/"
    supported_formats: [".xlsx", ".xls"]

# 数据处理配置
processing:
  # 渠道剔除配置
  channel_exclusion:
    enabled: true
    dtc_exclusions:
      exclude_ff: false          # 是否剔除FF
      exclude_social: false      # 是否剔除SC
      exclude_ff_and_social: false  # 是否同时剔除

    # 自动计算派生渠道
    calculate_derived_channels:
      - DTC_EXCL_FF
      - DTC_EXCL_FF_SC
      - CORE_BUSINESS
```

---

## 功能说明

### 1. 渠道剔除功能

**业务场景**:
- **FF (员工福利)**: 内部员工促销,折扣率高,销售滞销商品
- **SC (社群推广)**: 买量承诺ROI渠道,与常规广告投放不同

**使用方式**:

```python
from src.transformation.calculator import DataAggregator
from src.models.data_schema import ChannelType

aggregator = DataAggregator(daily_metrics)

# 剔除FF
dtc_excl_ff = aggregator.aggregate_monthly_with_exclusion(
    2025, 12, ChannelType.DTC,
    exclude_ff=True,
    exclude_social=False
)

# 剔除FF和SC
dtc_excl_ff_sc = aggregator.aggregate_monthly_with_exclusion(
    2025, 12, ChannelType.DTC,
    exclude_ff=True,
    exclude_social=True
)
```

### 2. Core Business计算

**定义**: `Core Business = PFS + DTC_EXCL_FF_SC`

**使用方式**:

```python
from src.transformation.channel_aggregator import ChannelAggregator

# 计算Core Business
core_business = ChannelAggregator.calculate_core_business(
    pfs_metric,
    dtc_excl_ff_sc_metric
)
```

### 3. 渠道层级结构

```
TOTAL (全渠道)
├── PFS (平台渠道: 天猫/京东)
└── DTC (直营渠道)
    ├── Social (社群推广) ← 可剔除
    ├── FF (员工福利) ← 可剔除
    ├── Ad (广告投放)
    └── Organic (自然流量)

派生渠道:
- DTC_EXCL_FF = DTC - FF
- DTC_EXCL_FF_SC = DTC - FF - Social
- CORE_BUSINESS = PFS + DTC_EXCL_FF_SC
```

---

## 测试验证

### 运行测试

```bash
# 测试所有功能 (使用模拟数据)
python test_phase1.py --mock

# 测试特定功能
python test_phase1.py --test aggregation
python test_phase1.py --test exclusion
python test_phase1.py --test core_business
```

### 测试输出示例

```
渠道剔除对比 (2025-12):
渠道                          NET              GMV             UV
──────────────────────────────────────────────────────────────────
DTC (完整)              5,638,500.00     6,265,000.00        160,495
DTC excl FF             5,410,500.00     6,011,700.00        160,195
DTC excl FF&SC          4,875,500.00     5,417,100.00        159,795
──────────────────────────────────────────────────────────────────
FF贡献                    228,000.00      253,300.00            300
SC贡献                    535,000.00      594,600.00            400
```

---

## 常见问题

### Q1: 如何准备Excel数据文件?

**A**: 确保Excel文件包含:
1. **必需列**: Date, channel, gmv, net, uv, buyers
2. **渠道剔除列** (可选): dtc_ff_net, dtc_social_net等
3. **日期格式**: YYYY-MM-DD
4. **渠道标识**: PFS, DTC, TOTAL

### Q2: 数据文件应该放在哪里?

**A**:
```
mbr-rpa/
├── data/
│   └── input/
│       └── MBR数据模板.xlsx  ← 放在这里
├── main.py
└── config.yaml
```

### Q3: 如何配置渠道剔除?

**A**: 修改 `config.yaml`:

```yaml
processing:
  channel_exclusion:
    enabled: true
    dtc_exclusions:
      exclude_ff: true      # 改为true启用
      exclude_social: true  # 改为true启用
```

### Q4: 系统支持哪些Excel格式?

**A**: 支持 `.xlsx` 和 `.xls` 格式

### Q5: 如何查看详细的处理日志?

**A**:
```bash
# 日志文件位置
outputs/logs/app.log

# 实时查看
tail -f outputs/logs/app.log
```

### Q6: 内存不足怎么办?

**A**:
1. 减少数据量或分批处理
2. 修改 `config.yaml` 中的配置
3. 增加系统内存

### Q7: 测试失败怎么办?

**A**:
```bash
# 1. 确认依赖已安装
pip install -r requirements.txt

# 2. 使用模拟数据测试
python test_phase1.py --mock

# 3. 查看详细错误
python test_phase1.py --mock 2>&1 | tee test.log
```

---

## 下一步

### Phase 2: AI洞察生成 (计划中)
- [ ] 集成Claude API
- [ ] 自动生成业务洞察
- [ ] 智能建议推荐

### Phase 3: PPT自动生成 (计划中)
- [ ] PowerPoint模板系统
- [ ] 自动填充数据
- [ ] 品牌一致性保持

### Phase 4: Claude Skill集成 (计划中)
- [ ] 命令行工具
- [ ] 交互式分析

---

## 相关文档

- [Core Business功能说明](CORE_BUSINESS_FEATURE.md)
- [API文档](API_REFERENCE.md) (待完善)
- [示例代码](../examples/)

---

## 联系支持

如遇问题,请查看:
1. 本文档的[常见问题](#常见问题)部分
2. [test_phase1.py](../test_phase1.py) 示例代码
3. `outputs/logs/app.log` 日志文件

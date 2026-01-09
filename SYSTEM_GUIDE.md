# MBR月报自动化系统 - 核心业务说明

> **版本**: v1.0
> **更新日期**: 2025-01-09
> **状态**: ✅ Phase 1 核心功能已完成

---

## 📊 一、核心业务指标 (20个)

### 1.1 指标分类

```
业务指标
├── 销售指标 (8个)
│   ├── GMV (Gross Merchandise Value) - 商品销售总额
│   ├── NET Sales - 净销售额
│   ├── Buyers - 购买人数
│   ├── Orders - 订单数
│   └── GMV Units - 销售件数
│   ├── AOV (Average Order Value) - 平均订单金额
│   ├── ATV (Average Transaction Value) - 人均消费
│   └── AUR (Average Unit Retail) - 件单价
│
├── 流量指标 (1个)
│   ├── UV (Unique Visitors) - 访客数
│
├── 转化指标 (3个)
│   ├── CR (Conversion Rate) - 转化率
│   ├── UPT (Units Per Transaction) - 连带率
│   └── 复购率 - Orders / Buyers
│
└── 退款指标 (4个)
    ├── Cancel Amount - 取消金额
    ├── Return Amount - 退货金额
    ├── RRC (Refund Rate) - 总退款率
    └── RRC After Cancel - 扣除取消后的退货率
```

### 1.2 计算公式

#### 销售指标

| 指标 | 公式                      | 说明           |
| ---- | ------------------------- | -------------- |
| GMV  | Σ(所有订单金额)          | 商品销售总额   |
| NET  | GMV - 取消金额 - 退货金额 | 净销售额       |
| AOV  | GMV / Orders              | 平均每订单金额 |
| ATV  | GMV / Buyers              | 平均每人消费   |
| AUR  | GMV / GMV Units           | 平均每件价格   |

**关键关系**: ATV ≥ AOV ≥ AUR

#### 流量与转化

| 指标   | 公式                  | 说明          |
| ------ | --------------------- | ------------- |
| CR     | (Buyers / UV) × 100% | 转化率        |
| UPT    | GMV Units / Orders    | 连带率        |
| 复购率 | Orders / Buyers       | 订单数/买家数 |

#### 退款指标

| 指标             | 公式                                  | 说明               |
| ---------------- | ------------------------------------- | ------------------ |
| Cancel Rate      | (取消金额 / GMV) × 100%              | 取消率             |
| Return Rate      | (退货金额 / GMV) × 100%              | 退货率             |
| RRC              | Cancel Rate + Return Rate             | 总退款率           |
| RRC After Cancel | (退货金额 / (GMV - 取消金额)) × 100% | 扣除取消后的退货率 |

#### 衍生关系

```
AOV = AUR × UPT                      # 平均订单 = 件单价 × 连带率
ATV = AOV × 复购率                   # 人均消费 = 平均订单 × 复购率
ATV = AUR × UPT × 复购率             # 人均消费 = 件单价 × 连带率 × 复购率
```

### 1.3 业务含义

| 指标          | 业务含义 | 监控重点           |
| ------------- | -------- | ------------------ |
| **GMV** | 销售总额 | 整体业绩           |
| **NET** | 实际收入 | 盈利能力           |
| **AOV** | 订单质量 | 连带销售效果       |
| **ATV** | 客户价值 | 复购和忠诚度       |
| **AUR** | 商品定价 | 产品结构和定价策略 |
| **CR**  | 流量效率 | 转化能力           |
| **RRC** | 退款情况 | 产品和服务质量     |

---

## 🏢 二、渠道层级体系

### 2.1 渠道结构

```
TOTAL (全渠道)
├── PFS (平台渠道) - 96.9%
│   ├── TMALL (天猫)
│   ├── JD (京东)
│   └── 其他第三方平台
│
└── DTC (直营渠道) - 3.1%
    ├── WBTQ (微信小程序) - 74.1% of DTC
    └── OFS (线下门店+官网) - 25.9% of DTC
        │
        └── DTC销售来源:
            ├── Social (社群推广) - 40%
            ├── Ad (广告推广) - 2.5%
            ├── FF (内卖) - 10%
            └── Organic (自然流量) - 47.5%
```

### 2.2 汇总公式

```python
✅ TOTAL = PFS + DTC
✅ DTC = WBTQ + OFS
✅ DTC净销售 = Social净销售 + Ad净销售 + FF净销售 + Organic净销售
✅ DTC流量 = Social流量 + Ad流量 + Organic流量
```

### 2.3 DTC销售来源详解

| 来源              | 占比  | 特点                 | 转化率           |
| ----------------- | ----- | -------------------- | ---------------- |
| **Social**  | 40%   | 主动营销，短期见效快 | 2000元/UV (最高) |
| **Ad**      | 2.5%  | 品牌曝光，转化较难   | 500元/UV (最低)  |
| **FF**      | 10%   | 员工福利，特殊渠道   | -                |
| **Organic** | 47.5% | 品牌认知，长期价值   | 1900元/UV (较高) |

### 2.4 广告推广特别说明

**广告类型**:

- 朋友圈广告
- Banner广告 (Bidding Banner)
- 小红书广告
- KOL/KOC付费推广

**关键指标**:

```
广告ROI = (广告收入 - 广告花费) / 广告花费 × 100%
广告转化率 = 广告GMV / 广告流量 × 100%
```

**业务理解**:

- 短期ROI可能为负 (如-37.5%)
- 但广告主要作用是品牌曝光和引流
- 需要看长期品牌价值和用户获取成本

---

## 📅 三、财年计算规则

### 3.1 财年定义

```
财年 cutoff = 4月1日

规则: 4月1日触发新财年

示例:
- 2025-01-01 → FY25
- 2025-03-31 → FY25
- 2025-04-01 → FY26 ⭐
- 2025-12-31 → FY26
```

### 3.2 YTD计算

```
FY25 YTD through Dec 2024:
  = 2024年4-12月累计
  = Apr + May + Jun + ... + Dec

FY26 YTD through Jun 2025:
  = 2025年4-6月累计
  = Apr + May + Jun
```

### 3.3 实现代码

**文件**: [src/utils/fiscal_year.py](src/utils/fiscal_year.py)

```python
def get_fiscal_year(date: datetime) -> int:
    """根据日期获取财年，4月1日触发新财年"""
    year = date.year
    if date.month >= 4:
        return year + 1
    return year
```

---

## 🔧 四、核心代码实现

### 4.1 数据模型

**文件**: [src/models/data_schema.py](src/models/data_schema.py)

```python
# 日度KPI数据
class TargetMetric:
    - 日期、渠道
    - GMV, NET, UV, Buyers, Orders
    - AOV, ATV, AUR
    - CR, UPT
    - 退款相关字段
    - DTC销售来源字段 (Social, Ad, Organic)

# 月度汇总数据
class MonthlyMetrics:
    - 年月、渠道
    - 所有日度指标的月度聚合
    - YoY, MoM增长率
```

### 4.2 计算器

**文件**: [src/transformation/calculator.py](src/transformation/calculator.py)

```python
class MetricCalculator:
    # 核心指标计算
    - calculate_aov(gmv, orders)
    - calculate_atv(gmv, buyers)
    - calculate_aur(gmv, gmv_units)
    - calculate_cr(buyers, uv)
    - calculate_rrc(...)

    # 聚合计算
    - aggregate_monthly(daily_metrics)
    - calculate_ytd(monthly_metrics)
```

### 4.3 渠道汇总器

**文件**: [src/transformation/channel_aggregator.py](src/transformation/channel_aggregator.py)

```python
class ChannelAggregator:
    # 渠道汇总
    - calculate_dtc_channel(wbtq, ofs)
    - calculate_total_channel(pfs, dtc)
    - validate_channel_hierarchy(metrics)
```

---

## 📐 五、数据验证规则

### 5.1 字段验证

```python
# 百分比字段 (0-100%)
✓ CR, RRC, Cancel Rate, Return Rate

# 非负数
✓ AOV, ATV, AUR, GMV, NET

# 业务逻辑
✓ Buyers ≤ UV
✓ Orders ≥ Buyers (有复购时)
```

### 5.2 渠道验证

```python
✓ TOTAL.net = PFS.net + DTC.net
✓ DTC.net = WBTQ.net + OFS.net
✓ PFS占比通常 > 95%
✓ DTC占比通常 < 5%
```

### 5.3 指标关系验证

```python
✓ ATV ≥ AOV ≥ AUR
✓ AOV = AUR × UPT
✓ ATV = AOV × 复购率
✓ RRC = Cancel Rate + Return Rate
```

---

## 🎯 六、常见问题速查

### Q1: AOV和ATV的区别？

```
AOV = GMV / Orders      # 平均每个订单多少钱
ATV = GMV / Buyers      # 平均每个买家花多少钱

关系: ATV ≥ AOV (因为一个买家可能下多个订单)
```

### Q2: 如何计算财年？

```
规则: 4月1日触发新财年

2025-01-01 → FY25
2025-04-01 → FY26  ⭐ 4月1日开始新财年
```

### Q3: DTC包含哪些渠道？

```
DTC = WBTQ (微信小程序) + OFS (线下门店+官网)

DTC销售来源:
  - Social (社群推广)
  - Ad (广告推广)
  - FF (内卖)
  - Organic (自然流量)
```

### Q4: RRC如何计算？

```
RRC = Cancel Rate + Return Rate

Cancel Rate = 取消金额 / GMV × 100%
Return Rate = 退货金额 / GMV × 100%
```

### Q5: 广告ROI为负是否正常？

```
对于奢侈品(如dunhill)，短期ROI可能为负是正常的。

因为广告主要作用是:
1. 品牌曝光和市场教育
2. 引流，为后续转化做铺垫
3. 维持品牌在消费者心智中的存在感

需要看长期品牌价值，而非短期ROI。
```

---

## 📁 七、文件结构

```
src/
├── models/
│   └── data_schema.py              # 数据模型定义
├── transformation/
│   ├── calculator.py               # 指标计算器
│   └── channel_aggregator.py       # 渠道汇总器
└── utils/
    └── fiscal_year.py              # 财年工具函数
```

---

## 📝 八、更新日志

### 2025-01-09 - v1.0

- ✅ 完成核心业务指标定义 (20个指标)
- ✅ 完成渠道层级体系定义
- ✅ 完成财年计算逻辑
- ✅ 新增AUR件单价指标
- ✅ 新增广告推广渠道
- ✅ 修正AOV/ATV计算逻辑
- ✅ 细化RRC退款率计算

---

**最后更新**: 2025-01-09
**维护者**: Claude Code
**状态**: ✅ 生产就绪

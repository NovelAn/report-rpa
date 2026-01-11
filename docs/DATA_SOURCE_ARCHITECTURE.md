# MBR数据源架构优化方案

## 📋 当前问题

现有架构中，所有数据都从Excel文件读取，但实际上：
1. **部分工作表是Power Query + SQL查询的结果** - 可以直接用SQL
2. **部分工作表是计算得出的Metrics** - 不需要存储，可以直接计算
3. **部分工作表是报告呈现层** - 基于基础数据汇总生成

## 🎯 优化方案

### 数据分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                     报告呈现层                               │
│  (Campaign, SalesOverview, dunhill_traffic_pivot, PFS流量)  │
│  ↓ 通过计算生成，不从存储读取                                │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│                     数据源层                                 │
│  ├─ 目标表 (MySQL查询)                                       │
│  ├─ 全店核心数据_bymonth (MySQL查询)                          │
│  ├─ 一级流量源 (MySQL查询)                                    │
│  ├─ 二级流量源 (MySQL查询)                                    │
│  └─ 三级流量源 (MySQL查询)                                    │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│                     数据库层                                 │
│              MySQL Database                                  │
└─────────────────────────────────────────────────────────────┘
```

### 工作表分类

#### 1. 可直接SQL查询的工作表 ✅ 推荐使用数据库查询

| 工作表名 | 数据源类型 | SQL复杂度 | 说明 |
|---------|-----------|----------|------|
| **目标表** | 原始交易数据 | 中等 | 日度KPI数据，核心数据源 |
| **全店核心数据_bymonth** | 月度聚合数据 | 简单 | 可以基于目标表聚合或直接查询月度表 |
| **一级流量源** | 流量数据 | 简单 | 按一级来源分组的流量 |
| **二级流量源** | 流量数据 | 简单 | 按二级来源分组的流量 |
| **三级流量源** | 流量数据 | 简单 | 按三级来源分组的流量 |

**优势**：
- ✅ 实时数据
- ✅ 可追溯数据历史
- ✅ 减少Excel文件大小
- ✅ 提高查询效率

#### 2. 不需要的工作表 ❌ 月度报告不需要

| 工作表名 | 原因 |
|---------|------|
| **fans&member** | 月度报告不需要会员详细数据 |
| **会员源** | 月度报告不需要会员来源详细数据 |
| **粉丝源** | 月度报告不需要粉丝来源详细数据 |

#### 3. 可计算生成的工作表 🔄 建议通过代码计算

| 工作表名 | 数据来源 | 计算逻辑 |
|---------|---------|----------|
| **Campaign** | 基于目标表 | 提取活动期间的日期范围数据 |
| **SalesOverview** | 基于目标表聚合 | 计算销售总览和关键指标 |
| **dunhill_traffic_pivot** | 基于流量源数据 | 创建数据透视表 |
| **PFS_流量呈现** | 基于流量源数据 | PFS渠道流量汇总 |

## 🏗️ 实施方案

### 方案A: 纯数据库模式 (推荐用于生产环境)

```
配置文件 (config.yaml)
  ↓
数据库连接池
  ↓
SQL查询模块
  ├─ queries/
  │   ├─ target_metrics.sql
  │   ├─ monthly_summary.sql
  │   ├─ traffic_source_l1.sql
  │   ├─ traffic_source_l2.sql
  │   └─ traffic_source_l3.sql
  ↓
数据处理引擎
  ├─ 聚合计算
  ├─ 指标计算
  └─ 渠道剔除
  ↓
报告生成
  ├─ Campaign汇总
  ├─ SalesOverview
  └─ PFS流量呈现
```

### 方案B: 混合模式 (当前过渡期)

```
数据摄入层
  ├─ 数据库查询 (优先)
  │   ├─ 目标表
  │   ├─ 全店核心数据
  │   └─ 流量源 (L1/L2/L3)
  └─ Excel回退 (fallback)
      ├─ Campaign
      ├─ SalesOverview
      └─ 其他计算结果
```

## 📝 实施步骤

### Phase 1.1: 数据库连接模块

创建 `src/ingestion/database/` 模块：
- `db_connection.py` - 数据库连接管理
- `query_builder.py` - SQL查询构建器
- `db_reader.py` - 数据库读取器

### Phase 1.2: SQL查询定义

创建 `src/ingestion/database/queries/` 目录：
- `target_metrics.sql` - 目标表查询
- `monthly_summary.sql` - 月度汇总查询
- `traffic_sources.sql` - 流量源查询

### Phase 1.3: 数据源配置

更新 `config.yaml`：
```yaml
data_sources:
  # 数据库配置
  database:
    enabled: true
    host: localhost
    port: 3306
    database: mbr_db
    user: readonly_user
    password: ${DB_PASSWORD}

  # 工作表数据源映射
  sheets_config:
    # 优先使用数据库查询
    target_table:
      source: database
      table: daily_kpi_metrics
      query: queries/target_metrics.sql

    monthly_summary:
      source: database
      table: monthly_summary
      query: queries/monthly_summary.sql

    # 使用Excel (计算结果或回退)
    campaign:
      source: calculated
      base_tables: [target_table]
      calculation: aggregate_by_campaign

    sales_overview:
      source: calculated
      base_tables: [target_table, monthly_summary]
      calculation: aggregate_overview
```

### Phase 1.4: 更新数据读取器

修改 `ExcelDataReader` → `DataReader`：
- 支持数据库优先读取
- 支持Excel回退
- 支持计算生成

## 💻 代码结构

### 1. 数据库模块

```
src/ingestion/database/
├── __init__.py
├── db_connection.py      # 数据库连接池
├── query_builder.py       # SQL查询构建
├── db_reader.py          # 数据库读取器
└── queries/              # SQL查询文件
    ├── target_metrics.sql
    ├── monthly_summary.sql
    ├── traffic_l1.sql
    ├── traffic_l2.sql
    └── traffic_l3.sql
```

### 2. 配置文件

```
config/
├── database.yaml         # 数据库配置
├── queries.yaml          # 查询配置
└── sources.yaml          # 数据源映射
```

## 🎯 SQL查询示例

### target_metrics.sql

```sql
-- 目标表：日度KPI指标
SELECT
    DATE(date) as Date,
    channel,
    gmv,
    net,
    net_units,
    gmv_units,
    uv,
    buyers,
    orders,
    paid_traffic,
    free_traffic,
    cancel_amount,
    return_amount,
    -- DTC细分渠道
    dtc_social_net,
    dtc_social_gmv,
    dtc_social_traffic,
    dtc_ff_net,
    dtc_ff_gmv,
    dtc_ff_traffic,
    dtc_ad_net,
    dtc_ad_gmv,
    dtc_ad_traffic,
    dtc_ad_spend,
    dtc_organic_net,
    dtc_organic_gmv,
    dtc_organic_traffic
FROM daily_kpi_metrics
WHERE date BETWEEN ? AND ?
    AND channel IN ('PFS', 'DTC', 'TOTAL')
ORDER BY date, channel;
```

### monthly_summary.sql

```sql
-- 全店核心数据_bymonth：月度汇总
SELECT
    YEAR(date) as year,
    MONTH(date) as month,
    channel,
    SUM(gmv) as gmv,
    SUM(net) as net,
    SUM(uv) as uv,
    SUM(buyers) as buyers,
    SUM(orders) as orders
FROM daily_kpi_metrics
WHERE date BETWEEN ? AND ?
GROUP BY YEAR(date), MONTH(date), channel
ORDER BY year, month, channel;
```

### traffic_l1.sql

```sql
-- 一级流量源
SELECT
    YEAR(date) as year,
    MONTH(date) as month,
    traffic_source_l1 as source_name,
    channel,
    SUM(uv) as uv,
    SUM(buyers) as buyers,
    SUM(gmv) as gmv,
    SUM(net) as net
FROM daily_traffic_metrics
WHERE date BETWEEN ? AND ?
GROUP BY YEAR(date), MONTH(date), traffic_source_l1, channel
ORDER BY year, month, uv DESC;
```

## 📊 数据流对比

### 优化前 (纯Excel)

```
Excel文件 (22个工作表, 5MB+)
  ↓
ExcelDataReader读取所有工作表
  ↓
数据处理
  ↓
报告
```

**问题**：
- ❌ Excel文件大，加载慢
- ❌ Power Query连接不稳定
- ❌ 数据无法追溯历史
- ❌ 手动更新Excel容易出错

### 优化后 (数据库优先)

```
MySQL数据库 (实时数据)
  ↓
SQL查询 (只查询需要的数据)
  ↓
数据处理引擎
  ├─ 实时聚合
  ├─ 指标计算
  └─ 渠道剔除
  ↓
报告生成 (Campaign, SalesOverview等)
```

**优势**：
- ✅ 实时数据
- ✅ 查询效率高
- ✅ 可追溯历史
- ✅ 自动化程度高
- ✅ 减少人工干预

## 🔧 迁移策略

### 阶段1: 保持兼容性

- 保留Excel读取功能
- 添加数据库查询功能
- 通过配置选择数据源

### 阶段2: 逐步迁移

- 先迁移"目标表"到数据库查询
- 验证数据一致性
- 逐步迁移其他工作表

### 阶段3: 完全切换

- 默认使用数据库查询
- Excel作为备用数据源
- 定期验证数据一致性

## 📝 配置示例

### config.yaml

```yaml
data_sources:
  # 数据库配置
  database:
    enabled: true
    connection:
      host: localhost
      port: 3306
      database: mbr_production
      user: mbr_readonly
      password: ${DB_PASSWORD}
      charset: utf8mb4
      pool_size: 5

  # 数据源优先级
  priority:
    - database  # 优先使用数据库
    - excel     # 数据库不可用时使用Excel

  # 工作表数据源映射
  sheets:
    # 使用数据库查询
    target_table:
      type: sql
      query: queries/target_metrics.sql
      params: [start_date, end_date]

    monthly_summary:
      type: sql
      query: queries/monthly_summary.sql
      params: [start_date, end_date]

    traffic_source_l1:
      type: sql
      query: queries/traffic_l1.sql
      params: [start_date, end_date]

    # 通过计算生成
    campaign:
      type: calculated
      source: target_table
      method: aggregate_by_campaign
      params: {start_date, end_date}

    sales_overview:
      type: calculated
      source: [target_table, monthly_summary]
      method: calculate_overview

    # 使用Excel (备用)
    dunhill_traffic_pivot:
      type: excel
      sheet: dunhill_traffic_pivot
      fallback: true
```

## ✅ 实施检查清单

- [ ] 安装MySQL数据库连接依赖
- [ ] 创建数据库只读用户
- [ ] 编写SQL查询文件
- [ ] 创建数据库连接模块
- [ ] 创建查询构建器
- [ ] 更新配置文件
- [ ] 更新数据读取器
- [ ] 编写单元测试
- [ ] 数据一致性验证
- [ ] 性能测试

## 🎯 预期收益

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| Excel文件大小 | ~5MB | ~500KB | ↓ 90% |
| 数据加载时间 | ~10秒 | ~2秒 | ↓ 80% |
| 数据实时性 | T+1天 | 实时 | ↑ 100% |
| 人工干预 | 每周更新 | 自动更新 | ↓ 100% |
| 错误率 | ~5% | <1% | ↓ 80% |

---

**下一步**: 开始实施数据库查询模块

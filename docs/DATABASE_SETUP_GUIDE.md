# MBR数据库集成设置指南

## 📋 概述

本指南说明如何配置MBR系统以直接从MySQL数据库读取数据，而不是从Excel文件。

## 🎯 优势

| 指标 | Excel模式 | 数据库模式 |
|------|-----------|-----------|
| 数据实时性 | T+1天 (手动更新) | 实时 |
| 文件大小 | ~5MB | ~500KB |
| 加载时间 | ~10秒 | ~2秒 |
| 人工干预 | 每周更新 | 自动 |
| 历史追溯 | 受Excel版本限制 | 完整历史 |

## 🏗️ 系统架构

```
数据库优先模式:

MySQL数据库
    ↓
DatabaseReader (SQL查询)
    ├─ 目标表 (日度KPI)
    ├─ 月度汇总
    └─ 流量源 (L1/L2/L3)
    ↓
数据处理引擎
    ├─ 聚合计算
    ├─ 指标计算
    └─ 渠道剔除
    ↓
报告生成
    ├─ Campaign (计算)
    ├─ SalesOverview (计算)
    └─ PFS流量呈现 (计算)
```

## 📝 数据库表结构

### 1. daily_kpi_metrics (日度KPI表)

**对应Excel**: 目标表

```sql
CREATE TABLE daily_kpi_metrics (
    date DATE NOT NULL COMMENT '日期',
    channel VARCHAR(20) NOT NULL COMMENT '渠道 (PFS/DTC/TOTAL)',

    -- 核心销售指标
    gmv DECIMAL(15,2) NOT NULL COMMENT '商品交易总额',
    net DECIMAL(15,2) NOT NULL COMMENT '净销售额',
    net_units INT COMMENT '净销售件数',
    gmv_units INT COMMENT 'GMV件数',

    -- 流量指标
    uv INT NOT NULL COMMENT '访客数',
    buyers INT NOT NULL COMMENT '购买人数',
    orders INT COMMENT '订单数',
    paid_traffic INT COMMENT '付费流量',
    free_traffic INT COMMENT '免费流量',

    -- 退款指标
    cancel_amount DECIMAL(15,2) COMMENT '取消金额',
    return_amount DECIMAL(15,2) COMMENT '退货金额',

    -- DTC细分渠道 - Social (社群推广)
    dtc_social_net DECIMAL(15,2) COMMENT '社群推广净销售',
    dtc_social_gmv DECIMAL(15,2) COMMENT '社群推广GMV',
    dtc_social_traffic INT COMMENT '社群推广流量',

    -- DTC细分渠道 - FF (员工福利)
    dtc_ff_net DECIMAL(15,2) COMMENT '员工福利净销售',
    dtc_ff_gmv DECIMAL(15,2) COMMENT '员工福利GMV',
    dtc_ff_traffic INT COMMENT '员工福利流量',

    -- DTC细分渠道 - Ad (广告投放)
    dtc_ad_net DECIMAL(15,2) COMMENT '广告推广净销售',
    dtc_ad_gmv DECIMAL(15,2) COMMENT '广告推广GMV',
    dtc_ad_traffic INT COMMENT '广告推广流量',
    dtc_ad_spend DECIMAL(15,2) COMMENT '广告花费',

    -- DTC细分渠道 - Organic (自然流量)
    dtc_organic_net DECIMAL(15,2) COMMENT '自然渠道净销售',
    dtc_organic_gmv DECIMAL(15,2) COMMENT '自然渠道GMV',
    dtc_organic_traffic INT COMMENT '自然渠道流量',

    PRIMARY KEY (date, channel),
    INDEX idx_date (date),
    INDEX idx_channel (channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. daily_traffic_metrics (流量源表)

**对应Excel**: 一级流量源、二级流量源、三级流量源

```sql
CREATE TABLE daily_traffic_metrics (
    date DATE NOT NULL COMMENT '日期',
    channel VARCHAR(20) NOT NULL COMMENT '渠道',

    -- 流量源层级
    source_level INT NOT NULL COMMENT '流量源层级 (1/2/3)',
    traffic_source_l1 VARCHAR(100) COMMENT '一级流量源',
    traffic_source_l2 VARCHAR(100) COMMENT '二级流量源',
    traffic_source_l3 VARCHAR(100) COMMENT '三级流量源',

    -- 流量类型
    traffic_type VARCHAR(20) COMMENT '流量类型 (paid/free/organic)',

    -- 指标
    uv INT COMMENT 'UV',
    buyers INT COMMENT '购买人数',
    orders INT COMMENT '订单数',
    gmv DECIMAL(15,2) COMMENT 'GMV',
    net DECIMAL(15,2) COMMENT '净销售',

    PRIMARY KEY (date, channel, source_level, traffic_source_l1),
    INDEX idx_date_level (date, source_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 🔧 配置步骤

### 步骤1: 创建数据库只读用户

```sql
-- 创建只读用户
CREATE USER 'mbr_readonly'@'%' IDENTIFIED BY 'your_password';

-- 授予只读权限
GRANT SELECT ON mbr_production.daily_kpi_metrics TO 'mbr_readonly'@'%';
GRANT SELECT ON mbr_production.daily_traffic_metrics TO 'mbr_readonly'@'%';

FLUSH PRIVILEGES;
```

### 步骤2: 设置环境变量

```bash
# 方式1: 导出环境变量
export DB_PASSWORD='your_password'

# 方式2: 创建 .env 文件
echo "DB_PASSWORD=your_password" >> .env
```

### 步骤3: 更新配置文件

编辑 `config.yaml`:

```yaml
data_sources:
  database:
    enabled: true  # 启用数据库查询
    connection:
      host: "your_database_host"  # 例如: localhost
      port: 3306
      database: "mbr_production"
      user: "mbr_readonly"
      password: "${DB_PASSWORD}"
      charset: "utf8mb4"
```

### 步骤4: 安装数据库依赖

```bash
pip install pymysql SQLAlchemy
```

### 步骤5: 测试数据库连接

```python
from src.ingestion.database import DatabaseReader

# 创建数据库读取器
reader = DatabaseReader("config.yaml")

# 测试连接
if reader.db and reader.db.is_connected():
    print("✓ 数据库连接成功")

    # 读取数据
    from datetime import date
    data = reader.read_target_metrics(
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 31)
    )

    print(f"✓ 读取了 {len(data)} 条记录")
else:
    print("✗ 数据库连接失败")
```

## 📊 数据验证

### 数据一致性检查

验证数据库数据和Excel数据是否一致：

```python
# 对比数据库和Excel数据
from src.ingestion.database import DatabaseReader
from src.ingestion.excel_reader import ExcelDataReader
from datetime import date

# 从数据库读取
db_reader = DatabaseReader("config.yaml")
db_data = db_reader.read_target_metrics(
    start_date=date(2025, 12, 1),
    end_date=date(2025, 12, 31)
)

# 从Excel读取
excel_reader = ExcelDataReader("MBR数据模板.xlsx")
excel_data = excel_reader.parse_target_table()

# 对比数据量
print(f"数据库记录数: {len(db_data)}")
print(f"Excel记录数: {len(excel_data.target_metrics)}")

# 对比具体数据
# TODO: 添加详细的数据对比逻辑
```

## 🔄 迁移策略

### 阶段1: 并行运行 (推荐)

1. 保持Excel数据读取正常工作
2. 添加数据库查询功能
3. 对比验证数据一致性
4. 数据库作为备用数据源

### 阶段2: 逐步切换

1. 优先使用数据库查询
2. Excel作为回退选项
3. 监控数据质量和性能

### 阶段3: 完全切换

1. 默认使用数据库
2. Excel仅用于特殊情况
3. 定期数据一致性检查

## 📝 SQL查询文件

SQL查询文件位于 `src/ingestion/database/queries/`:

| 文件 | 说明 | 对应工作表 |
|------|------|-----------|
| `target_metrics.sql` | 日度KPI查询 | 目标表 |
| `monthly_summary.sql` | 月度汇总查询 | 全店核心数据_bymonth |
| `traffic_l1.sql` | 一级流量源查询 | 一级流量源 |
| `traffic_l2.sql` | 二级流量源查询 | 二级流量源 |
| `traffic_l3.sql` | 三级流量源查询 | 三级流量源 |

## 🔍 故障排查

### 问题1: 数据库连接失败

**错误**: `Can't connect to MySQL server`

**解决方案**:
1. 检查数据库服务是否运行
2. 检查host和port配置
3. 检查防火墙设置
4. 检查用户权限

### 问题2: 密码包含特殊字符

**错误**: SQL语法错误

**解决方案**:
```bash
# 使用单引号包裹密码
export DB_PASSWORD='password!@#$%'
```

### 问题3: 时区问题

**错误**: 日期数据不匹配

**解决方案**:
```sql
-- 在查询中设置时区
SET time_zone = '+08:00';

-- 或在连接字符串中指定
connection:
  charset: 'utf8mb4'
  time_zone: '+08:00'
```

### 问题4: 性能慢

**错误**: 查询耗时过长

**解决方案**:
1. 添加索引: `CREATE INDEX idx_date ON daily_kpi_metrics(date);`
2. 限制日期范围: 只查询需要的时间段
3. 使用连接池: 已在配置中启用

## 📈 性能优化

### 查询优化

```sql
-- 添加复合索引
CREATE INDEX idx_date_channel ON daily_kpi_metrics(date, channel);

-- 添加覆盖索引
CREATE INDEX idx_date_covering ON daily_kpi_metrics(
    date, channel, gmv, net, uv, buyers
);
```

### 连接池优化

```yaml
data_sources:
  database:
    connection:
      pool_size: 10  # 增加连接池大小
      max_overflow: 20
      pool_recycle: 3600  # 1小时回收连接
```

## ✅ 检查清单

数据库集成前检查清单：

- [ ] MySQL数据库已安装并运行
- [ ] 已创建数据库表 (daily_kpi_metrics, daily_traffic_metrics)
- [ ] 已创建只读用户 (mbr_readonly)
- [ ] 已安装pymysql: `pip install pymysql`
- [ ] 已配置config.yaml
- [ ] 已设置环境变量: `export DB_PASSWORD=...`
- [ ] 已测试数据库连接
- [ ] 已验证数据一致性
- [ ] 已备份Excel数据文件

## 🎯 下一步

数据库集成完成后：

1. ✅ 运行测试: `python test_basic.py`
2. ✅ 测试数据库查询
3. ✅ 验证数据一致性
4. ✅ 性能测试
5. ✅ 切换到数据库优先模式

---

**需要帮助?** 查看 [DATA_SOURCE_ARCHITECTURE.md](DATA_SOURCE_ARCHITECTURE.md) 了解完整架构设计

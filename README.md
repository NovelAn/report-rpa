# MBR月报自动化系统

## 项目简介

MBR (Monthly Business Report) 月报自动化系统,将手动制作月报的流程转换为AI驱动的半自动化系统。

### 当前痛点

- 手动复制粘贴数据,耗时2-3小时
- Excel公式维护复杂
- 缺乏智能业务洞察
- PPT格式调整繁琐

### 解决方案

- **自动化数据处理**: 自动读取、计算、验证数据
- **AI智能洞察**: Claude AI生成业务洞察和建议
- **一键生成PPT**: 保持品牌一致性的报告生成
- **半自动化模式**: 保留人工审核环节,确保质量

## 项目结构

```
report-designer/
├── src/                    # 源代码
│   ├── models/            # 数据模型
│   ├── ingestion/         # 数据摄入
│   ├── transformation/    # 数据转换和计算
│   ├── validation/        # 数据验证
│   ├── ai/               # AI洞察生成
│   ├── ppt/              # PPT生成
│   └── workflow/         # 工作流编排
├── templates/            # PPT模板
├── skills/              # Claude Skill定义
├── tests/              # 测试代码
├── outputs/            # 输出文件
└── config.yaml         # 系统配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件,添加 ANTHROPIC_API_KEY
```

### 3. 运行示例

```python
from src.ingestion import ExcelDataReader
from src.transformation import DataAggregator
from src.validation import DataValidator

# 读取Excel数据
reader = ExcelDataReader("path/to/MBR数据模板.xlsx")
data = reader.parse_all()

# 计算月度聚合
aggregator = DataAggregator(data.target_metrics)
monthly_metrics = aggregator.calculate_all_monthly()
data.monthly_metrics = monthly_metrics

# 验证数据
validator = DataValidator()
result = validator.validate_report_data(data)
print(f"验证结果: {result.to_dict()}")
```

## 核心功能

### 1. 数据摄入 (`src/ingestion/`)

- 支持Excel、CSV、数据库等多源数据
- 自动解析22个工作表
- 统一数据模型

### 2. 数据转换 (`src/transformation/`)

- YoY、MoM增长率计算
- 月度、季度、YTD聚合
- 渠道汇总分析

### 3. 数据验证 (`src/validation/`)

- 数据完整性检查
- 业务规则验证
- 数据质量评分

### 4. AI洞察 (`src/ai/`)

- 自动生成执行摘要
- 销售趋势分析
- 流量效果评估
- 行动建议生成

### 5. PPT生成 (`src/ppt/`)

- 自动生成18张幻灯片
- 保持品牌VI一致性
- 条件格式化
- 智能图表推荐

## 技术栈

- **Python 3.11+**
- **Pydantic**: 数据模型和验证
- **Pandas**: 数据处理
- **python-pptx**: PPT生成
- **Anthropic Claude**: AI洞察

## 开发计划

- [x] Phase 1: 核心数据处理引擎
- [ ] Phase 2: AI洞察生成器
- [ ] Phase 3: PowerPoint生成引擎
- [ ] Phase 4: Claude Skill集成
- [ ] Phase 5: Web界面 (可选)

## 贡献指南

欢迎提交Issue和Pull Request!

## 📚 核心文档

- **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** ⭐ 核心业务说明
  - 20个核心业务指标定义和计算公式
  - 渠道层级体系 (TOTAL/PFS/DTC)
  - 财年计算规则 (FY25/FY26)
  - 常见问题速查

---

## 开发计划

- [x] Phase 1: 核心数据处理引擎 ✅
- [ ] Phase 2: AI洞察生成器
- [ ] Phase 3: PowerPoint生成引擎
- [ ] Phase 4: Claude Skill集成
- [ ] Phase 5: Web界面 (可选)

## 许可证

MIT License

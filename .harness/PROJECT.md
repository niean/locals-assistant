# PROJECT.md -- Hermes Assistant

Hermes 管理平台：监控和管理 Hermes cron 任务的执行状态，面向内部运维人员。

---

# Harness 框架适配

本节为 Harness 框架提供项目级配置，框架文件通过 `.harness/PROJECT.md` 直接引用。

## 知识库目录

首次加载时需建立 SUMMARY 索引的目录：
- `.harness/knowledge/`
- `.harness/prd/`（除 .harness/prd/03-prd-specs.md）
- `.harness/lessons/`

## 任务类型加载矩阵

首次加载时，根据任务类型选择性读取知识库文件（所有文件首行 SUMMARY 始终必读）：

| 任务类型 | 必读（完整读取） | 按需读取 |
|---------|----------------|---------|
| 功能需求 | .harness/knowledge/01-overview.md, .harness/knowledge/02-architecture.md, .harness/knowledge/22-file-map.md, .harness/prd/01-prd-sense.md, .harness/prd/02-prd-baseline.md | .harness/knowledge/03-conventions.md, .harness/knowledge/04-data-boundaries.md, .harness/knowledge/05-key-patterns.md, .harness/knowledge/21-glossary.md |
| 功能精调 | .harness/knowledge/01-overview.md, .harness/knowledge/22-file-map.md | .harness/knowledge/02-architecture.md, .harness/knowledge/03-conventions.md, .harness/knowledge/04-data-boundaries.md, .harness/knowledge/05-key-patterns.md, .harness/knowledge/21-glossary.md |
| Bug修复 | .harness/knowledge/01-overview.md, .harness/knowledge/03-conventions.md, .harness/knowledge/22-file-map.md | .harness/knowledge/02-architecture.md, .harness/knowledge/04-data-boundaries.md, .harness/knowledge/05-key-patterns.md, .harness/knowledge/21-glossary.md |
| 治理/扫描 | .harness/knowledge/01-overview.md, .harness/knowledge/03-conventions.md, .harness/knowledge/22-file-map.md | .harness/knowledge/02-architecture.md, .harness/knowledge/05-key-patterns.md |
| 文档维护 | .harness/knowledge/01-overview.md, .harness/knowledge/22-file-map.md | 读取目标文件引用链上的 knowledge/ 和 prd/ 文件 |

## 知识回填文件映射

知识回填的回填目标：
- 架构变化 -> .harness/knowledge/02-architecture.md
- 新术语 -> .harness/knowledge/21-glossary.md
- 数据结构/存储变化 -> .harness/knowledge/04-data-boundaries.md
- 新源文件 -> .harness/knowledge/22-file-map.md
- 新跨文件模式 -> .harness/knowledge/05-key-patterns.md
- 产品方向调整 -> 提示用户，人工更新 .harness/prd/01-prd-sense.md

## 教训库加载路径

本项目教训库分布在两个位置：
- `.harness/framework/lessons/general.md`（Harness 通用教训）
- `.harness/lessons/project.md`（项目教训）

## 构建与测试

### 构建
```bash
# 前端：无构建步骤（纯静态 HTML/CSS/JS）
# 后端：Python 语法检查
python3 -c "import py_compile; py_compile.compile('server.py', doraise=True)"
```

### 单元测试
单元测试执行策略：
- 用户明确要求时：必须执行
- 修改 server.py API 逻辑后：应执行 API 端点测试
- 其他场景：跳过

```bash
# 当前无自动化测试框架，手动验证：
# 1. 启动服务: python3 server.py
# 2. 访问 http://localhost:8090 验证页面加载
# 3. 访问 http://localhost:8090/api/jobs 验证 API 响应
```

## 扫描维度

代码扫描使用的维度及规则来源。下表路径均相对于 `.harness/knowledge/` 目录：

| # | 维度 | 规则来源 |
|---|------|---------|
| 1 | 代码规范 | 03-conventions.md §二.编码约定 |
| 2 | 架构边界 | 02-architecture.md §模块边界 |
| 3 | 安全规范 | 03-conventions.md §五.安全约定 |
| 4 | 数据边界 | 04-data-boundaries.md §边界约定 |

## 项目知识索引

| 文件 | 何时查阅 |
|------|---------|
| .harness/prd/01-prd-sense.md | 功能迭代前，确认产品定位和判断准则 |
| .harness/knowledge/01-overview.md | 任务开始时，了解项目概览（技术栈/入口/核心流程） |
| .harness/knowledge/02-architecture.md | 新增模块、修改跨层调用、重构时 |
| .harness/knowledge/03-conventions.md | 编写新代码、代码审查时 |
| .harness/knowledge/04-data-boundaries.md | 修改数据模型、API 响应结构、存储格式时 |
| .harness/knowledge/05-key-patterns.md | 实现跨模块交互、异步数据流时 |
| .harness/knowledge/21-glossary.md | 对术语不清楚时 |
| .harness/knowledge/22-file-map.md | 确定功能对应源文件时 |
| .harness/prd/02-prd-baseline.md | 确认功能需求与产品约束时 |
| .harness/lessons/project.md | 用户指令或当前根因与 SUMMARY 高度相关时按需读取 |

---

# 项目规范

## 代码生成

以下各节（代码生成、架构边界、质量守护、安全规范）为快速参考摘要，权威定义见 .harness/knowledge/03-conventions.md。

- JavaScript：遵循 Airbnb Style Guide（ES6+ Modules、const/let、箭头函数、解构赋值）
- CSS：ITCSS 架构分层（Settings → Tools → Generic → Elements → Objects → Components → Utilities）+ BEM 命名（block__element--modifier）
- Python：PEP 8 风格、类型注解、docstring
- HTML：语义化标签、无内联样式、无内联脚本（目标架构）
- 文件命名：kebab-case（如 job-card.js、job-card.css）
- 模块化：每个功能模块一个 ES6 Module，单一职责

## 架构边界

- 前后端通过 REST API（/api/*）通信，前端不直接读取文件系统
- UI 组件层不包含业务逻辑，通过 Service 层获取数据
- Python 后端仅负责数据解析与 API 暴露，不负责 Hermes 任务调度
- 详见 .harness/knowledge/02-architecture.md §模块边界

## 质量守护

- Python：`python3 -c "import py_compile; py_compile.compile('server.py', doraise=True)"` 零错误
- JavaScript：ESLint Airbnb 配置零警告（目标）
- 新代码必须模块化，禁止在 HTML 中内联超过 10 行的 JS/CSS
- API 响应必须有明确的 JSON 结构，错误时返回 `{"error": "message"}`

## 安全规范

- 禁止在代码中硬编码密钥或敏感路径（使用环境变量或配置文件）
- API 端点仅监听 localhost（127.0.0.1），不对外暴露
- 文件读取限制在 `~/.hermes/` 目录下，禁止路径遍历
- 日志中不输出完整文件路径或用户敏感信息

---

# 项目附录

## 仓库结构

```
AGENTS.md              -- AI 入口（纯路由）
CLAUDE.md              -- Claude Code 入口
.harness/
  PROJECT.md           -- 项目规范入口（本文件）
  framework/           -- 通用能力（详见 FRAMEWORK.md "Framework 目录结构"）
  knowledge/           -- AI 知识库（01~05 认知约束类, 21~22 工具索引类）
  prd/                 -- 产品文档（AI只读：01-prd-sense、02-prd-baseline、03-prd-specs）
  lessons/
    project.md         -- 项目教训（AI自主维护）
  specs/               -- 设计文档
    active/
    completed/
  plans/               -- 实现计划
    active/
    completed/
    debt-tracker.md    -- 技术债追踪
index.html             -- 前端入口（单页应用）
css/                   -- 样式文件（ITCSS 分层，目标架构）
  settings/            -- 变量、配置
  tools/               -- Mixins、函数
  generic/             -- Reset、Normalize
  elements/            -- HTML 元素默认样式
  objects/             -- 布局对象
  components/          -- UI 组件
  utilities/           -- 工具类
js/                    -- JavaScript 模块（目标架构）
  main.js              -- 应用入口
  services/            -- API 调用、数据服务
  components/          -- UI 组件类
  utils/               -- 工具函数
server.py              -- Python HTTP 服务器 + API
scripts/
  start-http-exec.sh   -- 启动脚本（launchd 管理）
favicon.svg            -- 站点图标
```

## 知识层级关系

```
Layer 0   AGENTS.md -> FRAMEWORK.md（通用规范+注册表） + PROJECT.md（项目配置+规则摘要）
Layer 1   framework/agents/（5个角色: Orchestrator/Designer/Planner/Coder/Reviewer）
Layer 1.5 framework/workflows/（迭代功能/修复Bug/迭代文档 + harness-ops/治理类）
Layer 2   framework/skills/（harness/ 核心Skill + harness-ops/ 运维Skill + superpowers/ 方法论）
Layer 3   framework/skills/harness/subskills/（扫描模板）
数据层    knowledge/（权威知识） + prd/（产品文档，AI只读） + guides/（方法论） + lessons/（教训）
辅助层    specs/（设计文档） + plans/（执行计划+技术债）
```

引用方向：Layer 0 -> Layer 1/1.5 -> Layer 2 -> Layer 3 -> 数据层。PROJECT.md 摘要引用 knowledge/03-conventions.md（权威源）。

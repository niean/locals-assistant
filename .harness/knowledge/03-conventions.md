<!-- SUMMARY: Hermes Assistant 编码约定、质量标准与安全规范 -->
# 约定与约束（实现细节）

本文件是项目规范约定的权威来源，`.harness/PROJECT.md` "项目规范"各节为摘要引用，以本文件为准。

---

# 一、UI交互约定

- 响应式：支持桌面浏览器，最小宽度 768px，无需移动端适配
- 刷新：自动轮询 5 分钟间隔，支持手动刷新按钮
- 状态着色：Delivered（绿色）、Silent（灰色）、Error（红色）
- 链接：CM 开头的订单号自动生成跳转链接（op.zuoyebang.cc）

---

# 二、编码约定

## JavaScript（Airbnb Style Guide）

- 使用 ES6+ 语法：const/let（禁止 var）、箭头函数、解构赋值、模板字符串
- 模块化：每个文件使用 `export`/`import`，type="module" 加载
- 命名：camelCase 变量/函数、PascalCase 类名、UPPER_SNAKE_CASE 常量
- 函数：单一职责，不超过 30 行，复杂逻辑拆分为子函数
- 异步：使用 async/await，禁止裸 .then() 链超过 2 层
- 错误处理：所有 fetch 调用必须 try/catch，失败时向用户展示友好提示
- 注释：关键业务逻辑添加 JSDoc，工具函数标注参数类型

## CSS（ITCSS + BEM）

- 分层顺序：Settings → Tools → Generic → Elements → Objects → Components → Utilities
- BEM 命名：`.block__element--modifier`，最多两层嵌套
- 禁止 ID 选择器用于样式，ID 仅用于 JS hook
- 颜色/字号/间距使用 CSS Custom Properties（变量）
- 组件样式文件与 JS 组件同名：`job-card.css` 对应 `job-card.js`
- 禁止 `!important`（utilities 层除外）

## Python（PEP 8）

- 类型注解：函数签名必须标注参数和返回值类型
- Docstring：public 函数必须有 docstring（Google 风格）
- 行宽：88 字符（Black 格式化器标准）
- 命名：snake_case 变量/函数、PascalCase 类名
- 错误处理：捕获具体异常，禁止裸 `except:`

## HTML

- 语义化标签：header、main、section、article、nav 等
- 无内联样式（`style=""`），无内联脚本（`<script>` 块内联超 10 行）
- 属性顺序：id → class → data-* → src/href → aria-*
- 自定义数据属性使用 `data-*` 前缀

## 文件命名

- 所有源文件使用 kebab-case：`job-card.js`、`stats-bar.css`
- 目录名使用 kebab-case
- Python 文件使用 snake_case：`be/server.py`（仅后端）

## 常量

- 前端常量集中在 `fe/js/utils/constants.js`
- API 路径常量化：`API_BASE = '/api'`
- 刷新间隔等可配置项不硬编码在业务代码中
- 禁止魔法数字，给数字赋予语义命名

## 禁止 Mock 造假

生产代码禁止以硬编码假数据冒充真实实现。具体规则：

- 禁止返回硬编码的 mock JSON 代替真实文件解析结果
- 文件不存在或格式异常时返回空数组 `[]`，附带日志说明原因
- 数据源不可用时 API 应返回 `{"error": "..."}` 而非伪造正常响应

---

# 三、质量约定

## 构建验证

- Python：`python3 -c "import py_compile; py_compile.compile('be/server.py', doraise=True)"`
- JavaScript：`node --check fe/js/**/*.js`（语法校验，目标架构）
- 所有变更后必须通过语法检查

## 错误处理

- 用户：页面展示友好的中文错误提示（如"数据加载失败，请稍后刷新"）
- 开发：be/server.py 使用 logging 模块，记录异常堆栈到 server.log
- API 错误响应格式：`{"error": "错误描述", "code": "ERROR_CODE"}`
- 超时：API 请求前端 10 秒超时，文件读取后端 5 秒超时

## 日志

- 后端使用 Python `logging` 模块，禁止 `print()`
- 日志级别：DEBUG（文件解析细节）、INFO（请求日志）、WARNING（数据异常）、ERROR（服务异常）
- 日志输出到 `~/Library/Logs/assistant-http/server.log`
- 日志中禁止输出完整文件路径，使用相对路径或脱敏

## 线程与并发

- be/server.py 使用 ThreadingMixIn 处理并发请求
- 文件 I/O 在请求处理线程中同步执行（数据量小，无需异步）
- 前端单线程，通过 async/await 管理异步

## 性能

- 任务列表数据轻量（通常 < 50 条），无需分页
- 执行历史按 limit 参数截取，默认最近 20 条
- 前端 DOM 操作使用 DocumentFragment 批量插入

## 单元测试

- 测试目录：`tests/`（目标架构）
- Python 测试：pytest，文件命名 `test_*.py`
- 前端测试：待引入（当前手动验证）
- 新增 API 端点时应补充对应的 pytest 用例

## 代码扫描

代码扫描（Reviewer 代码扫描能力）发现的问题处理规则：

- 本次变更新引入的问题：必须在本次修复
- 既存问题（非本次引入）：记录到 debt-tracker.md，不阻塞提交
- 判定方法：git diff 比对，仅在本次新增/修改行中出现的问题视为新引入
- 例外情况：安全漏洞无论是否本次引入都需立即修复

---

# 四、文件管理约定

- 禁止主动创建 README.md 文件（除非用户明确要求）
- 禁止自主删除项目文件（除非用户明确要求或文件为临时产物）
- 新增文件遵循 kebab-case 命名
- knowledge 文件编号规则：01~05 认知约束类，21~22 工具索引类
- 执行计划存放于 `.harness/plans/active/`，完成后移动到 `completed/`

---

# 五、安全约定

- 密钥：禁止在代码中硬编码任何密钥或 token，使用环境变量
- 网络：仅监听 127.0.0.1，不绑定 0.0.0.0
- 隐私：不收集用户行为数据，日志中不记录请求 IP
- 文件访问：be/server.py 读取路径必须限制在 ~/.hermes/ 下，验证路径无 `..` 遍历
- 响应头：设置 Content-Type，避免 MIME 嗅探

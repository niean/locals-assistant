<!-- SUMMARY: Hermes Assistant 数据模型、API 接口契约与存储结构 -->
# 数据与类型边界

## 核心数据模型

### Job（任务配置）

来源：`~/.hermes/cron/jobs.json`

```json
{
  "job_id": "string",        // 任务唯一标识
  "name": "string",          // 任务名称（中文）
  "schedule": "string",      // cron 表达式
  "state": "enabled|disabled", // 启用状态
  "next_run": "ISO8601",     // 下次执行时间
  "last_run": "ISO8601"      // 上次执行时间
}
```

### Run（执行记录）

来源：`~/.hermes/cron/output/{job_id}/*.md`（Markdown 文件解析）

```json
{
  "timestamp": "ISO8601",    // 执行时间
  "job_name": "string",      // 任务名称
  "response": "string",      // 响应内容（可能含 CM 订单号）
  "status": "delivered|silent|error"  // 执行状态
}
```

状态判定规则：
- 文件内容包含 `[SILENT]` 标记 → status = "silent"
- 文件解析异常或包含错误关键词 → status = "error"
- 其他情况 → status = "delivered"

### JobSummary（前端展示聚合）

API `/api/jobs` 返回的聚合数据：

```json
{
  "job_id": "string",
  "name": "string",
  "schedule": "string",
  "state": "enabled|disabled",
  "next_run": "ISO8601",
  "last_run": "ISO8601",
  "today_total": "number",     // 今日执行总次数
  "today_delivered": "number", // 今日 delivered 次数
  "today_silent": "number"     // 今日 silent 次数
}
```

## API 接口契约

### GET /api/jobs

- 响应：`JobSummary[]`
- 错误：`{"error": "message"}`

### GET /api/runs/{job_id}?limit=N

- 参数：job_id（路径参数），limit（查询参数，默认 20）
- 响应：`Run[]`（按时间倒序）
- 错误：`{"error": "message"}`

### GET /（静态资源）

- 响应：index.html 及关联的 CSS/JS 文件

## 磁盘存储结构（只读）

```
~/.hermes/cron/
  jobs.json              -- 任务配置（JSON 数组）
  output/
    {job_id}/            -- 按任务分目录
      YYYYMMDD-HHMMSS.md  -- 每次执行的输出记录（Markdown）
```

Markdown 文件格式（由 Hermes 系统生成）：
- 首行：任务名称
- 正文：执行响应内容
- 特殊标记：`[SILENT]` 表示静默执行

## 边界约定

- 前端不直接构造/解析 Markdown 文件，所有解析由 be/server.py 完成
- API 返回数据已格式化为 JSON，前端直接使用
- 执行历史按 limit 截取，大量历史数据不全量返回
- jobs.json 配置与 output/ 目录数据合并逻辑在 be/server.py 中完成

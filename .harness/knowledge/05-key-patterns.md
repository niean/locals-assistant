<!-- SUMMARY: Hermes Assistant 关键代码模式：数据轮询、状态着色、链接识别 -->
# 关键代码模式

项目中反复出现但不易从单个文件推断的模式，供新功能实现时参照。

## 模式一：定时轮询刷新

前端通过 setInterval 定期调用 API 刷新数据：

1. 页面加载完成 → 首次 fetchJobs()
2. setInterval(fetchJobs, 5 * 60 * 1000) 注册定时器
3. fetchJobs 获取数据后全量替换 DOM（简单重绘）
4. 手动刷新按钮调用 fetchJobs() 并重置定时器

陷阱：定时器未在页面隐藏时暂停，可能产生不必要的请求。可用 document.visibilitychange 优化。

## 模式二：Markdown 文件解析

server.py 将 Hermes 输出的 Markdown 文件解析为结构化数据：

1. 扫描 output/{job_id}/ 目录下所有 .md 文件
2. 文件名解析为时间戳（YYYYMMDD-HHMMSS 格式）
3. 读取文件内容，提取任务名和响应正文
4. 检测 `[SILENT]` 标记判定状态
5. 异常文件跳过，记录日志

陷阱：文件编码必须为 UTF-8，其他编码会导致解析失败。文件名格式不符时应跳过而非报错。

## 模式三：订单号链接识别

前端识别响应内容中的 CM 开头订单号并生成超链接：

1. 正则匹配：`/CM\d+/g`
2. 匹配到的文本替换为 `<a href="https://op.zuoyebang.cc/order/{id}" target="_blank">{id}</a>`
3. 非 CM 开头的文本保持原样

陷阱：innerHTML 注入需对非链接部分进行 XSS 转义。

## 模式四：任务配置与执行记录合并

server.py 的 /api/jobs 需要合并两个数据源：

1. 读取 jobs.json 获取任务配置（id/name/schedule/state）
2. 扫描 output/ 目录获取实际执行记录
3. 按 job_id 关联，计算今日统计（total/delivered/silent）
4. 配置中有但无执行记录的任务：统计为 0
5. output/ 中有但配置中没有的任务：仍然展示（可能是已删除任务的历史）

## 模式五：状态视觉映射

前端根据任务/执行状态应用不同视觉样式：

- Job 级别：enabled → 正常显示，disabled → 灰色 + 半透明
- Run 级别：delivered → 绿色标签，silent → 灰色标签，error → 红色标签
- 统计级别：数字着色与对应状态一致

BEM 实现：`.run-status--delivered`、`.run-status--silent`、`.run-status--error`

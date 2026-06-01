# Modular Refactor Implementation Plan

- 创建时间: 2026-06-01 15:10
- 状态: active
- 关联 spec: .harness/specs/active/spec-260601-modular-refactor.md

> **For agentic workers:** REQUIRED SUB-SKILL: Use .harness/framework/skills/superpowers/subagent-driven-development.md (recommended) or .harness/framework/skills/superpowers/executing-plans.md to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将单体 index.html 拆分为 ITCSS CSS + ES6 Modules JS，实现关注点分离

**Architecture:** 浏览器原生模块加载（无 bundler），CSS 通过多个 link 标签按 ITCSS 顺序加载，JS 通过 script type=module 入口加载。server.py 添加 StaticFiles mount 服务静态资源。

**Tech Stack:** HTML5, CSS3 Custom Properties, ES6 Modules, Python Starlette StaticFiles

---

### T1: 创建 CSS 文件（ITCSS 分层）

**Files:**
- Create: `css/settings/variables.css`
- Create: `css/generic/reset.css`
- Create: `css/components/tab-nav.css`
- Create: `css/components/stat-card.css`
- Create: `css/components/status-panel.css`
- Create: `css/components/sessions.css`
- Create: `css/components/job-card.css`
- Create: `css/components/badges.css`
- Create: `css/components/modal.css`
- Create: `css/components/buttons.css`
- Create: `css/utilities/text.css`

- [ ] **S1: 创建目录结构**

Run: `mkdir -p css/settings css/generic css/components css/utilities`

- [ ] **S2: 创建 css/settings/variables.css**

从内联 CSS 提取颜色、字号、间距为 CSS Custom Properties:
```css
:root {
  --color-fg-default: #1f2328;
  --color-fg-muted: #656d76;
  --color-fg-subtle: #8c959f;
  --color-border-default: #d1d9e0;
  --color-border-muted: #eaeef2;
  --color-bg-default: #f8f9fa;
  --color-bg-subtle: #f6f8fa;
  --color-bg-inset: #eaeef2;
  --color-bg-white: #ffffff;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-accent: #0969da;
  --font-mono: 'SF Mono', SFMono-Regular, monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 10px;
  --radius-2xl: 12px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
  --shadow-md: 0 1px 3px rgba(0,0,0,0.08);
}
```

- [ ] **S3: 创建 css/generic/reset.css**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-sans);
  background: var(--color-bg-default);
  color: var(--color-fg-default);
  min-height: 100vh;
  padding: 24px;
}
```

- [ ] **S4: 创建 css/components/tab-nav.css**

提取 .tab-nav, .tab-btn, .tab-content, .subtab-content 样式（index.html 行 51-87）

- [ ] **S5: 创建 css/components/stat-card.css**

提取 .stats-bar, .stat-card 及修饰符样式（行 89-128）

- [ ] **S6: 创建 css/components/status-panel.css**

提取 .status-grid, .status-panel, .indicator 样式（行 130-180）

- [ ] **S7: 创建 css/components/sessions.css**

提取 .sessions-table, .source-badge 及其修饰符样式（行 182-235）

- [ ] **S8: 创建 css/components/job-card.css**

提取 .job-section, .job-header, .job-meta, .runs-table 样式（行 237-297）

- [ ] **S9: 创建 css/components/badges.css**

提取 .status-badge, .status-dot 及修饰符样式（行 299-312）

- [ ] **S10: 创建 css/components/modal.css**

提取 .modal-overlay, .modal, .modal-header, .modal-close, .modal-body 样式（行 374-418）

- [ ] **S11: 创建 css/components/buttons.css**

提取 .header .refresh-btn, .prompt-btn, .icon-btn 样式（行 34-48 + 344-372）

- [ ] **S12: 创建 css/utilities/text.css**

提取 .response-text, .timestamp, .response-toggle, .response-full, .order-link, .empty-state, .last-update 样式（行 314-341）

---

### T2: 创建 JS 模块（ES6 Modules）

**Files:**
- Create: `js/utils/constants.js`
- Create: `js/utils/helpers.js`
- Create: `js/services/api.js`
- Create: `js/components/navigation.js`
- Create: `js/components/overview.js`
- Create: `js/components/jobs.js`
- Create: `js/components/sessions.js`
- Create: `js/components/tools.js`
- Create: `js/components/modal.js`
- Create: `js/main.js`

- [ ] **S1: 创建 JS 目录结构**

Run: `mkdir -p js/utils js/services js/components`

- [ ] **S2: 创建 js/utils/constants.js**

```javascript
export const API_BASE = '/assistant';
export const REFRESH_INTERVAL = 5 * 60 * 1000;
```

- [ ] **S3: 创建 js/utils/helpers.js**

提取工具函数：escapeHtml, linkify, formatNumber, toggleResponse

```javascript
export function escapeHtml(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

export function linkify(html) {
  return html.replace(/CM(\d{6,})/g, '<a class="order-link" href="https://op.zuoyebang.cc/static/odin/index.html#/cm/wait/detail/CM$1" target="_blank">CM$1</a>');
}

export function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

export function toggleResponse(id) {
  document.getElementById(id).classList.toggle('open');
}
```

- [ ] **S4: 创建 js/services/api.js**

封装所有 fetch 调用，统一错误处理：

```javascript
import { API_BASE } from '../utils/constants.js';

export async function fetchJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
}

export async function postJson(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}
```

- [ ] **S5: 创建 js/components/navigation.js**

提取 switchTab, switchSubTab, getTabFromHash 及 hashchange listener：

```javascript
export function switchTab(name, updateHash = true) { ... }
export function switchSubTab(name) { ... }
export function getTabFromHash() { ... }
export function initNavigation() {
  window.addEventListener('hashchange', () => switchTab(getTabFromHash(), false));
  switchTab(getTabFromHash(), false);
}
```

- [ ] **S6: 创建 js/components/overview.js**

提取 loadStatus, renderOverview 函数

- [ ] **S7: 创建 js/components/jobs.js**

提取 loadJobs, loadRuns, renderJobs, renderRuns, showPrompt 函数

- [ ] **S8: 创建 js/components/sessions.js**

提取 loadSessions, renderSessions, renderSessionTable, showSessionMessages, startRename, cancelRename, submitRename, disconnectSession 函数

- [ ] **S9: 创建 js/components/tools.js**

提取 loadSkills, renderSkills, renderSkillTable, loadMcp, loadPlugins, showSkillContent 函数

- [ ] **S10: 创建 js/components/modal.js**

提取 showPrompt 关联的 modal 操作函数：

```javascript
export function closePromptModal(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('prompt-modal').classList.remove('open');
}

export function openModal(title) {
  const modal = document.getElementById('prompt-modal');
  const body = document.getElementById('prompt-modal-body');
  const modalTitle = document.getElementById('prompt-modal-title');
  body.textContent = 'Loading...';
  modalTitle.textContent = title;
  modal.classList.add('open');
  return body;
}
```

- [ ] **S11: 创建 js/main.js**

应用入口，组装各模块：

```javascript
import { REFRESH_INTERVAL } from './utils/constants.js';
import { initNavigation } from './components/navigation.js';
import { loadStatus } from './components/overview.js';
import { loadJobs } from './components/jobs.js';
import { loadSessions } from './components/sessions.js';
import { loadSkills, loadMcp, loadPlugins } from './components/tools.js';

async function loadAll() {
  await Promise.all([loadStatus(), loadJobs(), loadSessions(), loadSkills(), loadMcp(), loadPlugins()]);
  document.getElementById('last-update').textContent = `Last updated: ${new Date().toLocaleString('zh-CN')}`;
}

// Initialize
initNavigation();
loadAll();
setInterval(loadAll, REFRESH_INTERVAL);

// Expose loadAll for refresh button
window.loadAll = loadAll;
```

---

### T3: 重写 index.html 为纯骨架

**Files:**
- Modify: `index.html`

- [ ] **S1: 重写 index.html**

移除所有 `<style>` 和 `<script>` 内容，替换为 `<link>` 和 `<script type="module">` 引用。保留 HTML 结构不变。

index.html 结构：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <title>Hermes Assistant</title>
  <!-- ITCSS: Settings -->
  <link rel="stylesheet" href="css/settings/variables.css">
  <!-- ITCSS: Generic -->
  <link rel="stylesheet" href="css/generic/reset.css">
  <!-- ITCSS: Components -->
  <link rel="stylesheet" href="css/components/tab-nav.css">
  <link rel="stylesheet" href="css/components/stat-card.css">
  <link rel="stylesheet" href="css/components/status-panel.css">
  <link rel="stylesheet" href="css/components/sessions.css">
  <link rel="stylesheet" href="css/components/job-card.css">
  <link rel="stylesheet" href="css/components/badges.css">
  <link rel="stylesheet" href="css/components/modal.css">
  <link rel="stylesheet" href="css/components/buttons.css">
  <!-- ITCSS: Utilities -->
  <link rel="stylesheet" href="css/utilities/text.css">
</head>
<body>
  [... existing HTML body unchanged ...]
  <script type="module" src="js/main.js"></script>
  <script src="/shared-nav.js"></script>
</body>
</html>
```

- [ ] **S2: 处理 onclick 内联事件绑定**

由于 ES Module 作用域隔离，onclick="fn()" 需要 window 上的全局引用。在各 component 模块中 export 函数后，在 main.js 中统一挂载到 window：

```javascript
// main.js 中补充
import { switchTab, switchSubTab } from './components/navigation.js';
import { showPrompt } from './components/jobs.js';
import { showSessionMessages, disconnectSession, startRename, submitRename, cancelRename } from './components/sessions.js';
import { showSkillContent } from './components/tools.js';
import { toggleResponse } from './utils/helpers.js';
import { closePromptModal } from './components/modal.js';

// Expose to inline handlers
Object.assign(window, {
  loadAll, switchTab, switchSubTab, showPrompt, closePromptModal,
  showSessionMessages, disconnectSession, startRename, submitRename, cancelRename,
  showSkillContent, toggleResponse,
});
```

---

### T4: 更新 server.py 支持静态文件

**Files:**
- Modify: `server.py`

- [ ] **S1: 添加 StaticFiles import 和 mount**

在 server.py 中：
1. 添加 import: `from starlette.staticfiles import StaticFiles`
2. 移除 `homepage` 路由函数
3. 在 routes 列表中，将 `Route("/", homepage)` 替换为最后追加 `Mount("/", StaticFiles(directory=str(STATIC_DIR), html=True))`

```python
from starlette.staticfiles import StaticFiles
from starlette.routing import Route, Mount

app = Starlette(routes=[
    # API routes first (priority)
    Route("/api/jobs", api_jobs),
    Route("/api/runs/{job_id}", api_runs),
    Route("/api/status", api_status),
    Route("/api/sessions", api_sessions),
    Route("/api/sessions/{session_id}/messages", api_session_messages),
    Route("/api/sessions/{session_id}/disconnect", api_disconnect_session, methods=["POST"]),
    Route("/api/sessions/{session_id}/rename", api_rename_session, methods=["POST"]),
    Route("/api/prompt/{job_id}", api_prompt),
    Route("/api/skills", api_skills),
    Route("/api/skills/{skill_path:path}/content", api_skill_content),
    Route("/api/plugins", api_plugins),
    Route("/api/mcp", api_mcp_servers),
    # Static files last (catch-all)
    Mount("/", StaticFiles(directory=str(STATIC_DIR), html=True)),
])
```

- [ ] **S2: 验证 Python 语法**

Run: `python3 -c "import py_compile; py_compile.compile('server.py', doraise=True)"`
Expected: 无输出（成功）

---

### T5: 验证与收尾

- [ ] **S1: 重启服务**

Run: `launchctl kickstart -k gui/$(id -u)/com.niean.assistant-dashboard && sleep 3 && launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway`

- [ ] **S2: 验证页面加载**

浏览器访问 http://localhost:8090，确认：
1. 四个 tab 切换正常
2. Overview 数据加载正常
3. Cron Jobs 列表和执行历史正常
4. Sessions 列表、详情查看、断开连接正常
5. Tools 三个 subtab 正常

- [ ] **S3: 验证浏览器控制台无 JS 错误**

- [ ] **S4: 验证 URL 路由**

刷新浏览器时 hash 路由（#cron, #sessions, #tools）正确恢复

---

## 变更记录
| 时间 | 变更内容 |
|------|---------|

## 发现的技术债
- (暂无)

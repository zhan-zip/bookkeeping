# Bookkeeping 项目实施总结

## 一、项目概述

基于 **QQ 机器人自然语言记账** + **手机 PWA 只读看数据** 的个人记账系统。

**目录：** `D:\Desktop\test\opencode\bookkeeping\`

**仓库：** `https://github.com/zhan-zip/bookkeeping`（已改公开，免费 GitHub Pages）

**状态：** 2026-08-23 M1/M2/M3/M4 完成，项目上线 ✅

---

## 二、架构

```
GitHub 仓库（zhan-zip/bookkeeping，公开）
  └─ data/expenses.json   ← 唯一数据源（GitHub API 读写，MCP 带写 token；PWA 可匿名只读）
         ↑ GitHub API
   ┌─────┴──────┐
   │            │
PWA（手机只读）  QQ 机器人（记账 MCP）
  匿名/只读 token  MCP server（内部持写 token）
```

**三大核心模块：**
1. **余额（本月开销视角）** — 每月最后一天 00:00 清零，手动记"收入：生活费"当期初
2. **心愿储蓄（心理账户，纯记录）** — 只记"东西名+价格"，真买转正式支出并从清单消失
3. **实际储蓄（每月独立）** — 每月 = 当月生活费剩余，不跨月累计

---

## 三、M1 实施计划：数据层 ✅ 已完成

**内容：**
- 仓库（已公开）`data/expenses.json` + `data/wishlist.json`
- JSON schema 定义（每条记录含 id/type/amount/category/note/date/balance_after/created_at）
- GitHub Contents API 读写封装（GET 拿文件+sha → PUT 带 sha 防冲突）

---

## 四、M2 实施计划：MCP Server ✅ 已完成

**内容：**
- 独立 MCP server 进程（stdio 模式，供 qq-agent 接入）
- 暴露 13 个标准工具，直接调用 storage.py 核心逻辑
- fastmcp 实现，零配置即用

---

## 五、M3 实施计划：PWA 前端 ✅ 已完成

**内容：**
- Vue3 + Vite + vite-plugin-pwa (autoUpdate) + ECharts
- 部署 GitHub Pages (`zhan-zip.github.io/bookkeeping`)
- `base: '/bookkeeping/'` 配置
- 只读 token 存 localStorage，仅授权 Contents read
- 底部中间浮动按键导航（可收起/展开）
- 黑白风：背景纯白、主文字纯黑、次要信息灰阶、仅负数/超支用红色

---

## 六、M4 实施计划：优化阶段 ✅ 已完成

**内容：**
- **自然语言记账优化**：MCP 新增 `parse_expense_text_tool`，服务端解析"午饭25"等自然语言
- **预算设置**：前端新增预算页，可配置分类预算（如零食¥200/月），总览/月报超支标红提醒
- **月报图片版**：ECharts + html2canvas 生成分享图，一键保存/分享

---

## 七、部署上线 ✅ 2026-08-23 完成

**线上地址：** https://zhan-zip.github.io/bookkeeping/

**部署配置：**
- GitHub Pages Source: **GitHub Actions** (非 gh-pages 分支)
- 自动构建部署：推送 main 分支触发 `.github/workflows/deploy.yml`
- 构建产物：client/dist → GitHub Pages
- 环境配置：github-pages environment，Deployment branches 设为 "No restriction"
- 站点地址：https://zhan-zip.github.io/bookkeeping/

**验证结果：** ✅ 站点上线，PWA 可安装，6 页面功能完整，数据实时从 GitHub API 读取

---

## 四、开发迭代记录

### 2026-08-18 M1 完成：数据层实施

**实施内容：**
1. 创建项目结构（Python 后端 `server/` + 测试目录 `tests/`）
2. 定义 JSON Schema（expenses.json / wishlist.json）
3. 实现 GitHub API 客户端（读/写/冲突处理，`github_client.py`）
4. 实现数据层核心逻辑（余额计算、月度清零、AA 冲抵、心愿清单，`storage.py`）
5. 编写单元测试验证（14 个测试全部通过）

**文件改动：**
| 文件 | 类型 | 说明 |
|------|------|------|
| `server/` | 新增 | 后端项目目录 |
| `server/requirements.txt` | 新增 | Python 依赖 |
| `server/.env.example` | 新增 | 环境变量模板 |
| `server/src/github_client.py` | 新增 | GitHub Contents API 封装 |
| `server/src/models.py` | 新增 | 数据模型定义 |
| `server/src/storage.py` | 新增 | 数据读写业务逻辑 |
| `server/src/main.py` | 新增 | 入口/手动测试脚本 |
| `tests/test_storage.py` | 新增 | 单元测试（14 passed） |

**验证结果：** ✅ 所有单元测试通过
- 模型测试：ExpenseRecord/WishItem 序列化、ID 生成、月份边界判断、分类定义
- 存储逻辑：余额计算、重新计算、月度筛选、期初生活费识别
- AA 公式：名义支出/收入、实际支出/收入、余额计算验证
- 心愿清单：买入流程（移除愿望+转支出）

**核心业务逻辑实现：**
- `add_expense` / `get_recent` / `get_today` / `get_month_summary`
- `get_category_stats` / `get_budget_status`
- `add_wish` / `get_wishlist` / `buy_wish`
- `get_monthly_report` / `delete_expense` / `update_expense`
- `ensure_monthly_allowance` / `init_repo`

---

### 2026-08-18 M2 完成：MCP Server 实施

**实施内容：**
1. 安装 `fastmcp` 依赖
2. 编写 `server/src/mcp_server.py`，暴露 13 个标准工具
3. 工具直接调用 `storage.py` 现有函数，无重复逻辑
4. 支持 stdio 传输，qq-agent 可直接接入

**新增文件：**
| 文件 | 类型 | 说明 |
|------|------|------|
| `server/src/mcp_server.py` | 新增 | MCP Server 入口，13 个工具 |

**暴露的 13 个工具：**
| 工具 | 对应 storage 函数 | 说明 |
|------|------------------|------|
| `add_expense_tool` | `add_expense` | 记一笔（自动算余额） |
| `get_summary_tool` | `get_month_summary`/`get_today` | 今日/本周/本月汇总（`year` 未实现，传非 today/week/month 会报错） |
| `get_category_stats_tool` | `get_category_stats` | 分类占比 |
| `get_recent_tool` | `get_recent` | 最近 N 笔流水 |
| `get_budget_status_tool` | `get_budget_status` | 预算剩余/超支 |
| `add_wish_tool` | `add_wish` | 心愿清单加一条 |
| `buy_wish_tool` | `buy_wish` | 心愿真买 → 转支出 + 从清单消失 |
| `get_monthly_report_tool` | `get_monthly_report` | 月报完整数据 |
| `ensure_allowance_tool` | `ensure_monthly_allowance` | 确保本月有期初生活费 |
| `parse_expense_text_tool` | `parse_expense_text` | 自然语言解析"午饭25"等 |
| `list_categories_tool` | `get_categories` | 获取所有分类（动态读取） |
| `add_category_tool` | `add_category` | 新增分类（去重、长度限制） |
| `delete_category_tool` | `delete_category` | 删除分类（内置 8 类受保护） |
| `delete_expense_tool` | `delete_expense` | 删除流水（自动重算余额） |
| `update_expense_tool` | `update_expense` | 修改流水（部分字段，自动重算余额） |
| `push_monthly_report_tool` | (内部 `_format_monthly_report_text`) | 生成月报推送文本 |

**验证结果：** ✅ 导入正常，工具注册完整

---

### 2026-08-18 M3 完成：PWA 前端实施

**实施内容：**
1. 创建 `client/` Vue3 + Vite 项目
2. 配置 PWA：vite-plugin-pwa (autoUpdate)、manifest、Service Worker
3. 配置 GitHub Pages 部署：`base: '/bookkeeping/'`
4. 实现 5 个页面：总览、流水、心愿、月报、设置
5. 底部中间浮动按键导航（可收起/展开遮罩）
6. 黑白风 UI：纯白背景、纯黑主文字、灰阶次要信息、仅负数用红色
7. ECharts 饼图展示分类占比
7. 下拉刷新、触摸滚动、点击交互
8. GitHub Token 本地存储，只读 API 调用

**新增文件：**
| 文件 | 类型 | 说明 |
|------|------|------|
| `client/` | 新增 | 前端项目目录 |
| `client/src/api/github.js` | 新增 | GitHub API 封装（只读） |
| `client/src/api/storage.js` | 新增 | 业务逻辑（复用 M1 逻辑） |
| `client/src/stores/app.js` | 新增 | Pinia 状态管理 |
| `client/src/router/index.js` | 新增 | Vue Router 配置 |
| `client/src/views/Overview.vue` | 新增 | 总览页（余额卡片、饼图、心愿预览） |
| `client/src/views/Records.vue` | 新增 | 流水页（分组列表、增删改弹窗） |
| `client/src/views/Wishes.vue` | 新增 | 心愿页（列表、添加、真买转支出） |
| `client/src/views/Report.vue` | 新增 | 月报页（完整数据、饼图、分类明细） |
| `client/src/views/Settings.vue` | 新增 | 设置页（Token 配置、连接测试） |
| `client/src/App.vue` | 重写 | 主布局、浮动导航、Toast |
| `client/src/assets/main.css` | 新增 | 黑白风样式、响应式 |
| `client/public/manifest.webmanifest` | 新增 | PWA 清单 |
| `client/public/favicon.svg` | 新增 | 图标 |
| `client/vite.config.js` | 重写 | PWA 配置、base 路径、别名 |

**验证结果：** ✅ `npm run build` 成功，PWA 资源预缓存正常，`npm run dev` 本地预览无报错

---

### 2026-08-23 M4 完成：优化阶段 & 部署上线

**M4 实施内容：**
1. **自然语言记账优化**：MCP 新增 `parse_expense_text_tool`，服务端解析"午饭25"、"买键盘499购物"、"收到生活费2000"等自然语言，返回结构化数据
2. **预算设置**：前端新增 Budget 页面，可配置分类预算，总览/月报超支标红提醒，预算持久化到 localStorage
3. **月报图片版**：Report 页集成 html2canvas，一键生成月报分享图（含饼图、数据卡片）

**部署上线：**
- GitHub Pages Source 改为 **GitHub Actions**
- 环境 github-pages 配置 "No restriction" 允许所有分支部署
- 推送 main 分支自动触发 `.github/workflows/deploy.yml` 构建部署
- 站点上线：https://zhan-zip.github.io/bookkeeping/

**新增文件：**
| 文件 | 类型 | 说明 |
|------|------|------|
| `client/src/views/Budget.vue` | 新增 | 预算设置页 |
| `client/src/views/Report.vue` | 重写 | 新增 html2canvas 生成图片功能 |
| `client/src/api/github.js` | 修复 | Source 改为 GitHub Actions 后的环境配置 |
| `.github/workflows/deploy.yml` | 新增 | GitHub Actions 自动部署工作流 |

**验证结果：** ✅ 站点上线 https://zhan-zip.github.io/bookkeeping/，PWA 可安装，6 页面功能完整，数据实时从 GitHub API 读取，PWA 离线缓存正常

---

### 2026-08-18 Git 提交记录

| Commit | 说明 |
|--------|------|
| `f84e41c` | ci: 修复 GitHub Pages 部署 - 加回 environment 配置 |
| `3beef6c` | ci: 修复 GitHub Pages 部署 - 加回 environment 配置 |
| `cd151a2` | ci: 添加 GitHub Pages 部署工作流 |
| `7d9030e` | feat: 前端改为纯只读 - 移除所有写入 UI（添加心愿、真买、记一笔、编辑、删除） |
| `7574e34` | fix: Wishes.vue 导入 computed 并修复 formatMoney 空值处理 |
| `88d9ebe` | M3: PWA 前端完成 - Vue3+Vite+PWA+ECharts，5页面+浮动导航+黑白风 |
| `e8bb101` | chore: 添加 Python pycache 到 .gitignore |
| `39c8a74` | M1: 数据层实施完成 - GitHub API 客户端、数据模型、存储逻辑、单元测试 |
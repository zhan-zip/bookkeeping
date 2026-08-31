# Bookkeeping

> 通过聊天机器人自然语言记账，手机端只读看板的记账系统。

## 它是什么

一个记账系统，记账通过 **MCP 服务** 完成——自然语言直接记账（"午饭25"、"买键盘499购物"），手机端 PWA 只读查看数据。数据存储在 GitHub 私有仓库的 JSON 文件中（通过 GitHub API 读写），无需自建数据库。

## 核心功能

- **自然语言记账**：通过 MCP server 暴露记账工具，可接入聊天机器人/Agent。支持中文自然语言解析（"午饭25"→ 吃饭 25 元、"收到生活费2000"→ 收入）
- **AA 记账**：垫付/回款冲抵，实际支出计算准确
- **心愿储蓄**：心理账户机制，想买的先记下，真买时一键转正式支出
- **预算管理**：按分类设置预算限额（如零食 200/月），超支提醒
- **月报生成**：月度收支汇总 + 分类占比 + 分享图片一键生成
- **手机 PWA**：可安装到主屏，离线可用，黑白风格简洁 UI

## 架构

```
QQ 机器人 / Agent  ←→  MCP server（记账工具）  ←→  GitHub API  ←→  data/expenses.json（唯一数据源）
        ↕
PWA（手机只读）  ←→  GitHub API（只读 token）
```

- 数据源是 GitHub 私有仓库的 JSON 文件，通过 GitHub Contents API 读写（带 sha 防冲突）
- 记账走 MCP（写 token），查看走 PWA（只读 token），权限分离
- 已部署到 GitHub Pages

## 技术栈

| 层 | 技术 |
|----|------|
| MCP server | Python + fastmcp（10 个记账工具） |
| 存储 | GitHub 私有仓库 JSON（GitHub Contents API） |
| 前端 | Vue 3 + Vite + PWA + ECharts |
| 部署 | GitHub Actions → GitHub Pages |

## 快速开始

```bash
git clone https://github.com/zhan-zip/bookkeeping.git
cd bookkeeping
```

**MCP server（记账端）**

```bash
cd server
pip install -r requirements.txt
# 配置 .env（GitHub Token + 仓库）
# 启动 MCP server
python -m src.mcp_server
```

**前端（查看端）**

```bash
cd client
npm install
npm run dev
```

## 在线演示

https://zhan-zip.github.io/bookkeeping/

## 目录结构

```
server/     Python MCP server（storage 业务逻辑 + mcp_server 工具）
client/     Vue3 + Vite PWA 前端（总览/流水/心愿/月报/预算/设置）
data/       GitHub 仓库中的 JSON 数据文件（expenses.json / wishlist.json）
tests/      单元测试
.github/    GitHub Actions 部署工作流
```

## 进度

- ✅ 数据层（GitHub API 读写 + 冲突处理 + 余额计算）
- ✅ MCP server（10 个记账工具 + 自然语言解析）
- ✅ PWA 前端（5 页面 + 黑白风 + 离线缓存）
- ✅ 优化（预算管理 + 月报分享图）
- ✅ 已上线

# Bookkeeping MCP Server 接入文档（给 QQ 机器人项目）

> 本文档面向 **开发 QQ 机器人记账功能的 AI 项目（以下简称"机器人项目"）**，旨在让对接方读完即可完成接入。
> 文档描述的是**当前线上代码的真实行为**，所有字段、枚举、报错信息均与 `server/src/` 下代码逐一核对，不包含文档作者的主观设想。
>
> - 创建：2026-08-31
> - 关联代码：`server/src/mcp_server.py`、`server/src/storage.py`、`server/src/github_client.py`、`server/src/models.py`
> - 机器人项目若需改动 MCP 侧代码，请与账本项目 owner 确认后再改，勿擅自修改仓库数据文件。

---

## 0. 一页速览（给对接方 AI 的摘要）

- 这是一个 **MCP Server（stdio 模式）**，用 `fastmcp` 实现，把"记账系统"的能力暴露成 13 个工具。
- 机器人项目把它作为 MCP Server 挂载到 agent 上，**用户对机器人说一句话，agent 通过调用这些工具完成记账/查询**。
- 数据**不是**存在机器人这边，而是存在 GitHub 仓库的 JSON 文件里（`data/expenses.json` / `data/wishlist.json`），MCP server 内部通过 GitHub Contents API 读写，**机器人项目不需要也不应该直接操作数据文件**。
- 机器人侧拿到的是**写权限 token**（存 `.env`），与手机 PWA 不同。**token 只放服务器环境变量，绝不进入机器人对话上下文或前端。**
- **记账主流程**（这是设计好的正确用法，务必遵守）：
  1. 用户说"午饭25"这类自然语言
  2. agent 先调 `parse_expense_text_tool` 把文本解析成结构化数据
  3. agent 拿到 `{amount, category, note, expense_type}` 后调 `add_expense_tool` 落库
  4. 不要跳过解析直接猜分类

---

## 1. 部署与启动

### 1.1 环境要求
- Python 3.10+（当前在 3.13 下运行）
- 依赖见 `server/requirements.txt`：`fastmcp>=0.4.0`、`requests>=2.31.0`、`python-dotenv>=1.0.0`、`pytest>=8.0`、`pytest-asyncio>=0.23.0`

### 1.2 安装
```bash
pip install -r server/requirements.txt
```

### 1.3 配置环境变量（`server/.env`）
参考 `server/.env.example`：

```bash
GITHUB_OWNER=zhan-zip
GITHUB_REPO=bookkeeping
GITHUB_TOKEN=your_personal_access_token_here   # 需要该仓库的 contents:write 权限
EXPENSES_PATH=data/expenses.json
WISHLIST_PATH=data/wishlist.json
MONTHLY_ALLOWANCE=2000
```

- `GITHUB_TOKEN` 是**写权限**的 Personal Access Token，只对 `zhan-zip/bookkeeping` 仓库授权即可（最小权限原则）。
- 首次部署若数据文件不存在，调用 `init_repo` 相关逻辑（或直接跑一次 `python server/src/main.py`）会创建文件。

### 1.4 启动方式（stdio）
```bash
python server/src/mcp_server.py
```
- 该进程从 stdin 读 JSON-RPC，向 stdout 写响应（`mcp_server.py` 末尾 `mcp.run()` 即 stdio 模式）。
- **不要在前台跑此命令做交互测试**，它要由 MCP 客户端（agent 宿主）以子进程方式拉起。

### 1.5 接入 agent 的配置示意（以标准 MCP 配置为例）
```json
{
  "mcpServers": {
    "bookkeeping": {
      "command": "python",
      "args": ["path/to/bookkeeping/server/src/mcp_server.py"],
      "env": {
        "GITHUB_OWNER": "zhan-zip",
        "GITHUB_REPO": "bookkeeping",
        "GITHUB_TOKEN": "<写权限token>",
        "EXPENSES_PATH": "data/expenses.json",
        "WISHLIST_PATH": "data/wishlist.json",
        "MONTHLY_ALLOWANCE": "2000"
      }
    }
  }
}
```
> 注意：不同 agent 宿主配置格式可能不同，请以宿主文档为准。核心是把 `mcp_server.py` 作为 stdio 子进程拉起，并把 `.env` 里的变量传给它。

---

## 2. 数据模型（理解返回值/参数的前提）

### 2.1 收支记录（`expenses.json` 中每一条）
```json
{
  "id": "20260801-143025-7",
  "type": "expense",
  "amount": 25.5,
  "category": "吃饭",
  "note": "午饭",
  "date": "2026-08-01",
  "balance_after": 1974.5,
  "created_at": "2026-08-01T12:15:00"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一，格式 `YYYYMMDD-HHMMSS-f`（微秒截断共 17 位，见 `models.py:88`），由系统生成，**不要自己构造** |
| `type` | string | 收支类型，见 2.3 |
| `amount` | number | 金额，正数 |
| `category` | string | 分类，见 2.2 |
| `note` | string | 备注（自然语言描述） |
| `date` | string | 日期，`YYYY-MM-DD` |
| `balance_after` | number | **当时余额**，由系统自动计算，**不要传** |
| `created_at` | string | ISO 时间，由系统生成，**不要传** |

### 2.2 分类白名单（8 类，`models.py:76`）
`技术`、`学习`、`吃饭`、`零食`、`购物`、`生活`、`社交`、`出行`

- **支出/AA 类型的 category 必须在这 8 类里**，否则 `add_expense` 会抛错。
- **`income`（收入）类型不校验分类**，此时 category 可以传 `生活费` 等非白名单值。

### 2.3 收支类型（4 种，`models.py:7`）
| type | 含义 | 对余额的影响 | 说明 |
|---|---|---|---|
| `expense` | 支出 | 减少余额 | 日常消费 |
| `income` | 收入 | 增加余额 | 生活费、兼职、红包等真收入 |
| `aa_advance` | AA 垫付 | 减少余额 | 帮朋友垫付的钱 |
| `aa_return` | AA 回款 | 增加余额 | 朋友还回来的垫付款 |

> **AA 回款不算真收入**。在月报统计里，回款只用来冲抵支出（见 3.2 的公式），不要把它当成收入。

### 2.4 心愿清单（`wishlist.json` 中每一条）
```json
{
  "id": "20260801-203000-1",
  "name": "机械键盘",
  "price": 499,
  "created_at": "2026-08-01T20:00:00"
}
```
只存"东西名 + 价格"，**没有"买没买"状态**。真买时用 `buy_wish_tool` 转移成支出并从清单消失。

---

## 3. 业务规则（agent 必须理解，否则会用错）

### 3.1 余额的计算
- 余额 = 累计（收入 + AA 回款）− 累计（支出 + AA 垫付）。
- **balance_after 全部由系统自动重算**（`storage.py:61`），agent 不需要也不应该传这个字段。
- 你调用 `add_expense_tool` 后，返回里会带 `balance_after`，那是当时的余额，**不要拿去当"剩余可用钱"直接回答用户**，涉及余额判断建议再查一次汇总。

### 3.2 月报/汇总里的"实际"与"名义"
- 名义收入 = 所有 income + aa_return
- 名义支出 = 所有 expense + aa_advance
- **实际收入 = 名义收入 − AA 回款总额**
- **实际支出 = 名义支出 − AA 回款总额**
- 余额 = 实际收入 − 实际支出
- 当月"存下"= max(0, 余额)；"花超"= max(0, −余额)

### 3.3 期初生活费
- 每月需要一笔 `type=income, category=生活费, note=期初生活费` 的记录作为期初余额。
- 通过 `ensure_allowance_tool` 确保本月存在，不要手工拼。

### 3.4 金额与备注
- 金额为正数，保留两位小数。
- 备注最长截断到 50 字符（`mcp_server.py` 解析时限制），不要传超长文本。

---

## 4. 工具完整契约（13 个）

> 说明：以下"错误"是指 MCP 调用层面返回的错误结构/异常，agent 应识别到并调整输入，而不是当成系统故障。
> 所有工具名以 `_tool` 结尾，**这是封装层**；原始 `storage.py` 函数名不要直接调。

### 4.1 `parse_expense_text_tool` —— 自然语言解析（记账第一步）
- **入参**
  - `text: string`：自然语言记账文本，如 `"午饭25"`、`"买键盘499购物"`、`"收到生活费2000"`
- **返回**（结构化解析结果，供确认）
  ```json
  {
    "amount": 25,
    "category": "吃饭",
    "note": "午饭",
    "expense_type": "expense",
    "confidence": 0.8
  }
  ```
  - `confidence`：分类是否命中的置信度（命中关键词 0.8，否则 0.5）。
- **错误**：空文本 → `{"error": "空文本"}`；未识别到金额 → `{"error": "未识别到金额"}`
- **用途**：先解析、给 agent 结构化结果，**再由 agent 调 `add_expense_tool` 落库**。

### 4.2 `add_expense_tool` —— 记一笔（核心写操作）
- **入参**
  - `amount: number`：金额（必填）
  - `category: string`（必填）：支出类须在 8 类白名单；`expense_type=income` 时不校验
  - `note: string`（必填）：备注
  - `expense_type: string`：`expense` / `income` / `aa_advance` / `aa_return`，默认 `expense`
  - `date: string`：`YYYY-MM-DD`，可选，默认今天
- **返回**
  ```json
  {
    "id": "20260831-121530-3",
    "type": "expense",
    "amount": 25,
    "category": "吃饭",
    "note": "午饭",
    "date": "2026-08-31",
    "balance_after": 1975
  }
  ```
- **错误**：`category` 不在白名单且非 income → `{"error": "无效分类: xxx，可选: ['技术', '学习', '吃饭', '零食', '购物', '生活', '社交', '出行']"}`
- **注意**：这是写操作，**每次调用都会真实写入 GitHub 仓库**。agent 应先确认用户意图再调用，避免重复记账。

### 4.3 `ensure_allowance_tool` —— 确保本月有期初生活费
- **入参**：无
- **返回**
  ```json
  { "created": true, "message": "已添加期初生活费 2000.0" }
  ```
  - `created: true` 表示刚创建；`false` 表示本月已有。金额是 `MONTHLY_ALLOWANCE` 环境变量的值（浮点数格式化进文本）。
- **用途**：每月首次记账前可先调用确保期初存在（幂等，可安全重复调用）。

### 4.4 `get_summary_tool` —— 汇总查询
- **入参**
  - `period: string`：`today` / `week` / `month`（默认 `month`）。**`year` 尚未实现**：传入除 `today`/`week`/`month` 之外的任何值都会返回错误（见下）。
- **返回**（以 `month` 为例）
  ```json
  {
    "period": "month",
    "month": "2026-08",
    "allowance": 2000,
    "actual_income": 2000,
    "actual_expense": 500,
    "balance": 1500,
    "saved": 1500,
    "overspent": 0
  }
  ```
  - `today` / `week` 返回的是流水列表 + 总支出，格式不同，注意区分。
  - **`week` 实现限制**：week 是先取最近 50 条流水再按周过滤，一周内流水超过 50 条时会漏算。
- **错误**：`period` 不是 `today`/`week`/`month` → `{"error": "period 必须是 today/week/month/year"}`（错误文案本身仍提及 year，属于代码层面的已知瑕疵，行为以本描述为准）

### 4.5 `get_category_stats_tool` —— 分类占比
- **入参**：无
- **返回**：形如 `{"吃饭": 100, "零食": 50}`，键为分类，值为本月该分类支出合计（只包含有支出的分类）。**只统计支出/AA 垫付，不含收入**。

### 4.6 `get_recent_tool` —— 最近流水
- **入参**
  - `limit: int`：返回条数，默认 20
- **返回**：记录数组（按日期倒序），元素结构见 2.1。

### 4.7 `get_budget_status_tool` —— 预算状态
- **入参**
  - `budgets: object`：`{分类: 限额}`，如 `{"零食": 200, "购物": 500}`
- **返回**
  ```json
  {
    "零食": { "limit": 200, "spent": 150, "remaining": 50, "overspent": false }
  }
  ```
- **注意**：预算本身不持久化在数据文件，是 agent 调用时传入的；**预算的"标准答案"在手机 PWA 的 localStorage 里**，机器人侧如需一致需自行维护/确认，本 MCP 只做纯计算。

### 4.8 `add_wish_tool` —— 心愿清单加一条
- **入参**
  - `name: string`（必填）
  - `price: number`（必填）
- **返回**
  ```json
  { "id": "20260831-203000-4", "name": "机械键盘", "price": 499, "created_at": "2026-08-31T20:30:00" }
  ```

### 4.9 `buy_wish_tool` —— 心愿真买（转移成支出）
- **入参**
  - `wish_id: string`（必填）：心愿的 id
  - `category: string`（必填）：转成的支出分类（须在白名单）
  - `note: string`（可选）：备注，默认 `心愿购买: <name>`
- **返回**
  ```json
  {
    "wish": { "id": "...", "name": "...", "price": 499 },
    "expense": { "id": "...", "amount": 499, "category": "购物", "note": "心愿购买: 机械键盘", "balance_after": 1500 }
  }
  ```
- **效果**：从心愿清单移除该条，并新增一笔支出记录。**注意：这是两步写操作**（删心愿 + 加支出），如果中间出错可能不同步，agent 应在确认用户"真的买了"后再调用。
- **错误**：wish_id 不存在 → `{"error": "心愿不存在: <id>"}`

### 4.10 `get_monthly_report_tool` —— 月报（原始数据）
- **入参**：无
- **返回**：包含 `month`、`allowance`、`nominal_income`、`nominal_expense`、`aa_advance`、`aa_return`、`actual_income`、`actual_expense`、`final_balance`、`saved_this_month`、`overspent`、`wishlist_count`、`wishlist_total`、`category_stats`、`records`（本月全部流水）。
- **用途**：给用户生成"月报"类回答/推送的最全数据源。

### 4.11 `push_monthly_report_tool` —— 月报推送文本（格式化输出）
- **入参**
  - `month: string`（可选）：目标月份 `YYYY-MM`，默认当前月。
- **返回**
  ```json
  {
    "month": "2026-09",
    "text": "📊 2026-09 月报\n─ ─ ─\n💰 期初生活费：¥2000.00\n📥 名义收入：¥2000.00  （含 AA 回款 ¥0.00）\n📤 名义支出：¥500.00  （含 AA 垫付 ¥0.00）\n📈 实际收入：¥2000.00\n📉 实际支出：¥500.00\n\n🟢 期末余额：¥1500.00\n💾 本月存下：¥1500.00\n\n🎁 心愿清单：2 件 共 ¥1298.00\n\n📂 分类支出：\n  吃饭：¥300.00 (60.0%)\n  零食：¥200.00 (40.0%)\n\n📝 近期流水（最近 10 笔）：\n  💸 2026-09-01 -¥25.00 [吃饭] 午饭 余额¥1975.00\n  ...",
    "raw": { /* 同 get_monthly_report_tool 的完整返回 */ }
  }
  ```
- **文本内容说明**（`_format_monthly_report_text` 生成）：
  1. **标题 + 月份**
  2. **收支概览**：期初生活费、名义/实际收入支出、AA 垫付回款单独标注
  3. **结余**：期末余额、本月存下/超支（带颜色表情）
  4. **心愿清单**：数量 + 总价
  5. **分类占比**：按金额降序，显示金额与占实际支出百分比
  6. **近期流水**：最近 10 笔（倒序），含类型表情、金额、分类、备注、时点余额
- **用途**：机器人直接把 `text` 推送给用户（QQ 群/私聊），无需再组装。如需自定义格式，用 `raw` 字段二次处理。
- **错误**：月份格式不对 → 返回当前月报（容错处理，不报错）。

### 4.12 `list_categories_tool` —— 获取所有分类
- **入参**：无
- **返回**：`{"categories": ["技术", "学习", "吃饭", "零食", "购物", "生活", "社交", "出行", ...]}`（动态读取 `data/categories.json`，内置 8 类为默认值）。
- **用途**：机器人在记账前可先调用获取当前可用分类，避免硬编码。

### 4.13 `add_category_tool` —— 新增分类
- **入参**
  - `name: string`：分类名称（1-10 字符，去空）。
- **返回**：
  ```json
  { "added": true, "category": "新分类", "categories": ["技术", "学习", "吃饭", "零食", "购物", "生活", "社交", "出行", "新分类"] }
  ```
- **错误**：空名/超长/已存在 → `{"error": "..."}`

### 4.14 `delete_category_tool` —— 删除分类
- **入参**
  - `name: string`：要删除的分类名。
- **返回**：
  ```json
  { "deleted": true, "category": "旧分类", "categories": ["技术", "学习", "吃饭", "零食", "购物", "生活", "社交", "出行"] }
  ```
- **保护机制**：内置 8 类（技术/学习/吃饭/零食/购物/生活/社交/出行）**不可删除**，尝试删除返回 `{"error": "内置分类不可删除: xxx"}`。
- **注意**：已有流水引用的分类若被删，后续记账时会校验不过；建议先确认无引用再删。

### 4.15 `delete_expense_tool` —— 删除流水（按 id）
- **入参**
  - `expense_id: string`：流水记录的 id（来自 `get_recent_tool` 或 `add_expense_tool` 的返回）。
- **返回**：
  ```json
  {
    "deleted": true,
    "record": { "id": "...", "type": "expense", "amount": 25, "category": "吃饭", "note": "午饭", "date": "2026-08-31" }
  }
  ```
- **错误**：id 不存在 → `{"error": "流水不存在: xxx"}`
- **效果**：删除后**所有后续记录的 balance_after 自动重算**。

### 4.16 `update_expense_tool` —— 修改流水（按 id，部分字段可选）
- **入参**
  - `expense_id: string`：流水 id
  - `amount: number`（可选）
  - `category: string`（可选，支出/AA 须在白名单，income 不校验）
  - `note: string`（可选）
  - `date: string`（可选，`YYYY-MM-DD`）
  - `expense_type: string`（可选，`expense/income/aa_advance/aa_return`）
- **返回**：更新后完整记录（含 `balance_after`）。
- **错误**：id 不存在、字段无效、无任何修改字段 → 返回对应 error。
- **效果**：改动金额/类型/日期会触发**全量余额重算**。

### 4.17 `ensure_allowance_tool` —— 确保本月有期初生活费

### 5.1 记账（核心路径）
1. 用户说"午饭25"
2. agent 调 `parse_expense_text_tool("午饭25")` → 得到 `{amount:25, category:"吃饭", note:"午饭", expense_type:"expense"}`
3. agent 调 `add_expense_tool(amount=25, category="吃饭", note="午饭")`
4. 把返回的 `balance_after` 作为"当前余额"告知用户，如"已记一笔 25 元（吃饭），当前余额 xxx"

### 5.2 用户问"我还有多少钱"
1. 调 `get_summary_tool(period="month")`
2. 用 `balance` 回答（是"余额/可花额度"，不是名义收入）

### 5.3 用户问"上个月/这个月花了多少"
- 用 `get_monthly_report_tool` 的 `actual_expense` 回答，不要用 `nominal_expense`（那是含 AA 垫付的口径）

### 5.4 用户说"想买个 xx"
- 用 `add_wish_tool` 加入心愿清单，**不要**直接记支出

### 5.5 用户说"xx 我买了"
- 先 `get_recent_tool` 或让用户确认是哪个心愿，再 `buy_wish_tool`

### 5.6 预算相关
- 用户问"零食预算还有多少" → 需要知道预算值。可询问用户，或让用户先在 PWA 设置。MCP 只做给定预算下的计算（`get_budget_status_tool`），不自带存储。

---

## 6. 边界与注意事项（避免踩坑）

1. **token 权限**：机器人侧必须用写权限 token；读 token（PWA 那种）写不进去。
2. **写操作要确认**：`add_expense_tool` / `buy_wish_tool` 会真实改 GitHub 仓库，agent 在意图不明确时先询问用户。
3. **不要在 agent 层"猜"分类再落库**：请走 `parse_expense_text_tool`。虽然它也不是 100% 准（有 confidence），但比模型直接编一个分类更稳，且能让你看到解析结果再决定。
4. **id 由系统生成**：任何工具都不接受外部传入 id，不要自己构造。
5. **余额别乱答**：`balance_after` 是单笔时点值，回答"还剩多少"时优先用 `get_summary_tool` 的 `balance`。
6. **并发/一致性**：数据文件是 GitHub 上的单文件，读写有 sha 防冲突。agent 不要并发发多个写请求，顺序写即可。
7. **数据位置**：所有数据在仓库 `data/*.json`，**不要**在别处另存一份"真相"，否则两端数据会不一致。

---

## 7. 遇到问题时排查顺序

1. MCP server 能否正常拉起？检查 Python 环境、`fastmcp` 是否安装、`server/.env` 的 token 是否有效。
2. 调用工具报错是"参数错误"还是"连接失败"？
   - 参数错误（如无效分类）：按本文档 4 的契约调整入参。
   - 连接/认证失败：检查 `GITHUB_TOKEN` 权限（需要该仓库 contents:write）。
3. 检查线上数据文件是否被改坏（`data/expenses.json` 是否仍是合法 JSON 数组）。若被改坏，可用 git 历史恢复。

---

## 8. 附：代码变更需知的（给后续维护者）

> 本节是给"要改 MCP 代码"的人看的，机器人项目对接时一般不需要。

- 工具都是 `@mcp.tool()` 装饰器包装的**薄封装**，直接调 `storage.py` 的同名函数，没有重复逻辑。新增工具时照此模式。
- 分类白名单在 `models.py:76` 的 `CATEGORIES`，改分类要同时改这里（以及前端、`mcp_server.py` 的关键词表，注意别漏）。
- 收支类型的枚举在 `models.py:7` 的 `ExpenseType`。
- 余额重算逻辑在 `storage.py:61` `_recompute_all_balances`，改记账规则时要保证它仍然正确。
- `mcp_server.py` 里的 `CATEGORY_KEYWORDS` / `EXPENSE_TYPE_KEYWORDS` 是自然语言解析用的关键词表，新增分类/关键词需同步维护。

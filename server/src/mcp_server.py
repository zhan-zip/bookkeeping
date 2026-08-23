import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from src.storage import (
    add_expense, get_recent, get_today, get_month_summary,
    get_category_stats, get_budget_status, add_wish, get_wishlist,
    buy_wish, get_monthly_report, ensure_monthly_allowance,
)
from src.models import ExpenseType, CATEGORIES

mcp = FastMCP("Bookkeeping MCP Server")

CATEGORY_KEYWORDS = {
    "技术": ["技术", "服务器", "域名", "订阅", "api", "ai", "cursor", "chatgpt", "github", "云"],
    "学习": ["书", "教材", "笔记本", "笔", "课", "学习", "考试", "证书"],
    "吃饭": ["饭", "午饭", "晚饭", "早饭", "早餐", "午餐", "晚餐", "食堂", "餐厅", "面", "米饭", "菜"],
    "零食": ["奶茶", "咖啡", "饮料", "零食", "薯片", "巧克力", "糖", "冰淇淋", "蛋糕", "甜品"],
    "购物": ["买", "淘宝", "京东", "拼多多", "键盘", "鼠标", "耳机", "手机", "电脑", "衣服", "鞋", "包"],
    "生活": ["洗发水", "沐浴露", "牙膏", "纸巾", "洗衣液", "生活用品", "日用品"],
    "社交": ["聚餐", "ktv", "电影", "游戏", "朋友", "社交", "请客", "红包"],
    "出行": ["打车", "滴滴", "高铁", "飞机", "地铁", "公交", "油", "停车", "出行"],
}

EXPENSE_TYPE_KEYWORDS = {
    "income": ["收入", "工资", "生活费", "兼职", "奖金", "红包", "转账"],
    "aa_advance": ["垫付", "帮付", "先付", "aa垫付"],
    "aa_return": ["回款", "还钱", "报销", "aa回款", "收到"],
}

def parse_expense_text(text: str) -> dict:
    """解析自然语言记账文本，返回结构化数据"""
    text = text.strip()
    if not text:
        return {"error": "空文本"}
    
    # 提取金额
    amount_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if not amount_match:
        return {"error": "未识别到金额"}
    amount = float(amount_match.group(1))
    
    # 去除金额部分，剩余文本用于推断分类和备注
    remaining = text[:amount_match.start()] + text[amount_match.end():]
    remaining = re.sub(r'[元块钱]', '', remaining).strip()
    
    # 判断收支类型
    expense_type = "expense"
    for etype, keywords in EXPENSE_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            expense_type = etype
            break
    
    # 推断分类
    category = "吃饭"  # 默认
    matched_cat = None
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            matched_cat = cat
            break
    if matched_cat:
        category = matched_cat
    elif expense_type == "income":
        category = "生活费"
    
    # 生成备注（去除金额、分类关键词后的剩余文本）
    note = remaining
    if not note:
        note = "记账"
    
    # 处理特殊格式："买键盘499购物" -> note="键盘", category="购物"
    buy_match = re.match(r'买(.+?)(\d+(?:\.\d+)?)(.*)', text)
    if buy_match:
        item = buy_match.group(1).strip()
        category = "购物"
        note = item or "购物"
    
    return {
        "amount": amount,
        "category": category,
        "note": note[:50],  # 限制长度
        "expense_type": expense_type,
        "confidence": 0.8 if matched_cat else 0.5,
    }


@mcp.tool()
def parse_expense_text_tool(text: str) -> dict:
    """解析自然语言记账文本，返回结构化数据供确认
    
    Args:
        text: 自然语言文本，如 "午饭25"、"买键盘499购物"、"收到生活费2000"
    
    Returns:
        解析结果：amount, category, note, expense_type, confidence
    """
    return parse_expense_text(text)


@mcp.tool()
def add_expense_tool(
    amount: float,
    category: str,
    note: str,
    expense_type: str = "expense",
    date: str = None,
) -> dict:
    """记一笔流水（自动计算 balance_after）
    
    Args:
        amount: 金额
        category: 分类（技术/学习/吃饭/零食/购物/生活/社交/出行）
        note: 备注
        expense_type: 类型 expense/income/aa_advance/aa_return
        date: 日期 YYYY-MM-DD，默认今天
    """
    if category not in CATEGORIES and expense_type != "income":
        return {"error": f"无效分类: {category}，可选: {CATEGORIES}"}
    
    record = add_expense(amount, category, note, expense_type, date)
    return {
        "id": record.id,
        "type": record.type,
        "amount": record.amount,
        "category": record.category,
        "note": record.note,
        "date": record.date,
        "balance_after": record.balance_after,
    }


@mcp.tool()
def get_summary_tool(period: str = "month") -> dict:
    """获取汇总数据
    
    Args:
        period: today/week/month/year
    """
    if period == "today":
        records = get_today()
        total = sum(r.amount for r in records if r.type in ("expense", "aa_advance"))
        return {"period": "today", "count": len(records), "total_expense": total, "records": [r.to_dict() for r in records]}
    
    elif period == "month":
        summary = get_month_summary()
        return {
            "period": "month",
            "month": summary["month"],
            "allowance": summary["allowance"],
            "actual_income": summary["actual_income"],
            "actual_expense": summary["actual_expense"],
            "balance": summary["balance"],
            "saved": summary["saved"],
            "overspent": summary["overspent"],
        }
    
    elif period == "week":
        records = get_recent(50)
        week_records = [r for r in records if r.date >= get_week_start()]
        total = sum(r.amount for r in week_records if r.type in ("expense", "aa_advance"))
        return {"period": "week", "count": len(week_records), "total_expense": total, "records": [r.to_dict() for r in week_records]}
    
    else:
        return {"error": "period 必须是 today/week/month/year"}


def get_week_start() -> str:
    from datetime import datetime, timedelta
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    return start.strftime("%Y-%m-%d")


@mcp.tool()
def get_category_stats_tool() -> dict:
    """获取本月分类占比"""
    return get_category_stats()


@mcp.tool()
def get_recent_tool(limit: int = 20) -> list:
    """获取最近 N 笔流水"""
    records = get_recent(limit)
    return [r.to_dict() for r in records]


@mcp.tool()
def get_budget_status_tool(budgets: dict = None) -> dict:
    """获取预算状态
    
    Args:
        budgets: {分类: 预算限额}，如 {"零食": 200, "购物": 500}
    """
    if budgets is None:
        budgets = {}
    return get_budget_status(budgets)


@mcp.tool()
def add_wish_tool(name: str, price: float) -> dict:
    """心愿清单加一条"""
    item = add_wish(name, price)
    return {"id": item.id, "name": item.name, "price": item.price, "created_at": item.created_at}


@mcp.tool()
def buy_wish_tool(wish_id: str, category: str, note: str = None) -> dict:
    """心愿真买 → 转正式支出 + 从清单消失"""
    expense, wish = buy_wish(wish_id, category, note)
    return {
        "wish": {"id": wish.id, "name": wish.name, "price": wish.price},
        "expense": {
            "id": expense.id,
            "amount": expense.amount,
            "category": expense.category,
            "note": expense.note,
            "balance_after": expense.balance_after,
        },
    }


@mcp.tool()
def get_monthly_report_tool() -> dict:
    """获取月报数据（含所有细节）"""
    return get_monthly_report()


@mcp.tool()
def ensure_allowance_tool() -> dict:
    """确保本月有期初生活费记录"""
    created, msg = ensure_monthly_allowance()
    return {"created": created, "message": msg}


if __name__ == "__main__":
    mcp.run()
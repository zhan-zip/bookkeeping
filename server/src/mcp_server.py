import os
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
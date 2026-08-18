import os
import json
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from .github_client import get_file, put_file, ensure_file_exists
from .models import (
    ExpenseRecord, WishItem, ExpenseType, CATEGORIES,
    generate_id, now_iso, today_str, is_month_end
)

EXPENSES_PATH = os.getenv("EXPENSES_PATH", "data/expenses.json")
WISHLIST_PATH = os.getenv("WISHLIST_PATH", "data/wishlist.json")
MONTHLY_ALLOWANCE = float(os.getenv("MONTHLY_ALLOWANCE", "2000"))


DEFAULT_EXPENSES = "[]"
DEFAULT_WISHLIST = "[]"


def _load_expenses() -> Tuple[List[ExpenseRecord], Optional[str]]:
    data = get_file(EXPENSES_PATH)
    if not data:
        return [], None
    records = [ExpenseRecord.from_dict(r) for r in json.loads(data["content"])]
    return records, data["sha"]


def _save_expenses(records: List[ExpenseRecord], sha: Optional[str], message: str) -> str:
    content = json.dumps([r.to_dict() for r in records], ensure_ascii=False, indent=2)
    result = put_file(EXPENSES_PATH, content, sha, message)
    return result["content"]["sha"]


def _load_wishlist() -> Tuple[List[WishItem], Optional[str]]:
    data = get_file(WISHLIST_PATH)
    if not data:
        return [], None
    items = [WishItem.from_dict(w) for w in json.loads(data["content"])]
    return items, data["sha"]


def _save_wishlist(items: List[WishItem], sha: Optional[str], message: str) -> str:
    content = json.dumps([w.to_dict() for w in items], ensure_ascii=False, indent=2)
    result = put_file(WISHLIST_PATH, content, sha, message)
    return result["content"]["sha"]


def _calculate_balance(records: List[ExpenseRecord], up_to_index: int) -> float:
    """计算到某条记录为止的余额"""
    balance = 0.0
    for i, r in enumerate(records):
        if i > up_to_index:
            break
        if r.type in ("income", "aa_return"):
            balance += r.amount
        else:
            balance -= r.amount
    return balance


def _recompute_all_balances(records: List[ExpenseRecord]) -> List[ExpenseRecord]:
    """重新计算所有记录的 balance_after"""
    balance = 0.0
    for r in records:
        if r.type in ("income", "aa_return"):
            balance += r.amount
        else:
            balance -= r.amount
        r.balance_after = round(balance, 2)
    return records


def _get_month_start(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(day=1).strftime("%Y-%m-%d")


def _get_month_end(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    last_day = (dt.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return last_day.strftime("%Y-%m-%d")


def _filter_by_month(records: List[ExpenseRecord], date_str: str) -> List[ExpenseRecord]:
    month_start = _get_month_start(date_str)
    month_end = _get_month_end(date_str)
    return [r for r in records if month_start <= r.date <= month_end]


def _get_monthly_allowance_record(records: List[ExpenseRecord], date_str: str) -> Optional[ExpenseRecord]:
    """找到本月的生活费收入记录（期初录入的那一笔）"""
    month_records = _filter_by_month(records, date_str)
    for r in month_records:
        if r.type == "income" and r.category == "生活费" and r.note == "期初生活费":
            return r
    return None


def ensure_monthly_allowance(date_str: str = None) -> Tuple[bool, str]:
    """确保本月有期初生活费记录，没有则创建"""
    date_str = date_str or today_str()
    records, sha = _load_expenses()
    
    existing = _get_monthly_allowance_record(records, date_str)
    if existing:
        return False, "本月已有期初生活费记录"
    
    new_record = ExpenseRecord(
        id=generate_id(),
        type="income",
        amount=MONTHLY_ALLOWANCE,
        category="生活费",
        note="期初生活费",
        date=_get_month_start(date_str),
        balance_after=0,
        created_at=now_iso(),
    )
    records.append(new_record)
    records = _recompute_all_balances(records)
    _save_expenses(records, sha, f"添加本月期初生活费 {MONTHLY_ALLOWANCE}")
    return True, f"已添加期初生活费 {MONTHLY_ALLOWANCE}"


def add_expense(
    amount: float,
    category: str,
    note: str,
    expense_type: ExpenseType = "expense",
    date: str = None,
) -> ExpenseRecord:
    """记一笔流水（自动计算 balance_after）"""
    date = date or today_str()
    records, sha = _load_expenses()
    
    if category not in CATEGORIES and expense_type != "income":
        raise ValueError(f"无效分类: {category}，可选: {CATEGORIES}")
    
    records.sort(key=lambda r: (r.date, r.created_at))
    balance_before = _calculate_balance(records, len(records) - 1)
    
    if expense_type in ("income", "aa_return"):
        balance_after = balance_before + amount
    else:
        balance_after = balance_before - amount
    
    record = ExpenseRecord(
        id=generate_id(),
        type=expense_type,
        amount=round(amount, 2),
        category=category,
        note=note,
        date=date,
        balance_after=round(balance_after, 2),
        created_at=now_iso(),
    )
    records.append(record)
    records = _recompute_all_balances(records)
    _save_expenses(records, sha, f"记{expense_type}: {note} {amount} ({category})")
    return record


def get_recent(limit: int = 20) -> List[ExpenseRecord]:
    records, _ = _load_expenses()
    records.sort(key=lambda r: (r.date, r.created_at), reverse=True)
    return records[:limit]


def get_today() -> List[ExpenseRecord]:
    today = today_str()
    records, _ = _load_expenses()
    return [r for r in records if r.date == today]


def get_month_summary(date_str: str = None) -> dict:
    date_str = date_str or today_str()
    records, _ = _load_expenses()
    month_records = _filter_by_month(records, date_str)
    
    total_income = sum(r.amount for r in month_records if r.type in ("income", "aa_return"))
    total_expense = sum(r.amount for r in month_records if r.type in ("expense", "aa_advance"))
    aa_advance = sum(r.amount for r in month_records if r.type == "aa_advance")
    aa_return = sum(r.amount for r in month_records if r.type == "aa_return")
    
    actual_income = total_income - aa_return
    actual_expense = total_expense - aa_return
    balance = actual_income - actual_expense
    
    allowance_record = _get_monthly_allowance_record(records, date_str)
    allowance = allowance_record.amount if allowance_record else 0
    
    return {
        "month": date_str[:7],
        "allowance": allowance,
        "nominal_income": total_income,
        "nominal_expense": total_expense,
        "aa_advance": aa_advance,
        "aa_return": aa_return,
        "actual_income": actual_income,
        "actual_expense": actual_expense,
        "balance": balance,
        "saved": max(0, balance),
        "overspent": max(0, -balance),
        "records": month_records,
    }


def get_category_stats(date_str: str = None) -> dict:
    date_str = date_str or today_str()
    records, _ = _load_expenses()
    month_records = _filter_by_month(records, date_str)
    
    stats = {cat: 0.0 for cat in CATEGORIES}
    for r in month_records:
        if r.type in ("expense", "aa_advance"):
            stats[r.category] = stats.get(r.category, 0) + r.amount
    
    return {k: round(v, 2) for k, v in stats.items() if v > 0}


def get_budget_status(budgets: dict, date_str: str = None) -> dict:
    """budgets: {category: limit}"""
    stats = get_category_stats(date_str)
    result = {}
    for cat, limit in budgets.items():
        spent = stats.get(cat, 0)
        result[cat] = {
            "limit": limit,
            "spent": spent,
            "remaining": round(limit - spent, 2),
            "overspent": spent > limit,
        }
    return result


def add_wish(name: str, price: float) -> WishItem:
    items, sha = _load_wishlist()
    item = WishItem(
        id=generate_id(),
        name=name,
        price=round(price, 2),
        created_at=now_iso(),
    )
    items.append(item)
    _save_wishlist(items, sha, f"心愿清单加入: {name} {price}")
    return item


def get_wishlist() -> List[WishItem]:
    items, _ = _load_wishlist()
    return items


def buy_wish(wish_id: str, category: str, note: str = None) -> Tuple[ExpenseRecord, WishItem]:
    """心愿真买 → 转正式支出 + 从清单消失"""
    items, wish_sha = _load_wishlist()
    wish = next((w for w in items if w.id == wish_id), None)
    if not wish:
        raise ValueError(f"心愿不存在: {wish_id}")
    
    items = [w for w in items if w.id != wish_id]
    _save_wishlist(items, wish_sha, f"心愿真买移除: {wish.name}")
    
    expense = add_expense(
        amount=wish.price,
        category=category,
        note=note or f"心愿购买: {wish.name}",
        expense_type="expense",
    )
    return expense, wish


def get_monthly_report(date_str: str = None) -> dict:
    date_str = date_str or today_str()
    records, _ = _load_expenses()
    month_records = _filter_by_month(records, date_str)
    
    summary = get_month_summary(date_str)
    category_stats = get_category_stats(date_str)
    wishlist = get_wishlist()
    
    wish_total = sum(w.price for w in wishlist)
    wish_count = len(wishlist)
    
    last_record = month_records[-1] if month_records else None
    final_balance = last_record.balance_after if last_record else 0
    
    return {
        "month": date_str[:7],
        "allowance": summary["allowance"],
        "nominal_income": summary["nominal_income"],
        "nominal_expense": summary["nominal_expense"],
        "aa_advance": summary["aa_advance"],
        "aa_return": summary["aa_return"],
        "actual_income": summary["actual_income"],
        "actual_expense": summary["actual_expense"],
        "final_balance": final_balance,
        "saved_this_month": max(0, final_balance),
        "overspent": max(0, -final_balance),
        "wishlist_count": wish_count,
        "wishlist_total": wish_total,
        "category_stats": category_stats,
        "records": [r.to_dict() for r in month_records],
    }


def delete_expense(expense_id: str) -> bool:
    records, sha = _load_expenses()
    original_len = len(records)
    records = [r for r in records if r.id != expense_id]
    if len(records) == original_len:
        return False
    records = _recompute_all_balances(records)
    _save_expenses(records, sha, f"删除流水: {expense_id}")
    return True


def update_expense(expense_id: str, **kwargs) -> Optional[ExpenseRecord]:
    records, sha = _load_expenses()
    for i, r in enumerate(records):
        if r.id == expense_id:
            for k, v in kwargs.items():
                if hasattr(r, k):
                    setattr(r, k, v)
            records = _recompute_all_balances(records)
            _save_expenses(records, sha, f"修改流水: {expense_id}")
            return records[i]
    return None


def init_repo() -> dict:
    """初始化仓库数据文件"""
    ensure_file_exists(EXPENSES_PATH, DEFAULT_EXPENSES, "初始化 expenses.json")
    ensure_file_exists(WISHLIST_PATH, DEFAULT_WISHLIST, "初始化 wishlist.json")
    return {"status": "initialized"}
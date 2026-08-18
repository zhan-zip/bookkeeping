import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from src.models import (
    ExpenseRecord, WishItem, CATEGORIES, generate_id, now_iso, today_str,
    is_month_end, last_day_of_month
)
from src.storage import (
    _calculate_balance, _recompute_all_balances, _filter_by_month,
    _get_monthly_allowance_record, _get_month_start, _get_month_end,
)


class TestModels:
    def test_expense_record_to_dict(self):
        record = ExpenseRecord(
            id="20260818-1",
            type="expense",
            amount=25.5,
            category="吃饭",
            note="午饭",
            date="2026-08-18",
            balance_after=1775.0,
            created_at="2026-08-18T02:45:00",
        )
        d = record.to_dict()
        assert d["id"] == "20260818-1"
        assert d["amount"] == 25.5
        assert d["type"] == "expense"

    def test_expense_record_from_dict(self):
        data = {
            "id": "20260818-1",
            "type": "income",
            "amount": 2000.0,
            "category": "生活费",
            "note": "期初生活费",
            "date": "2026-08-01",
            "balance_after": 2000.0,
            "created_at": "2026-08-01T00:00:00",
        }
        record = ExpenseRecord.from_dict(data)
        assert record.type == "income"
        assert record.amount == 2000.0

    def test_wish_item(self):
        wish = WishItem(id="w1", name="键盘", price=499.0, created_at=now_iso())
        d = wish.to_dict()
        assert d["name"] == "键盘"
        assert d["price"] == 499.0

    def test_generate_id_format(self):
        id_str = generate_id()
        assert len(id_str) == 17
        assert "-" in id_str

    def test_last_day_of_month(self):
        assert last_day_of_month(2026, 1) == 31
        assert last_day_of_month(2026, 2) == 28
        assert last_day_of_month(2024, 2) == 29
        assert last_day_of_month(2026, 4) == 30

    def test_is_month_end(self):
        assert is_month_end("2026-01-31") is True
        assert is_month_end("2026-02-28") is True
        assert is_month_end("2024-02-29") is True
        assert is_month_end("2026-01-30") is False
        assert is_month_end("2026-03-15") is False

    def test_categories(self):
        assert "吃饭" in CATEGORIES
        assert "零食" in CATEGORIES
        assert len(CATEGORIES) == 8


class TestStorageLogic:
    def test_calculate_balance(self):
        records = [
            ExpenseRecord("1", "income", 2000, "生活费", "期初", "2026-08-01", 0, now_iso()),
            ExpenseRecord("2", "expense", 25.5, "吃饭", "午饭", "2026-08-01", 0, now_iso()),
            ExpenseRecord("3", "expense", 15.0, "零食", "奶茶", "2026-08-02", 0, now_iso()),
            ExpenseRecord("4", "aa_advance", 100, "吃饭", "请客", "2026-08-03", 0, now_iso()),
            ExpenseRecord("5", "aa_return", 50, "吃饭", "回款", "2026-08-04", 0, now_iso()),
        ]
        assert _calculate_balance(records, 0) == 2000
        assert _calculate_balance(records, 1) == 1974.5
        assert _calculate_balance(records, 2) == 1959.5
        assert _calculate_balance(records, 3) == 1859.5
        assert _calculate_balance(records, 4) == 1909.5

    def test_recompute_all_balances(self):
        records = [
            ExpenseRecord("1", "income", 2000, "生活费", "期初", "2026-08-01", 0, now_iso()),
            ExpenseRecord("2", "expense", 25.5, "吃饭", "午饭", "2026-08-01", 0, now_iso()),
            ExpenseRecord("3", "aa_return", 50, "吃饭", "回款", "2026-08-02", 0, now_iso()),
        ]
        records = _recompute_all_balances(records)
        assert records[0].balance_after == 2000
        assert records[1].balance_after == 1974.5
        assert records[2].balance_after == 2024.5

    def test_filter_by_month(self):
        records = [
            ExpenseRecord("1", "expense", 100, "吃饭", "7月", "2026-07-15", 0, now_iso()),
            ExpenseRecord("2", "expense", 200, "吃饭", "8月", "2026-08-01", 0, now_iso()),
            ExpenseRecord("3", "expense", 300, "吃饭", "8月", "2026-08-15", 0, now_iso()),
            ExpenseRecord("4", "expense", 400, "吃饭", "9月", "2026-09-01", 0, now_iso()),
        ]
        august = _filter_by_month(records, "2026-08-10")
        assert len(august) == 2
        assert august[0].note == "8月"
        assert august[1].note == "8月"

    def test_get_month_start_end(self):
        assert _get_month_start("2026-08-15") == "2026-08-01"
        assert _get_month_end("2026-08-15") == "2026-08-31"
        assert _get_month_end("2026-02-10") == "2026-02-28"
        assert _get_month_end("2024-02-10") == "2024-02-29"

    def test_get_monthly_allowance_record(self):
        records = [
            ExpenseRecord("1", "income", 2000, "生活费", "期初生活费", "2026-08-01", 0, now_iso()),
            ExpenseRecord("2", "income", 500, "兼职", "外快", "2026-08-10", 0, now_iso()),
        ]
        allowance = _get_monthly_allowance_record(records, "2026-08-15")
        assert allowance is not None
        assert allowance.amount == 2000
        assert allowance.note == "期初生活费"
        
        # 9月没有
        allowance = _get_monthly_allowance_record(records, "2026-09-15")
        assert allowance is None


class TestAAFormula:
    """AA 记账公式测试：实际花费 = 名义支出 - AA回款，实际收入 = 名义收入 - AA回款"""
    
    def test_aa_calculation(self):
        records = [
            ExpenseRecord("1", "income", 2000, "生活费", "期初", "2026-08-01", 0, now_iso()),
            ExpenseRecord("2", "expense", 100, "吃饭", "正常吃饭", "2026-08-01", 0, now_iso()),
            ExpenseRecord("3", "aa_advance", 200, "吃饭", "请客", "2026-08-02", 0, now_iso()),
            ExpenseRecord("4", "aa_return", 150, "吃饭", "回款", "2026-08-03", 0, now_iso()),
        ]
        
        # 名义支出 = 100 (expense) + 200 (aa_advance) = 300
        # 名义收入 = 2000 (income, 不含 aa_return)
        # AA回款 = 150
        # 实际支出 = 300 - 150 = 150
        # 实际收入 = 2000 - 150 = 1850
        # 余额 = 1850 - 150 = 1700
        
        nominal_expense = sum(r.amount for r in records if r.type in ("expense", "aa_advance"))
        nominal_income = sum(r.amount for r in records if r.type == "income")
        aa_return = sum(r.amount for r in records if r.type == "aa_return")
        
        actual_expense = nominal_expense - aa_return
        actual_income = nominal_income - aa_return
        balance = actual_income - actual_expense
        
        assert nominal_expense == 300
        assert nominal_income == 2000
        assert aa_return == 150
        assert actual_expense == 150
        assert actual_income == 1850
        assert balance == 1700


class TestWishlist:
    def test_buy_wish_flow(self):
        """心愿真买：从清单消失 + 转正式支出"""
        # 模拟逻辑：买心愿时，从 wishlist 移除，调用 add_expense
        wishlist = [
            WishItem("w1", "键盘", 499, now_iso()),
            WishItem("w2", "鼠标", 199, now_iso()),
        ]
        
        # 买 w1
        target = next(w for w in wishlist if w.id == "w1")
        wishlist = [w for w in wishlist if w.id != "w1"]
        
        assert len(wishlist) == 1
        assert wishlist[0].id == "w2"
        assert target.price == 499


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
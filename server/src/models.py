from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Literal, Optional
import json


ExpenseType = Literal["expense", "income", "aa_advance", "aa_return"]


@dataclass
class ExpenseRecord:
    id: str
    type: ExpenseType
    amount: float
    category: str
    note: str
    date: str
    balance_after: float
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExpenseRecord":
        return cls(**data)


@dataclass
class WishItem:
    id: str
    name: str
    price: float
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WishItem":
        return cls(**data)


EXPENSES_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "type", "amount", "category", "note", "date", "balance_after", "created_at"],
        "properties": {
            "id": {"type": "string"},
            "type": {"type": "string", "enum": ["expense", "income", "aa_advance", "aa_return"]},
            "amount": {"type": "number"},
            "category": {"type": "string"},
            "note": {"type": "string"},
            "date": {"type": "string", "format": "date"},
            "balance_after": {"type": "number"},
            "created_at": {"type": "string", "format": "date-time"},
        },
    },
}

WISHLIST_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "name", "price", "created_at"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "price": {"type": "number"},
            "created_at": {"type": "string", "format": "date-time"},
        },
    },
}

CATEGORIES = [
    "技术",
    "学习",
    "吃饭",
    "零食",
    "购物",
    "生活",
    "社交",
    "出行",
]

def generate_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:17]

def now_iso() -> str:
    return datetime.now().isoformat()

def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def last_day_of_month(year: int, month: int) -> int:
    """返回该月最后一天的日期数（处理闰年）"""
    import calendar
    return calendar.monthrange(year, month)[1]

def is_month_end(date_str: str) -> bool:
    """判断是否为该月最后一天"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    last_day = last_day_of_month(dt.year, dt.month)
    return dt.day == last_day
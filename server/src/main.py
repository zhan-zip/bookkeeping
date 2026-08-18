import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github_client import get_file, put_file, ensure_file_exists
from src.storage import (
    init_repo, add_expense, get_recent, get_today, get_month_summary,
    get_category_stats, add_wish, get_wishlist, buy_wish, get_monthly_report,
    ensure_monthly_allowance,
)
from src.models import CATEGORIES


def test_github_connection():
    print("=== 测试 GitHub 连接 ===")
    try:
        # 尝试获取文件（不存在也返回 None 不报错）
        data = get_file("data/expenses.json")
        print(f"GitHub 连接正常，expenses.json 存在: {data is not None}")
        return True
    except Exception as e:
        print(f"GitHub 连接失败: {e}")
        return False


def test_init():
    print("\n=== 测试初始化 ===")
    try:
        result = init_repo()
        print(f"初始化结果: {result}")
        return True
    except Exception as e:
        print(f"初始化失败: {e}")
        return False


def test_add_expense():
    print("\n=== 测试记账 ===")
    try:
        # 先确保有期初生活费
        ensure_monthly_allowance()
        
        # 记几笔支出
        r1 = add_expense(25.5, "吃饭", "午饭", "expense")
        print(f"记账1: {r1.note} {r1.amount} 余额: {r1.balance_after}")
        
        r2 = add_expense(15.0, "零食", "奶茶", "expense")
        print(f"记账2: {r2.note} {r2.amount} 余额: {r2.balance_after}")
        
        # 记一笔 AA 垫付
        r3 = add_expense(100.0, "吃饭", "请客吃饭", "aa_advance")
        print(f"AA垫付: {r3.note} {r3.amount} 余额: {r3.balance_after}")
        
        # 记 AA 回款
        r4 = add_expense(50.0, "吃饭", "朋友回款", "aa_return")
        print(f"AA回款: {r4.note} {r4.amount} 余额: {r4.balance_after}")
        
        return True
    except Exception as e:
        print(f"记账测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query():
    print("\n=== 测试查询 ===")
    try:
        print("最近 5 笔:")
        for r in get_recent(5):
            print(f"  {r.date} {r.type} {r.amount} {r.category} {r.note} 余额:{r.balance_after}")
        
        print("\n今日流水:")
        for r in get_today():
            print(f"  {r.type} {r.amount} {r.category} {r.note}")
        
        print("\n本月汇总:")
        summary = get_month_summary()
        for k, v in summary.items():
            if k != "records":
                print(f"  {k}: {v}")
        
        print("\n分类统计:")
        stats = get_category_stats()
        for cat, amt in stats.items():
            print(f"  {cat}: {amt}")
        
        return True
    except Exception as e:
        print(f"查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wishlist():
    print("\n=== 测试心愿清单 ===")
    try:
        w1 = add_wish("机械键盘", 499.0)
        print(f"加入心愿: {w1.name} {w1.price}")
        
        w2 = add_wish("Kindle", 799.0)
        print(f"加入心愿: {w2.name} {w2.price}")
        
        print("\n当前心愿清单:")
        for w in get_wishlist():
            print(f"  {w.name} {w.price}")
        
        # 真买一个
        expense, wish = buy_wish(w1.id, "购物", "心愿购买")
        print(f"\n真买: {wish.name} -> 转支出 {expense.amount} 余额: {expense.balance_after}")
        
        print("\n剩余心愿:")
        for w in get_wishlist():
            print(f"  {w.name} {w.price}")
        
        return True
    except Exception as e:
        print(f"心愿清单测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monthly_report():
    print("\n=== 测试月报 ===")
    try:
        report = get_monthly_report()
        print(f"月份: {report['month']}")
        print(f"生活费: {report['allowance']}")
        print(f"名义收入: {report['nominal_income']}")
        print(f"名义支出: {report['nominal_expense']}")
        print(f"AA垫付: {report['aa_advance']}")
        print(f"AA回款: {report['aa_return']}")
        print(f"实际收入: {report['actual_income']}")
        print(f"实际支出: {report['actual_expense']}")
        print(f"期末余额: {report['final_balance']}")
        print(f"本月存下: {report['saved_this_month']}")
        print(f"花超金额: {report['overspent']}")
        print(f"心愿清单: {report['wishlist_count']} 件 共 {report['wishlist_total']}")
        print("分类占比:")
        for cat, amt in report['category_stats'].items():
            print(f"  {cat}: {amt}")
        return True
    except Exception as e:
        print(f"月报测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_delete_update():
    print("\n=== 测试删改 ===")
    try:
        # 记一笔新的用于测试删改
        r = add_expense(99.0, "技术", "测试删改", "expense")
        print(f"新增测试记录: {r.id} {r.amount}")
        
        # 修改
        updated = update_expense(r.id, amount=88.0, note="修改后")
        print(f"修改后: {updated.amount} {updated.note} 余额: {updated.balance_after}")
        
        # 删除
        deleted = delete_expense(r.id)
        print(f"删除结果: {deleted}")
        
        return True
    except Exception as e:
        print(f"删改测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始 M1 数据层测试\n")
    
    # 需要先配置 .env 才能运行
    if not os.getenv("GITHUB_TOKEN"):
        print("⚠️  请先配置 server/.env 填入 GITHUB_TOKEN")
        sys.exit(1)
    
    ok = True
    ok &= test_github_connection()
    ok &= test_init()
    ok &= test_add_expense()
    ok &= test_query()
    ok &= test_wishlist()
    ok &= test_monthly_report()
    ok &= test_delete_update()
    
    print("\n" + "=" * 40)
    if ok:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
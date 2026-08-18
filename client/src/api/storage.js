import { getFile, putFile, ensureFile } from './github'

const EXPENSES_PATH = 'data/expenses.json'
const WISHLIST_PATH = 'data/wishlist.json'

function generateId() {
  return new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 17)
}

function nowIso() {
  return new Date().toISOString()
}

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function lastDayOfMonth(year, month) {
  return new Date(year, month, 0).getDate()
}

function isMonthEnd(dateStr) {
  const d = new Date(dateStr)
  return d.getDate() === lastDayOfMonth(d.getFullYear(), d.getMonth() + 1)
}

function getMonthStart(dateStr) {
  const d = new Date(dateStr)
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10)
}

function getMonthEnd(dateStr) {
  const d = new Date(dateStr)
  const end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
  return end.toISOString().slice(0, 10)
}

async function loadExpenses() {
  const data = await getFile(EXPENSES_PATH)
  return data ? data.content : []
}

async function saveExpenses(records, sha, message) {
  return putFile(EXPENSES_PATH, records, sha, message)
}

async function loadWishlist() {
  const data = await getFile(WISHLIST_PATH)
  return data ? data.content : []
}

async function saveWishlist(items, sha, message) {
  return putFile(WISHLIST_PATH, items, sha, message)
}

function computeBalance(records, upToIndex) {
  let balance = 0
  for (let i = 0; i <= upToIndex && i < records.length; i++) {
    const r = records[i]
    if (r.type === 'income' || r.type === 'aa_return') balance += r.amount
    else balance -= r.amount
  }
  return Math.round(balance * 100) / 100
}

function recomputeAllBalances(records) {
  let balance = 0
  for (const r of records) {
    if (r.type === 'income' || r.type === 'aa_return') balance += r.amount
    else balance -= r.amount
    r.balance_after = Math.round(balance * 100) / 100
  }
  return records
}

function filterByMonth(records, dateStr) {
  const start = getMonthStart(dateStr)
  const end = getMonthEnd(dateStr)
  return records.filter(r => r.date >= start && r.date <= end)
}

function getAllowanceRecord(records, dateStr) {
  const monthRecords = filterByMonth(records, dateStr)
  return monthRecords.find(r => r.type === 'income' && r.category === '生活费' && r.note === '期初生活费')
}

export const CATEGORIES = [
  '技术', '学习', '吃饭', '零食', '购物', '生活', '社交', '出行'
]

export async function ensureMonthlyAllowance() {
  const records = await loadExpenses()
  const today = todayStr()
  const existing = getAllowanceRecord(records, today)
  if (existing) return { created: false, message: '本月已有期初生活费记录' }
  
  const allowance = 2000
  const newRecord = {
    id: generateId(),
    type: 'income',
    amount: allowance,
    category: '生活费',
    note: '期初生活费',
    date: getMonthStart(today),
    balance_after: 0,
    created_at: nowIso(),
  }
  records.push(newRecord)
  const updated = recomputeAllBalances(records)
  await saveExpenses(updated, null, `添加本月期初生活费 ${allowance}`)
  return { created: true, message: `已添加期初生活费 ${allowance}` }
}

export async function addExpense(amount, category, note, expenseType = 'expense', date = null) {
  date = date || todayStr()
  const records = await loadExpenses()
  
  if (!CATEGORIES.includes(category) && expenseType !== 'income') {
    throw new Error(`无效分类: ${category}，可选: ${CATEGORIES.join(', ')}`)
  }
  
  records.sort((a, b) => (a.date + a.created_at).localeCompare(b.date + b.created_at))
  const balanceBefore = computeBalance(records, records.length - 1)
  const balanceAfter = (expenseType === 'income' || expenseType === 'aa_return')
    ? balanceBefore + amount
    : balanceBefore - amount
  
  const record = {
    id: generateId(),
    type: expenseType,
    amount: Math.round(amount * 100) / 100,
    category,
    note,
    date,
    balance_after: Math.round(balanceAfter * 100) / 100,
    created_at: nowIso(),
  }
  records.push(record)
  const updated = recomputeAllBalances(records)
  await saveExpenses(updated, null, `记${expenseType}: ${note} ${amount} (${category})`)
  return record
}

export async function getRecent(limit = 20) {
  const records = await loadExpenses()
  records.sort((a, b) => (b.date + b.created_at).localeCompare(a.date + a.created_at))
  return records.slice(0, limit)
}

export async function getToday() {
  const records = await loadExpenses()
  const today = todayStr()
  return records.filter(r => r.date === today)
}

export async function getMonthSummary(dateStr = null) {
  dateStr = dateStr || todayStr()
  const records = await loadExpenses()
  const monthRecords = filterByMonth(records, dateStr)
  
  const totalIncome = monthRecords.filter(r => r.type === 'income' || r.type === 'aa_return')
    .reduce((sum, r) => sum + r.amount, 0)
  const totalExpense = monthRecords.filter(r => r.type === 'expense' || r.type === 'aa_advance')
    .reduce((sum, r) => sum + r.amount, 0)
  const aaAdvance = monthRecords.filter(r => r.type === 'aa_advance')
    .reduce((sum, r) => sum + r.amount, 0)
  const aaReturn = monthRecords.filter(r => r.type === 'aa_return')
    .reduce((sum, r) => sum + r.amount, 0)
  
  const actualIncome = totalIncome - aaReturn
  const actualExpense = totalExpense - aaReturn
  const balance = actualIncome - actualExpense
  
  const allowanceRecord = getAllowanceRecord(records, dateStr)
  const allowance = allowanceRecord ? allowanceRecord.amount : 0
  
  return {
    month: dateStr.slice(0, 7),
    allowance,
    nominal_income: totalIncome,
    nominal_expense: totalExpense,
    aa_advance: aaAdvance,
    aa_return: aaReturn,
    actual_income: actualIncome,
    actual_expense: actualExpense,
    balance,
    saved: Math.max(0, balance),
    overspent: Math.max(0, -balance),
    records: monthRecords,
  }
}

export async function getCategoryStats(dateStr = null) {
  dateStr = dateStr || todayStr()
  const records = await loadExpenses()
  const monthRecords = filterByMonth(records, dateStr)
  
  const stats = {}
  for (const cat of CATEGORIES) stats[cat] = 0
  for (const r of monthRecords) {
    if (r.type === 'expense' || r.type === 'aa_advance') {
      stats[r.category] = (stats[r.category] || 0) + r.amount
    }
  }
  const result = {}
  for (const [cat, amt] of Object.entries(stats)) {
    if (amt > 0) result[cat] = Math.round(amt * 100) / 100
  }
  return result
}

export async function getBudgetStatus(budgets = {}) {
  const stats = await getCategoryStats()
  const result = {}
  for (const [cat, limit] of Object.entries(budgets)) {
    const spent = stats[cat] || 0
    result[cat] = {
      limit,
      spent,
      remaining: Math.round((limit - spent) * 100) / 100,
      overspent: spent > limit,
    }
  }
  return result
}

export async function addWish(name, price) {
  const items = await loadWishlist()
  const item = {
    id: generateId(),
    name,
    price: Math.round(price * 100) / 100,
    created_at: nowIso(),
  }
  items.push(item)
  await saveWishlist(items, null, `心愿清单加入: ${name} ${price}`)
  return item
}

export async function getWishlist() {
  return loadWishlist()
}

export async function buyWish(wishId, category, note = null) {
  const items = await loadWishlist()
  const idx = items.findIndex(w => w.id === wishId)
  if (idx === -1) throw new Error(`心愿不存在: ${wishId}`)
  
  const wish = items[idx]
  items.splice(idx, 1)
  await saveWishlist(items, null, `心愿真买移除: ${wish.name}`)
  
  const expense = await addExpense(
    wish.price,
    category,
    note || `心愿购买: ${wish.name}`,
    'expense'
  )
  return { expense, wish }
}

export async function getMonthlyReport(dateStr = null) {
  dateStr = dateStr || todayStr()
  const records = await loadExpenses()
  const monthRecords = filterByMonth(records, dateStr)
  const summary = await getMonthSummary(dateStr)
  const categoryStats = await getCategoryStats(dateStr)
  const wishlist = await loadWishlist()
  
  const wishTotal = wishlist.reduce((sum, w) => sum + w.price, 0)
  const wishCount = wishlist.length
  
  const lastRecord = monthRecords[monthRecords.length - 1]
  const finalBalance = lastRecord ? lastRecord.balance_after : 0
  
  return {
    month: dateStr.slice(0, 7),
    allowance: summary.allowance,
    nominal_income: summary.nominal_income,
    nominal_expense: summary.nominal_expense,
    aa_advance: summary.aa_advance,
    aa_return: summary.aa_return,
    actual_income: summary.actual_income,
    actual_expense: summary.actual_expense,
    final_balance: finalBalance,
    saved_this_month: Math.max(0, finalBalance),
    overspent: Math.max(0, -finalBalance),
    wishlist_count: wishCount,
    wishlist_total: wishTotal,
    category_stats: categoryStats,
    records: monthRecords,
  }
}

export async function deleteExpense(expenseId) {
  const records = await loadExpenses()
  const idx = records.findIndex(r => r.id === expenseId)
  if (idx === -1) return false
  records.splice(idx, 1)
  const updated = recomputeAllBalances(records)
  await saveExpenses(updated, null, `删除流水: ${expenseId}`)
  return true
}

export async function updateExpense(expenseId, updates) {
  const records = await loadExpenses()
  const idx = records.findIndex(r => r.id === expenseId)
  if (idx === -1) return null
  records[idx] = { ...records[idx], ...updates }
  const updated = recomputeAllBalances(records)
  await saveExpenses(updated, null, `修改流水: ${expenseId}`)
  return updated[idx]
}

export async function initRepo() {
  await ensureFile(EXPENSES_PATH, [], '初始化 expenses.json')
  await ensureFile(WISHLIST_PATH, [], '初始化 wishlist.json')
  return { status: 'initialized' }
}
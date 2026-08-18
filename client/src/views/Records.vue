<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { useRouter } from 'vue-router'
import { format } from 'date-fns'

const store = useAppStore()
const router = useRouter()
const showModal = ref(false)
const editingRecord = ref(null)
const form = ref({ amount: '', category: '吃饭', note: '', type: 'expense', date: '' })
const loading = ref(false)

const today = new Date().toISOString().slice(0, 10)

onMounted(() => {
  if (store.isAuthenticated) {
    store.fetchAll()
  }
  form.value.date = today
})

const records = computed(() => store.expenses)

const groupedRecords = computed(() => {
  const groups = {}
  for (const r of records.value) {
    if (!groups[r.date]) groups[r.date] = []
    groups[r.date].push(r)
  }
  return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a))
})

function openAddRecord() {
  editingRecord.value = null
  form.value = { amount: '', category: '吃饭', note: '', type: 'expense', date: today }
  showModal.value = true
}

function openEditRecord(record) {
  editingRecord.value = record
  form.value = {
    amount: record.amount,
    category: record.category,
    note: record.note,
    type: record.type,
    date: record.date,
  }
  showModal.value = true
}

async function submitForm() {
  if (!form.value.amount || !form.value.note) return
  loading.value = true
  try {
    if (editingRecord.value) {
      await store.updateExpense(editingRecord.value.id, {
        amount: Number(form.value.amount),
        category: form.value.category,
        note: form.value.note,
        type: form.value.type,
        date: form.value.date,
      })
    } else {
      await store.addExpense(
        Number(form.value.amount),
        form.value.category,
        form.value.note,
        form.value.type,
        form.value.date
      )
    }
    showModal.value = false
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

async function deleteRecord(id) {
  if (!confirm('确定删除这笔记录？')) return
  try {
    await store.deleteExpense(id)
  } catch (e) {
    alert(e.message)
  }
}

function formatMoney(n) {
  return '¥' + n.toFixed(2)
}

function getTypeBadge(type) {
  const map = {
    expense: 'badge-expense',
    income: 'badge-income',
    aa_advance: 'badge-aa',
    aa_return: 'badge-aa',
  }
  const label = { expense: '支出', income: '收入', aa_advance: 'AA垫付', aa_return: 'AA回款' }
  return `<span class="badge ${map[type]}">${label[type]}</span>`
}

function getAmountClass(type) {
  return type === 'income' || type === 'aa_return' ? 'income' : 'expense'
}
</script>

<template>
  <div class="container">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <h1 class="page-title" style="margin:0;">流水记录</h1>
      <button class="btn btn-primary" @click="openAddRecord" style="padding:8px 16px; font-size:14px; min-height:40px;">+ 记一笔</button>
    </div>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding:40px 20px;">
      <p style="margin-bottom:16px; color:var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else-if="records.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
      <p>暂无记录，点击右下角 + 添加第一笔</p>
    </div>
    
    <div v-else>
      <div v-for="[date, dayRecords] in groupedRecords" :key="date" class="card">
        <div class="card-title" style="margin-bottom:12px;">{{ date }}</div>
        <div v-for="r in dayRecords" :key="r.id" class="record-item">
          <div class="record-main" @click="openEditRecord(r)" style="cursor:pointer; flex:1;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="record-category">{{ r.category }}</span>
              <span v-html="getTypeBadge(r.type)"></span>
            </div>
            <span class="record-note">{{ r.note }}</span>
          </div>
          <div style="text-align:right;">
            <div class="record-amount" :class="getAmountClass(r.type)">
              {{ r.type === 'income' || r.type === 'aa_return' ? '+' : '-' }}{{ formatMoney(r.amount) }}
            </div>
            <div class="record-balance">余额 {{ formatMoney(r.balance_after) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Modal -->
    <div class="modal" :class="{ open: showModal }" @click.self="showModal = false">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <h2 style="margin-bottom:20px;">{{ editingRecord ? '修改记录' : '新增记录' }}</h2>
        
        <div class="form-group">
          <label class="form-label">类型</label>
          <select v-model="form.type" class="form-input" style="padding:12px;">
            <option value="expense">支出</option>
            <option value="income">收入</option>
            <option value="aa_advance">AA垫付</option>
            <option value="aa_return">AA回款</option>
          </select>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">金额</label>
            <input type="number" step="0.01" v-model="form.amount" class="form-input" placeholder="0.00" inputmode="decimal">
          </div>
          <div class="form-group">
            <label class="form-label">日期</label>
            <input type="date" v-model="form.date" class="form-input" max="today">
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">分类</label>
          <select v-model="form.category" class="form-input" style="padding:12px;">
            <option v-for="c in ['技术','学习','吃饭','零食','购物','生活','社交','出行']" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">备注</label>
          <input type="text" v-model="form.note" class="form-input" placeholder="午饭、奶茶等" maxlength="50">
        </div>
        
        <div style="display:flex; gap:12px; margin-top:24px;">
          <button class="btn btn-secondary" style="flex:1;" @click="showModal = false">取消</button>
          <button class="btn btn-primary" style="flex:1;" @click="submitForm" :disabled="loading">
            {{ loading ? '保存中...' : '保存' }}
          </button>
        </div>
        
        <div v-if="editingRecord" style="margin-top:12px; text-align:center;">
          <button class="btn btn-danger" style="width:100%;" @click="deleteRecord(editingRecord.id)">删除这笔记录</button>
        </div>
      </div>
    </div>
  </div>
</template>
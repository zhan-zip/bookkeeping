<script setup>
import { onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()

onMounted(() => {
  if (store.isAuthenticated) {
    store.fetchAll()
  }
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
    <h1 class="page-title">流水记录</h1>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding:40px 20px;">
      <p style="margin-bottom:16px; color:var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else-if="records.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
      <p>暂无记录</p>
      <p style="font-size:12px; margin-top:8px; color:var(--color-text-secondary);">记账请在 QQ 机器人中说「午饭 25」</p>
    </div>
    
    <div v-else>
      <div v-for="[date, dayRecords] in groupedRecords" :key="date" class="card">
        <div class="card-title" style="margin-bottom:12px;">{{ date }}</div>
        <div v-for="r in dayRecords" :key="r.id" class="record-item">
          <div class="record-main" style="flex:1;">
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
  </div>
</template>
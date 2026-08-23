<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const editingBudget = ref(null)
const form = ref({ category: '零食', limit: '' })
const saving = ref(false)

const CATEGORIES = [
  '技术', '学习', '吃饭', '零食', '购物', '生活', '社交', '出行'
]

onMounted(() => {
  if (store.isAuthenticated) {
    store.fetchAll()
  }
})

const budgetStatus = computed(() => store.budgetStatus || {})

const budgets = computed(() => {
  // 从 budgetStatus 中提取预算设置
  const result = {}
  for (const [cat, status] of Object.entries(budgetStatus.value)) {
    if (status.limit > 0) {
      result[cat] = status.limit
    }
  }
  return result
})

async function saveBudget() {
  if (!form.value.limit || form.value.limit <= 0) return
  saving.value = true
  try {
    store.setBudget(form.value.category, Number(form.value.limit))
    editingBudget.value = null
    form.value = { category: '零食', limit: '' }
  } catch (e) {
    alert(e.message)
  } finally {
    saving.value = false
  }
}

async function removeBudget(category) {
  if (!confirm(`删除 ${category} 的预算设置？`)) return
  try {
    store.removeBudget(category)
  } catch (e) {
    alert(e.message)
  }
}

function editBudget(category, limit) {
  editingBudget.value = category
  form.value = { category, limit }
}

function formatMoney(n) {
  return '¥' + (n || 0).toFixed(2)
}

function getStatusClass(status) {
  if (!status || !status.limit) return ''
  return status.overspent ? 'overspent' : (status.remaining < status.limit * 0.2 ? 'warning' : '')
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">预算设置</h1>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding:40px 20px;">
      <p style="margin-bottom:16px; color:var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">设置分类预算</div>
        <div v-if="editingBudget" style="margin-bottom:12px; padding:12px; background:var(--color-divider); border-radius:var(--radius-sm);">
          <div style="font-size:13px; color:var(--color-text-secondary);">正在编辑：{{ editingBudget }}</div>
        </div>
        <div class="form-row" style="gap:8px;">
          <div class="form-group" style="flex:1;">
            <label class="form-label">分类</label>
            <select v-model="form.category" class="form-input" style="padding:12px;">
              <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="form-group" style="flex:1;">
            <label class="form-label">预算限额</label>
            <input type="number" step="0.01" v-model="form.limit" class="form-input" placeholder="0.00" inputmode="decimal">
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <button v-if="editingBudget" class="btn btn-secondary" style="flex:1;" @click="editingBudget = null; form.category='零食'; form.limit=''">取消</button>
          <button class="btn btn-primary" style="flex:1;" @click="saveBudget" :disabled="saving || !form.limit">
            {{ saving ? '保存中...' : (editingBudget ? '更新' : '添加') }}
          </button>
        </div>
      </div>
      
      <div class="card">
        <div class="card-title">当前预算状态</div>
        <div v-if="Object.keys(budgetStatus).length === 0" class="empty-state" style="padding:24px;">
          <p>暂无预算设置</p>
          <p style="font-size:12px; margin-top:8px; color:var(--color-text-secondary);">点击上方添加分类预算，超支会在总览和月报中标红提醒</p>
        </div>
        <div v-else>
          <div v-for="(status, cat) in budgetStatus" :key="cat" class="budget-item" style="padding:12px 0; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--color-divider);">
            <div style="display:flex; flex-direction:column; gap:4px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="record-category">{{ cat }}</span>
                <span class="badge" :class="['badge-budget', getStatusClass(status)]">{{ formatMoney(status.limit) }}</span>
              </div>
              <div style="font-size:12px; color:var(--color-text-secondary);">
                已用 {{ formatMoney(status.spent) }} / 剩余 {{ formatMoney(status.remaining) }}
                <span v-if="status.overspent" style="color:var(--color-negative); margin-left:8px;">⚠ 超支</span>
              </div>
            </div>
            <div style="display:flex; gap:8px;">
              <button class="btn btn-ghost" style="padding:6px 10px; font-size:12px;" @click="editBudget(cat, status.limit)">编辑</button>
              <button class="btn btn-ghost" style="padding:6px 10px; font-size:12px; color:var(--color-negative);" @click="removeBudget(cat)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.badge-budget {
  background: #f0f0f0;
  color: var(--color-text);
}
.badge-budget.warning {
  background: #fff3e0;
  color: #e65100;
}
.badge-budget.overspent {
  background: #fdeaea;
  color: var(--color-negative);
}
</style>
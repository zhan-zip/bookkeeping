<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import * as echarts from 'echarts'

const store = useAppStore()
const chartDom = ref(null)
const chart = ref(null)

const summary = computed(() => store.monthlySummary)

onMounted(() => {
  if (!store.isAuthenticated) return
  initChart()
  store.fetchAll()
})

function initChart() {
  if (!chartDom.value) return
  chart.value = echarts.init(chartDom.value)
  updateChart()
  window.addEventListener('resize', () => chart.value?.resize())
}

function updateChart() {
  if (!chart.value || !summary.value) return
  const stats = store.categoryStats
  const data = Object.entries(stats).map(([name, value]) => ({ name, value }))
  
  chart.value.setOption({
    color: ['#000', '#333', '#666', '#999', '#ccc', '#ddd', '#eee', '#f5f5f5'],
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c} ({d}%)',
      backgroundColor: '#fff',
      borderColor: '#e0e0e0',
      borderWidth: 1,
      textStyle: { color: '#000' },
    },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { fontSize: 11, color: '#666' },
    },
    series: [{
      type: 'pie',
      radius: ['50%', '70%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
      labelLine: { show: false },
      data,
    }],
  })
}

function formatMoney(n) {
  return '¥' + (n || 0).toFixed(2)
}

function getBalanceClass(balance) {
  return balance < 0 ? 'negative' : 'positive'
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">本月概览</h1>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding: 40px 20px;">
      <p style="margin-bottom: 16px; color: var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else>
      <div class="card">
        <div class="row">
          <span class="row-label">生活费</span>
          <span class="row-value">{{ formatMoney(summary?.allowance) }}</span>
        </div>
        <div class="row">
          <span class="row-label">实际收入</span>
          <span class="row-value positive">{{ formatMoney(summary?.actual_income) }}</span>
        </div>
        <div class="row">
          <span class="row-label">实际支出</span>
          <span class="row-value negative">{{ formatMoney(summary?.actual_expense) }}</span>
        </div>
        <div class="row">
          <span class="row-label">期末余额</span>
          <span class="row-value" :class="getBalanceClass(summary?.balance)">{{ formatMoney(summary?.balance) }}</span>
        </div>
        <div class="row">
          <span class="row-label">本月存下</span>
          <span class="row-value positive">{{ formatMoney(summary?.saved) }}</span>
        </div>
        <div v-if="summary?.overspent > 0" class="row">
          <span class="row-label">花超金额</span>
          <span class="row-value negative">{{ formatMoney(summary?.overspent) }}</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-title">分类占比</div>
        <div class="chart-container" ref="chartDom"></div>
      </div>
      
      <div class="card">
        <div class="card-title">心愿清单</div>
        <template v-if="store.wishlist.length === 0">
          <div class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            <p>暂无心愿，去添加一个吧</p>
          </div>
        </template>
        <div v-else class="wish-list">
          <div 
            v-for="w in store.wishlist.slice(0, 3)" 
            :key="w.id" 
            class="wish-item"
          >
            <div class="wish-info">
              <span class="wish-name">{{ w.name }}</span>
              <span class="wish-price">¥{{ w.price.toFixed(2) }}</span>
            </div>
          </div>
          <div v-if="store.wishlist.length > 3" class="wish-item" style="color: var(--color-text-muted); font-size: 13px;">
            共 {{ store.wishlist.length }} 件，总计 ¥{{ store.wishlist.reduce((s, w) => s + w.price, 0).toFixed(2) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
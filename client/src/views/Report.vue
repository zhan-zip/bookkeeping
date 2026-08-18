<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import * as echarts from 'echarts'

const store = useAppStore()
const chartDom = ref(null)
const chart = ref(null)
const report = ref(null)
const loading = ref(false)

onMounted(() => {
  if (store.isAuthenticated) {
    loadReport()
  }
})

async function loadReport() {
  loading.value = true
  try {
    report.value = await store.getMonthlyReport()
    if (chartDom.value) initChart()
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

function initChart() {
  if (!chartDom.value) return
  chart.value = echarts.init(chartDom.value)
  updateChart()
  window.addEventListener('resize', () => chart.value?.resize())
}

function updateChart() {
  if (!chart.value || !report.value) return
  const stats = report.value.category_stats
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
    <h1 class="page-title">月报</h1>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding:40px 20px;">
      <p style="margin-bottom:16px; color:var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else-if="loading" class="card" style="text-align:center; padding:40px;">
      <p style="color:var(--color-text-secondary);">生成月报中...</p>
    </div>
    
    <div v-else-if="report">
      <div class="card">
        <div class="card-title">{{ report.month }} 月报</div>
        
        <div class="row">
          <span class="row-label">生活费</span>
          <span class="row-value">{{ formatMoney(report.allowance) }}</span>
        </div>
        <div class="row">
          <span class="row-label">名义收入</span>
          <span class="row-value positive">{{ formatMoney(report.nominal_income) }}</span>
        </div>
        <div class="row">
          <span class="row-label">名义支出</span>
          <span class="row-value negative">{{ formatMoney(report.nominal_expense) }}</span>
        </div>
        <div class="row">
          <span class="row-label">AA垫付</span>
          <span class="row-value">{{ formatMoney(report.aa_advance) }}</span>
        </div>
        <div class="row">
          <span class="row-label">AA回款</span>
          <span class="row-value">{{ formatMoney(report.aa_return) }}</span>
        </div>
        <div class="row">
          <span class="row-label">实际收入</span>
          <span class="row-value positive">{{ formatMoney(report.actual_income) }}</span>
        </div>
        <div class="row">
          <span class="row-label">实际支出</span>
          <span class="row-value negative">{{ formatMoney(report.actual_expense) }}</span>
        </div>
        <div class="row">
          <span class="row-label">期末余额</span>
          <span class="row-value" :class="getBalanceClass(report.final_balance)">{{ formatMoney(report.final_balance) }}</span>
        </div>
        <div class="row">
          <span class="row-label">本月存下</span>
          <span class="row-value positive">{{ formatMoney(report.saved_this_month) }}</span>
        </div>
        <div v-if="report.overspent > 0" class="row">
          <span class="row-label">花超金额</span>
          <span class="row-value negative">{{ formatMoney(report.overspent) }}</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-title">分类占比</div>
        <div class="chart-container" ref="chartDom"></div>
      </div>
      
      <div class="card">
        <div class="card-title">心愿清单守住</div>
        <div class="row">
          <span class="row-label">件数</span>
          <span class="row-value">{{ report.wishlist_count }}</span>
        </div>
        <div class="row">
          <span class="row-label">总金额</span>
          <span class="row-value positive">{{ formatMoney(report.wishlist_total) }}</span>
        </div>
        <p style="margin-top:12px; font-size:13px; color:var(--color-text-secondary);">这些钱没花出去，相当于额外存下</p>
      </div>
      
      <div class="card">
        <div class="card-title">分类明细</div>
        <div v-for="(amt, cat) in report.category_stats" :key="cat" class="row">
          <span class="row-label">{{ cat }}</span>
          <span class="row-value negative">{{ formatMoney(amt) }}</span>
        </div>
        <div v-if="Object.keys(report.category_stats).length === 0" class="empty-state" style="padding:20px;">
          <p>本月暂无支出分类记录</p>
        </div>
      </div>
    </div>
  </div>
</template>
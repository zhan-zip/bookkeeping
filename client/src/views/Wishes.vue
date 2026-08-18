<script setup>
import { onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()

onMounted(() => {
  if (store.isAuthenticated) {
    store.fetchAll()
  }
})

function formatMoney(n) {
  if (n == null || isNaN(n)) return '¥0.00'
  return '¥' + n.toFixed(2)
}

const totalPrice = computed(() => 
  (store.wishlist || []).reduce((sum, w) => sum + (w.price || 0), 0)
)
</script>

<template>
  <div class="container">
    <h1 class="page-title">心愿清单</h1>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding:40px 20px;">
      <p style="margin-bottom:16px; color:var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else-if="store.wishlist.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
      <p>暂无心愿</p>
      <p style="font-size:12px; margin-top:8px; color:var(--color-text-secondary);">想买东西请在 QQ 机器人中说「想买 键盘 499」</p>
    </div>
    
    <div v-else>
      <div class="card" style="margin-bottom:16px; padding:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:13px; color:var(--color-text-secondary);">共 {{ store.wishlist.length }} 件</div>
            <div style="font-size:20px; font-weight:600;">{{ formatMoney(totalPrice) }}</div>
          </div>
          <div style="text-align:right; color:var(--color-text-secondary); font-size:12px;">
            忍住 = 存下了这笔钱
          </div>
        </div>
      </div>
      
      <div class="card">
        <div v-for="w in store.wishlist" :key="w.id" class="wish-item">
          <div class="wish-info">
            <span class="wish-name">{{ w.name }}</span>
            <span class="wish-price">{{ formatMoney(w.price) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
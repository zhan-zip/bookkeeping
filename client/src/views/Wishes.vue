<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const showModal = ref(false)
const buyingWish = ref(null)
const form = ref({ name: '', price: '', category: '购物', note: '' })
const loading = ref(false)

onMounted(() => {
  if (store.isAuthenticated) {
    store.fetchAll()
  }
})

async function addWish() {
  if (!form.value.name || !form.value.price) return
  loading.value = true
  try {
    await store.addWish(form.value.name, Number(form.value.price))
    showModal.value = false
    form.value = { name: '', price: '', category: '购物', note: '' }
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

async function buyWish(wish) {
  buyingWish.value = wish
  form.value = { name: '', price: '', category: '购物', note: `心愿购买: ${wish.name}` }
  showModal.value = true
}

async function confirmBuy() {
  if (!buyingWish.value) return
  loading.value = true
  try {
    await store.buyWish(buyingWish.value.id, form.value.category, form.value.note)
    showModal.value = false
    buyingWish.value = null
    form.value = { name: '', price: '', category: '购物', note: '' }
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

function formatMoney(n) {
  return '¥' + n.toFixed(2)
}

const totalPrice = computed(() => 
  store.wishlist.reduce((sum, w) => sum + w.price, 0)
)
</script>

<template>
  <div class="container">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <h1 class="page-title" style="margin:0;">心愿清单</h1>
      <button class="btn btn-primary" @click="showModal = true" style="padding:8px 16px; font-size:14px; min-height:40px;">+ 添加心愿</button>
    </div>
    
    <div v-if="!store.isAuthenticated" class="card" style="text-align:center; padding:40px 20px;">
      <p style="margin-bottom:16px; color:var(--color-text-secondary);">请先在设置中配置 GitHub Token</p>
      <router-link to="/settings" class="btn btn-primary">去设置</router-link>
    </div>
    
    <div v-else-if="store.wishlist.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
      <p>暂无心愿，点击右下角 + 添加</p>
      <p style="font-size:12px; margin-top:8px;">想买东西先放这里，真买了再转正式支出</p>
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
          <div class="wish-actions">
            <button class="btn btn-ghost" @click="buyWish(w)" style="padding:6px 12px; font-size:13px; min-height:36px;">真买</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add Wish Modal -->
    <div class="modal" :class="{ open: showModal && !buyingWish }" @click.self="showModal = false">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <h2 style="margin-bottom:20px;">添加心愿</h2>
        
        <div class="form-group">
          <label class="form-label">东西名</label>
          <input type="text" v-model="form.name" class="form-input" placeholder="例如：机械键盘、Kindle" maxlength="30">
        </div>
        
        <div class="form-group">
          <label class="form-label">价格</label>
          <input type="number" step="0.01" v-model="form.price" class="form-input" placeholder="0.00" inputmode="decimal">
        </div>
        
        <div style="display:flex; gap:12px; margin-top:24px;">
          <button class="btn btn-secondary" style="flex:1;" @click="showModal = false">取消</button>
          <button class="btn btn-primary" style="flex:1;" @click="addWish" :disabled="loading">
            {{ loading ? '添加中...' : '加入清单' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Buy Wish Modal -->
    <div class="modal" :class="{ open: showModal && buyingWish }" @click.self="showModal = false">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <h2 style="margin-bottom:20px;">确认购买：{{ buyingWish?.name }}</h2>
        <p style="color:var(--color-text-secondary); margin-bottom:20px; font-size:14px;">价格：{{ formatMoney(buyingWish?.price) }} · 真买后会从心愿清单移除，并记入正式支出</p>
        
        <div class="form-group">
          <label class="form-label">分类</label>
          <select v-model="form.category" class="form-input" style="padding:12px;">
            <option v-for="c in ['技术','学习','吃饭','零食','购物','生活','社交','出行']" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">备注</label>
          <input type="text" v-model="form.note" class="form-input" placeholder="可选备注" maxlength="50">
        </div>
        
        <div style="display:flex; gap:12px; margin-top:24px;">
          <button class="btn btn-secondary" style="flex:1;" @click="showModal = false; buyingWish = null">再忍忍</button>
          <button class="btn btn-primary" style="flex:1;" @click="confirmBuy" :disabled="loading">
            {{ loading ? '处理中...' : '确定买了' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
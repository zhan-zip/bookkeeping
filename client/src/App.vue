<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const route = useRoute()
const store = useAppStore()

const fabOpen = ref(false)
const toastMsg = ref('')
const toastTimer = ref(null)

const navItems = [
  { path: '/overview', icon: overviewIcon, label: '总览' },
  { path: '/records', icon: recordsIcon, label: '流水' },
  { path: '/wishes', icon: wishesIcon, label: '心愿' },
  { path: '/report', icon: reportIcon, label: '月报' },
]

function toggleFab() {
  fabOpen.value = !fabOpen.value
}

function navigate(path) {
  router.push(path)
  fabOpen.value = false
}

function showToast(msg, duration = 2000) {
  toastMsg.value = msg
  if (toastTimer.value) clearTimeout(toastTimer.value)
  toastTimer.value = setTimeout(() => { toastMsg.value = '' }, duration)
}

function handlePullRefresh() {
  store.fetchAll()
  showToast('已刷新')
}

let touchStartY = 0
let touchMoving = false

function onTouchStart(e) {
  if (window.scrollY === 0) {
    touchStartY = e.touches[0].clientY
    touchMoving = true
  }
}

function onTouchMove(e) {
  if (!touchMoving) return
  const deltaY = e.touches[0].clientY - touchStartY
  if (deltaY > 60) {
    touchMoving = false
    handlePullRefresh()
  }
}

function onTouchEnd() {
  touchMoving = false
}

onMounted(() => {
  store.loadToken()
  if (store.isAuthenticated) {
    store.fetchAll()
  }
  document.addEventListener('touchstart', onTouchStart, { passive: true })
  document.addEventListener('touchmove', onTouchMove, { passive: true })
  document.addEventListener('touchend', onTouchEnd)
})

onUnmounted(() => {
  document.removeEventListener('touchstart', onTouchStart)
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
  if (toastTimer.value) clearTimeout(toastTimer.value)
})

const overviewIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`
const recordsIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>`
const wishesIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`
const reportIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`
const plusIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`
const closeIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`
</script>

<template>
  <div class="app">
    <div class="overlay" :class="{ open: fabOpen }" @click="fabOpen = false" aria-hidden="true"></div>
    
    <nav class="nav-menu" :class="{ open: fabOpen }" role="navigation" aria-label="主导航">
      <div 
        v-for="item in navItems" 
        :key="item.path"
        class="nav-item"
        :class="{ active: route.path === item.path }"
        @click="navigate(item.path)"
        role="button"
        tabindex="0"
        @keydown.enter="navigate(item.path)"
      >
        <span v-html="item.icon"></span>
        <span>{{ item.label }}</span>
      </div>
    </nav>
    
    <router-view />
    
    <button 
      class="fab" 
      @click="toggleFab"
      :aria-expanded="fabOpen"
      :aria-label="fabOpen ? '关闭菜单' : '打开菜单'"
    >
      <span v-html="fabOpen ? closeIcon : plusIcon"></span>
    </button>
    
    <div class="toast" :class="{ show: toastMsg }" role="status" aria-live="polite">
      {{ toastMsg }}
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  position: relative;
}
</style>
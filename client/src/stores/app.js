import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/storage'
import { setToken as setGithubToken } from '@/api/github'

export const useAppStore = defineStore('app', () => {
  const token = ref('')
  const expenses = ref([])
  const wishlist = ref([])
  const monthlySummary = ref(null)
  const categoryStats = ref({})
  const loading = ref(false)
  const error = ref(null)
  const budgets = ref({})
  
  const isAuthenticated = computed(() => !!token.value)
  
  function setToken(t) {
    token.value = t
    localStorage.setItem('github_token', t)
    setGithubToken(t)
  }
  
  function loadToken() {
    const saved = localStorage.getItem('github_token')
    if (saved) {
      token.value = saved
      setGithubToken(saved)
    }
  }
  
  function clearError() {
    error.value = null
  }
  
  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      expenses.value = await api.getRecent(1000)
      wishlist.value = await api.getWishlist()
      monthlySummary.value = await api.getMonthSummary()
      categoryStats.value = await api.getCategoryStats()
    } catch (e) {
      error.value = e.message
      console.error(e)
    } finally {
      loading.value = false
    }
  }
  
  async function refreshMonth() {
    monthlySummary.value = await api.getMonthSummary()
    categoryStats.value = await api.getCategoryStats()
  }
  
  async function getMonthlyReport() {
    clearError()
    try {
      return await api.getMonthlyReport()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  return {
    token,
    expenses,
    wishlist,
    monthlySummary,
    categoryStats,
    loading,
    error,
    budgets,
    isAuthenticated,
    setToken,
    loadToken,
    fetchAll,
    refreshMonth,
    getMonthlyReport,
  }
})
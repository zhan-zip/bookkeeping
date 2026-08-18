import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/storage'

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
  }
  
  function loadToken() {
    const saved = localStorage.getItem('github_token')
    if (saved) token.value = saved
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
  
  async function addExpense(amount, category, note, type = 'expense', date = null) {
    clearError()
    try {
      const record = await api.addExpense(amount, category, note, type, date)
      await fetchAll()
      return record
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  async function addWish(name, price) {
    clearError()
    try {
      const item = await api.addWish(name, price)
      wishlist.value = await api.getWishlist()
      return item
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  async function buyWish(wishId, category, note) {
    clearError()
    try {
      const result = await api.buyWish(wishId, category, note)
      await fetchAll()
      return result
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  async function deleteExpense(expenseId) {
    clearError()
    try {
      await api.deleteExpense(expenseId)
      await fetchAll()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  async function updateExpense(expenseId, updates) {
    clearError()
    try {
      await api.updateExpense(expenseId, updates)
      await fetchAll()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  async function ensureAllowance() {
    clearError()
    try {
      const result = await api.ensureMonthlyAllowance()
      await fetchAll()
      return result
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  async function refreshMonth() {
    monthlySummary.value = await api.getMonthSummary()
    categoryStats.value = await api.getCategoryStats()
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
    addExpense,
    addWish,
    buyWish,
    deleteExpense,
    updateExpense,
    ensureAllowance,
    refreshMonth,
  }
})
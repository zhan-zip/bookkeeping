<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const token = ref('')
const saving = ref(false)
const testResult = ref('')

onMounted(() => {
  token.value = store.token
})

async function saveToken() {
  if (!token.value.trim()) {
    alert('请输入 Token')
    return
  }
  saving.value = true
  store.setToken(token.value.trim())
  try {
    await store.fetchAll()
    testResult.value = '✅ Token 有效，数据加载成功'
  } catch (e) {
    testResult.value = '❌ ' + e.message
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  if (!token.value.trim()) {
    alert('请先输入 Token')
    return
  }
  testResult.value = '测试中...'
  store.setToken(token.value.trim())
  try {
    await store.fetchAll()
    testResult.value = '✅ 连接成功，数据加载正常'
  } catch (e) {
    testResult.value = '❌ ' + e.message
  }
}

function clearToken() {
  token.value = ''
  store.setToken('')
  localStorage.removeItem('github_token')
  testResult.value = '已清除 Token'
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">设置</h1>
    
    <div class="card">
      <div class="card-title">GitHub 配置</div>
      <p style="font-size:13px; color:var(--color-text-secondary); margin-bottom:16px; line-height:1.6;">
        请输入具有 <strong>repo</strong> 权限的 GitHub Personal Access Token。<br>
        数据存储在私有仓库 <code>zhan-zip/bookkeeping</code> 的 <code>data/</code> 目录下。
      </p>
      
      <div class="form-group">
        <label class="form-label">GitHub Token</label>
        <input 
          type="password" 
          v-model="token" 
          class="form-input" 
          placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
          @keydown.enter="saveToken"
        >
      </div>
      
      <div style="display:flex; gap:12px; margin-top:16px;">
        <button class="btn btn-primary" style="flex:1;" @click="saveToken" :disabled="saving">
          {{ saving ? '保存中...' : '保存并测试' }}
        </button>
        <button class="btn btn-secondary" style="flex:1;" @click="testConnection" :disabled="saving || !token">
          测试连接
        </button>
      </div>
      
      <button v-if="token" class="btn btn-danger" style="width:100%; margin-top:12px;" @click="clearToken">
        清除 Token
      </button>
      
      <p v-if="testResult" style="margin-top:12px; font-size:13px; color:var(--color-text-secondary);">{{ testResult }}</p>
    </div>
    
    <div class="card">
      <div class="card-title">关于</div>
      <div class="row">
        <span class="row-label">版本</span>
        <span class="row-value">M3 预览版</span>
      </div>
      <div class="row">
        <span class="row-label">数据源</span>
        <span class="row-value">GitHub 私有仓库</span>
      </div>
      <div class="row">
        <span class="row-label">记账入口</span>
        <span class="row-value">QQ 机器人 (MCP)</span>
      </div>
      <div class="row">
        <span class="row-label">查看端</span>
        <span class="row-value">手机 PWA (只读)</span>
      </div>
    </div>
    
    <div class="card">
      <div class="card-title">使用说明</div>
      <div style="font-size:13px; color:var(--color-text-secondary); line-height:1.8;">
        <p style="margin-bottom:12px;"><strong>1. 配置 Token：</strong>在 GitHub Settings → Developer settings → Personal access tokens 生成 token，勾选 repo 权限。</p>
        <p style="margin-bottom:12px;"><strong>2. 记账：</strong>在 QQ 中对机器人说"午饭 25"或"买了键盘 499 购物"。</p>
        <p style="margin-bottom:12px;"><strong>3. 查看：</strong>打开本 PWA 查看总览、流水、心愿、月报。</p>
        <p style="margin-bottom:12px;"><strong>4. 心愿清单：</strong>想买的东西先放这里，真买了点"真买"转正式支出。</p>
        <p><strong>5. 月底清零：</strong>每月最后一天 00:00 自动清零，次月需重新录入生活费。</p>
      </div>
    </div>
  </div>
</template>
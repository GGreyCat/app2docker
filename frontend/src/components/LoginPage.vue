<template>
  <div class="login-page d-flex align-items-center justify-content-center min-vh-100 bg-light">
    <div class="login-container">
      <div class="card shadow-lg" style="width: 400px;">
        <div class="card-body p-4">
          <!-- Logo -->
          <div class="text-center mb-4">
            <i class="fas fa-box-open fa-3x text-primary mb-3"></i>
            <h3 class="fw-bold">App2Docker</h3>
            <p class="text-muted small">Docker 镜像构建平台</p>
          </div>

          <!-- 登录表单 -->
          <form @submit.prevent="handleLogin">
            <div class="mb-3">
              <label class="form-label">
                <i class="fas fa-user"></i> 用户名
              </label>
              <input 
                v-model="username" 
                type="text" 
                class="form-control" 
                placeholder="请输入用户名"
                required
                autocomplete="username"
              />
            </div>

            <div class="mb-3">
              <label class="form-label">
                <i class="fas fa-lock"></i> 密码
              </label>
              <input 
                v-model="password" 
                type="password" 
                class="form-control" 
                placeholder="请输入密码"
                required
                autocomplete="current-password"
              />
            </div>

            <div class="mb-3 form-check">
              <input 
                v-model="rememberMe" 
                type="checkbox" 
                class="form-check-input" 
                id="rememberMe"
              />
              <label class="form-check-label" for="rememberMe">
                记住我
              </label>
            </div>

            <button 
              type="submit" 
              class="btn btn-primary w-100" 
              :disabled="loading"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </form>

          <!-- 错误提示 -->
          <div v-if="error" class="alert alert-danger mt-3 mb-0" role="alert">
            <i class="fas fa-exclamation-triangle"></i>
            {{ error }}
          </div>

          <!-- 默认账号提示 -->
          <div class="mt-3 p-3 bg-light rounded small">
            <p class="mb-1 text-muted">
              <i class="fas fa-info-circle"></i> 默认账号
            </p>
            <div class="font-monospace">
              <div>用户名: <code>admin</code></div>
              <div>密码: <code>admin</code></div>
            </div>
          </div>
        </div>

        <!-- 版本信息 -->
        <div class="card-footer text-center text-muted small bg-light">
          <i class="fas fa-shield-alt"></i> 安全认证登录
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['login-success'])

const username = ref('admin')
const password = ref('')
const rememberMe = ref(true)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  
  try {
    const res = await axios.post('/api/login', {
      username: username.value,
      password: password.value
    })
    
    if (res.data.success) {
      // 保存 token
      const storage = rememberMe.value ? localStorage : sessionStorage
      storage.setItem('auth_token', res.data.token)
      storage.setItem('username', res.data.username)
      
      // 设置 axios 默认 header
      axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.token}`
      
      emit('login-success', {
        username: res.data.username,
        token: res.data.token
      })
    } else {
      error.value = res.data.error || '登录失败'
    }
  } catch (err) {
    error.value = err.response?.data?.error || '登录失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  animation: slideIn 0.4s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card {
  border: none;
  border-radius: 1rem;
}

.card-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 0 0 1rem 1rem;
}

code {
  background-color: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #d63384;
}
</style>


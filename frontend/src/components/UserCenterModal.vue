<template>
  <div v-if="show" class="modal fade show d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-user-circle"></i> 用户中心
          </h5>
          <button type="button" class="btn-close" @click="close"></button>
        </div>
        <div class="modal-body">
          <!-- 需要修改密码的提示 -->
          <div v-if="requirePasswordChange" class="alert alert-warning mb-3">
            <i class="fas fa-info-circle"></i> 
            检测到您使用的是默认密码，为了安全起见，请先修改密码。
          </div>

          <!-- 用户信息 -->
          <div v-if="!requirePasswordChange" class="mb-4">
            <h6 class="mb-3">
              <i class="fas fa-user"></i> 用户信息
            </h6>
            <div class="card bg-light">
              <div class="card-body">
                <div class="d-flex align-items-center">
                  <i class="fas fa-user-circle fa-2x text-primary me-3"></i>
                  <div>
                    <div class="fw-bold">{{ username }}</div>
                    <small class="text-muted">管理员</small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 修改密码 -->
          <div>
            <h6 v-if="!requirePasswordChange" class="mb-3">
              <i class="fas fa-key"></i> 修改密码
            </h6>
            <form @submit.prevent="handleChangePassword">
              <div class="mb-3">
                <label class="form-label">
                  当前密码 <span class="text-danger">*</span>
                </label>
                <input 
                  v-model="form.oldPassword" 
                  type="password" 
                  class="form-control" 
                  placeholder="请输入当前密码"
                  required
                  autocomplete="current-password"
                />
              </div>
              
              <div class="mb-3">
                <label class="form-label">
                  新密码 <span class="text-danger">*</span>
                </label>
                <input 
                  v-model="form.newPassword" 
                  type="password" 
                  class="form-control" 
                  placeholder="请输入新密码（至少6位）"
                  required
                  minlength="6"
                  autocomplete="new-password"
                />
                <div class="form-text">密码长度至少6位</div>
              </div>
              
              <div class="mb-3">
                <label class="form-label">
                  确认新密码 <span class="text-danger">*</span>
                </label>
                <input 
                  v-model="form.confirmPassword" 
                  type="password" 
                  class="form-control" 
                  placeholder="请再次输入新密码"
                  required
                  minlength="6"
                  autocomplete="new-password"
                />
              </div>
              
              <div v-if="error" class="alert alert-danger mb-0">
                <i class="fas fa-exclamation-circle"></i> {{ error }}
              </div>
              
              <div v-if="success" class="alert alert-success mb-0">
                <i class="fas fa-check-circle"></i> {{ success }}
              </div>
            </form>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            v-if="!requirePasswordChange"
            type="button" 
            class="btn btn-secondary" 
            @click="close"
          >
            关闭
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="handleChangePassword"
            :disabled="loading || !canSubmit"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? '修改中...' : '修改密码' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  username: {
    type: String,
    default: ''
  },
  requirePasswordChange: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:show', 'password-changed'])

const form = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

const canSubmit = computed(() => {
  return form.value.oldPassword && 
         form.value.newPassword && 
         form.value.confirmPassword &&
         form.value.newPassword.length >= 6 &&
         form.value.newPassword === form.value.confirmPassword
})

function close() {
  emit('update:show', false)
  // 清空表单和消息
  form.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  error.value = ''
  success.value = ''
}

async function handleChangePassword() {
  if (!canSubmit.value) {
    error.value = '请填写完整信息，且新密码长度至少6位，两次输入需一致'
    return
  }
  
  if (form.value.newPassword !== form.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  if (form.value.newPassword.length < 6) {
    error.value = '新密码长度至少6位'
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const res = await axios.post('/api/change-password', {
      old_password: form.value.oldPassword,
      new_password: form.value.newPassword
    })
    
    if (res.data.success) {
      success.value = '密码修改成功！'
      // 清空表单
      form.value = {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      
      // 如果是必须修改密码模式，修改成功后触发事件并关闭
      if (props.requirePasswordChange) {
        // 延迟一下，让用户看到成功消息
        setTimeout(() => {
          emit('password-changed')
          emit('update:show', false)
        }, 1000)
      } else {
        // 普通模式，只显示成功消息
        // 3秒后自动关闭成功消息
        setTimeout(() => {
          success.value = ''
        }, 3000)
      }
    } else {
      error.value = res.data.error || '修改密码失败'
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || '修改密码失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal.show {
  display: block;
}
</style>

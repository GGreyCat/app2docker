<template>
  <div 
    class="modal fade" 
    :class="{ show: modelValue, 'd-block': modelValue }"
    tabindex="-1"
    @click.self="close"
  >
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header bg-primary text-white">
          <h5 class="modal-title">
            <i class="fas fa-cog"></i> Docker 配置
          </h5>
          <button type="button" class="btn-close btn-close-white" @click="close"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="save">
            <!-- Docker 构建配置 -->
            <h6 class="mb-3 text-primary">
              <i class="fas fa-server"></i> Docker 构建配置
            </h6>
            <div class="row g-3 mb-4">
              <div class="col-md-12">
                <div class="form-check form-switch">
                  <input 
                    v-model="config.use_remote" 
                    type="checkbox" 
                    class="form-check-input" 
                    id="useRemote"
                  />
                  <label class="form-check-label" for="useRemote">
                    <strong>使用远程 Docker</strong>
                    <small class="text-muted d-block">启用后将连接远程 Docker 服务器进行构建</small>
                  </label>
                </div>
              </div>
              
              <!-- 远程 Docker 配置（仅在启用远程时显示） -->
              <template v-if="config.use_remote">
                <div class="col-12">
                  <div class="alert alert-info mb-3">
                    <i class="fas fa-info-circle"></i> 
                    远程 Docker 配置需要确保远程主机的 Docker 守护进程已开启 TCP 访问
                  </div>
                </div>
                <div class="col-md-8">
                  <label class="form-label">远程主机地址 *</label>
                  <input 
                    v-model="config.remote.host" 
                    type="text" 
                    class="form-control" 
                    placeholder="192.168.1.100"
                    :required="config.use_remote"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">端口</label>
                  <input 
                    v-model.number="config.remote.port" 
                    type="number" 
                    class="form-control" 
                    placeholder="2375"
                  />
                </div>
                <div class="col-md-6">
                  <div class="form-check">
                    <input 
                      v-model="config.remote.use_tls" 
                      type="checkbox" 
                      class="form-check-input" 
                      id="remoteTls"
                    />
                    <label class="form-check-label" for="remoteTls">
                      使用 TLS 加密连接
                    </label>
                  </div>
                </div>
                <div class="col-md-6" v-if="config.remote.use_tls">
                  <div class="form-check">
                    <input 
                      v-model="config.remote.verify_tls" 
                      type="checkbox" 
                      class="form-check-input" 
                      id="remoteVerifyTls"
                    />
                    <label class="form-check-label" for="remoteVerifyTls">
                      验证 TLS 证书
                    </label>
                  </div>
                </div>
                <div class="col-md-12" v-if="config.remote.use_tls">
                  <label class="form-label">证书路径</label>
                  <input 
                    v-model="config.remote.cert_path" 
                    type="text" 
                    class="form-control" 
                    placeholder="/path/to/certs"
                  />
                  <small class="text-muted">
                    证书目录应包含 ca.pem, cert.pem, key.pem
                  </small>
                </div>
              </template>
            </div>

            <!-- 镜像仓库配置 -->
            <h6 class="mb-3 text-primary d-flex justify-content-between align-items-center">
              <span>
                <i class="fas fa-box"></i> 镜像仓库配置
              </span>
              <button type="button" class="btn btn-sm btn-success" @click="addRegistry">
                <i class="fas fa-plus"></i> 添加仓库
              </button>
            </h6>

            <!-- 仓库列表 -->
            <div v-if="config.registries && config.registries.length > 0" class="mb-4">
              <div 
                v-for="(registry, index) in config.registries" 
                :key="index"
                class="card mb-3"
                :class="{ 'border-primary': registry.active }"
              >
                <div class="card-header d-flex justify-content-between align-items-center">
                  <div class="d-flex align-items-center">
                    <input 
                      v-model="registry.active"
                      type="radio"
                      :name="'active-registry'"
                      :checked="registry.active"
                      @change="setActiveRegistry(index)"
                      class="form-check-input me-2"
                    />
                    <strong>{{ registry.name }}</strong>
                    <span v-if="registry.active" class="badge bg-primary ms-2">激活</span>
                  </div>
                  <button 
                    type="button" 
                    class="btn btn-sm btn-danger" 
                    @click="removeRegistry(index)"
                    :disabled="config.registries.length === 1"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
                <div class="card-body">
                  <div class="row g-3">
                    <div class="col-md-12">
                      <label class="form-label">仓库名称</label>
                      <input 
                        v-model="registry.name" 
                        type="text" 
                        class="form-control" 
                        placeholder="如：Docker Hub"
                        required
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">Registry 地址</label>
                      <input 
                        v-model="registry.registry" 
                        type="text" 
                        class="form-control" 
                        placeholder="docker.io"
                        required
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">镜像前缀（可选）</label>
                      <input 
                        v-model="registry.registry_prefix" 
                        type="text" 
                        class="form-control" 
                        placeholder="your-namespace"
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">账号</label>
                      <input 
                        v-model="registry.username" 
                        type="text" 
                        class="form-control" 
                        placeholder="用户名"
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">密码</label>
                      <input 
                        v-model="registry.password" 
                        type="password" 
                        class="form-control" 
                        placeholder="密码"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 其他配置 -->
            <div class="row g-3 mb-4">
              <div class="col-md-6">
                <label class="form-label">暴露端口</label>
                <input v-model.number="config.expose_port" type="number" class="form-control" />
              </div>
              <div class="col-md-6 d-flex align-items-end">
                <div class="form-check">
                  <input 
                    v-model="config.default_push" 
                    type="checkbox" 
                    class="form-check-input" 
                    id="defaultPush"
                  />
                  <label class="form-check-label" for="defaultPush">
                    默认推送镜像
                  </label>
                </div>
              </div>
              <div class="col-md-12 d-flex justify-content-end">
                <button type="submit" class="btn btn-primary" :disabled="saving">
                  <i class="fas fa-save"></i> 
                  {{ saving ? '保存中...' : '保存配置' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
  
  <div v-if="modelValue" class="modal-backdrop fade show"></div>
</template>

<script setup>
import axios from 'axios'
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue'])

const config = ref({
  registries: [
    {
      name: 'Docker Hub',
      registry: 'docker.io',
      registry_prefix: '',
      username: '',
      password: '',
      active: true
    }
  ],
  expose_port: 8080,
  default_push: false,  // 默认不推送
  use_remote: false,  // 是否使用远程 Docker
  remote: {
    host: '',
    port: 2375,
    use_tls: false,
    cert_path: '',
    verify_tls: true
  }
})

const saving = ref(false)

async function loadConfig() {
  try {
    console.log('📥 正在加载配置...')
    const res = await axios.get('/api/get-config')
    console.log('📋 配置响应:', res.data)
    
    const docker = res.data.docker || {}
    const remote = docker.remote || {}
    
    // 处理仓库列表
    let registries = docker.registries || []
    
    // 如果没有仓库，创建一个默认仓库
    if (!registries || registries.length === 0) {
      registries = [{
        name: 'Docker Hub',
        registry: 'docker.io',
        registry_prefix: '',
        username: '',
        password: '',
        active: true
      }]
    }
    
    // 确保至少有一个仓库被激活
    const hasActive = registries.some(r => r.active)
    if (!hasActive && registries.length > 0) {
      registries[0].active = true
    }
    
    config.value = {
      registries: registries,
      expose_port: docker.expose_port || 8080,
      default_push: docker.default_push === true,  // 布尔值必须严格判断
      use_remote: docker.use_remote === true,
      remote: {
        host: remote.host || '',
        port: remote.port || 2375,
        use_tls: remote.use_tls === true,
        cert_path: remote.cert_path || '',
        verify_tls: remote.verify_tls !== false  // 默认为 true
      }
    }
    console.log('✅ 配置已加载:', config.value)
  } catch (error) {
    console.error('❌ 加载配置失败:', error)
    const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message
    alert(`加载配置失败: ${errorMsg}`)
  }
}

async function save() {
  saving.value = true
  try {
    // 先保存仓库配置
    const registriesRes = await axios.post('/api/registries', {
      registries: config.value.registries
    })
    console.log('✅ 仓库配置保存成功:', registriesRes.data)
    
    // 然后保存其他配置
    const formData = new FormData()
    
    // 添加基础配置（使用激活仓库的配置进行向后兼容）
    const activeRegistry = config.value.registries.find(r => r.active) || config.value.registries[0]
    formData.append('registry', activeRegistry.registry)
    formData.append('registry_prefix', activeRegistry.registry_prefix)
    formData.append('username', activeRegistry.username)
    formData.append('password', activeRegistry.password)
    formData.append('expose_port', String(config.value.expose_port))
    formData.append('default_push', config.value.default_push ? 'on' : 'off')
    
    // 添加远程 Docker 配置
    formData.append('use_remote', config.value.use_remote ? 'on' : 'off')
    formData.append('remote_host', config.value.remote.host)
    formData.append('remote_port', String(config.value.remote.port))
    formData.append('remote_use_tls', config.value.remote.use_tls ? 'on' : 'off')
    formData.append('remote_cert_path', config.value.remote.cert_path)
    formData.append('remote_verify_tls', config.value.remote.verify_tls ? 'on' : 'off')
    
    console.log('📤 发送配置:', Object.fromEntries(formData))
    
    const res = await axios.post('/api/save-config', formData)
    console.log('✅ 其他配置保存成功:', res.data)
    
    // 保存成功后重新加载配置以验证
    await loadConfig()
    
    alert('配置保存成功')
    close()
  } catch (error) {
    console.error('❌ 保存配置失败:', error)
    const errorMsg = error.response?.data?.detail || error.response?.data?.error || '保存配置失败'
    alert(errorMsg)
  } finally {
    saving.value = false
  }
}

// 添加仓库
function addRegistry() {
  config.value.registries.push({
    name: `仓库 ${config.value.registries.length + 1}`,
    registry: 'docker.io',
    registry_prefix: '',
    username: '',
    password: '',
    active: false
  })
}

// 移除仓库
function removeRegistry(index) {
  if (config.value.registries.length === 1) {
    alert('至少需要保留一个仓库')
    return
  }
  
  const wasActive = config.value.registries[index].active
  config.value.registries.splice(index, 1)
  
  // 如果删除的是激活仓库，激活第一个
  if (wasActive && config.value.registries.length > 0) {
    config.value.registries[0].active = true
  }
}

// 设置激活仓库
function setActiveRegistry(index) {
  config.value.registries.forEach((reg, i) => {
    reg.active = (i === index)
  })
}

function close() {
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  (val) => {
  if (val) {
      console.log('🔔 ConfigModal: 模态框打开，开始加载配置')
    loadConfig()
  }
  },
  { immediate: true }  // 立即执行一次，确保首次打开时也会加载
)
</script>

<style scoped>
.modal.show {
  display: block !important;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>


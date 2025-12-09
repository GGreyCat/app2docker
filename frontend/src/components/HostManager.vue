<template>
  <div class="host-manager-panel">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="mb-0">
        <i class="fas fa-server"></i> 主机资源管理
      </h6>
      <button class="btn btn-primary btn-sm" @click="showAddModal = true">
        <i class="fas fa-plus"></i> 添加主机
      </button>
    </div>

    <!-- 主机列表 -->
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>主机名称</th>
            <th>主机地址</th>
            <th>SSH端口</th>
            <th>用户名</th>
            <th>认证方式</th>
            <th>Docker信息</th>
            <th>描述</th>
            <th>创建时间</th>
            <th class="text-end">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="text-center py-4">
              <div class="spinner-border spinner-border-sm me-2"></div>
              加载中...
            </td>
          </tr>
          <tr v-else-if="hosts.length === 0">
            <td colspan="9" class="text-center text-muted py-4">
              <i class="fas fa-server fa-2x mb-2 d-block"></i>
              暂无主机，请点击"添加主机"添加
            </td>
          </tr>
          <tr v-for="host in hosts" :key="host.host_id">
            <td>
              <strong>{{ host.name }}</strong>
            </td>
            <td>{{ host.host }}</td>
            <td>{{ host.port }}</td>
            <td>{{ host.username }}</td>
            <td>
              <span v-if="host.has_private_key" class="badge bg-info">
                <i class="fas fa-key"></i> 密钥
              </span>
              <span v-else-if="host.has_password" class="badge bg-secondary">
                <i class="fas fa-lock"></i> 密码
              </span>
              <span v-else class="badge bg-warning">未配置</span>
            </td>
            <td>
              <div v-if="host.checking_docker" class="text-muted small">
                <span class="spinner-border spinner-border-sm me-1"></span>检测中...
              </div>
              <div v-else>
                <span v-if="host.docker_available" class="badge bg-success mb-1 d-inline-block">
                  <i class="fab fa-docker me-1"></i>可用
                </span>
                <span v-else class="badge bg-secondary mb-1 d-inline-block">
                  <i class="fab fa-docker me-1"></i>不可用
                </span>
                <div v-if="host.docker_version" class="small text-muted mt-1">
                  <i class="fas fa-info-circle me-1"></i>{{ host.docker_version }}
                </div>
              </div>
            </td>
            <td>
              <span class="text-muted small">{{ host.description || '无描述' }}</span>
            </td>
            <td>{{ formatTime(host.created_at) }}</td>
            <td class="text-end">
              <div class="btn-group btn-group-sm">
                <button 
                  class="btn btn-outline-info" 
                  @click="testConnection(host)"
                  :disabled="testingConnection === host.host_id"
                  title="测试连接"
                >
                  <span v-if="testingConnection === host.host_id" class="spinner-border spinner-border-sm"></span>
                  <i v-else class="fas fa-plug"></i>
                </button>
                <button 
                  class="btn btn-outline-primary" 
                  @click="editHost(host)"
                  title="编辑"
                >
                  <i class="fas fa-edit"></i>
                </button>
                <button 
                  class="btn btn-outline-danger" 
                  @click="deleteHost(host)"
                  title="删除"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 添加/编辑主机模态框 -->
    <div v-if="showAddModal || showEditModal" class="modal fade show d-block" style="background-color: rgba(0,0,0,0.5);" @click.self="closeModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title mb-0">
              <i class="fas fa-server me-2"></i> {{ editingHost ? '编辑主机' : '添加主机' }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveHost">
              <!-- 主机信息 -->
              <div class="mb-4">
                <h6 class="mb-3 text-muted border-bottom pb-2">
                  <i class="fas fa-server me-2"></i>主机信息
                </h6>
                <div class="row g-3">
                  <div class="col-md-6">
                    <label class="form-label">
                      主机名称 <span class="text-danger">*</span>
                    </label>
                    <input 
                      type="text" 
                      class="form-control form-control-sm" 
                      v-model="hostForm.name"
                      placeholder="例如：生产服务器"
                      required
                    />
                  </div>
                  <div class="col-md-6">
                    <label class="form-label">
                      主机地址 <span class="text-danger">*</span>
                    </label>
                    <input 
                      type="text" 
                      class="form-control form-control-sm" 
                      v-model="hostForm.host"
                      placeholder="例如：192.168.1.100"
                      required
                    />
                  </div>
                  <div class="col-md-6">
                    <label class="form-label">
                      SSH端口 <span class="text-danger">*</span>
                    </label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm" 
                      v-model.number="hostForm.port"
                      placeholder="22"
                      min="1"
                      max="65535"
                      required
                    />
                  </div>
                  <div class="col-12">
                    <label class="form-label">描述（可选）</label>
                    <input 
                      type="text" 
                      class="form-control form-control-sm" 
                      v-model="hostForm.description"
                      placeholder="请输入主机描述信息..."
                    />
                  </div>
                  <div class="col-12">
                    <div v-if="hostForm.docker_version || (editingHost && editingHost.docker_version)" class="small text-muted">
                      <i class="fab fa-docker me-1"></i>
                      <strong>Docker版本:</strong> {{ hostForm.docker_version || (editingHost && editingHost.docker_version) || '未知' }}
                    </div>
                    <div v-else class="small text-muted">
                      <i class="fab fa-docker me-1"></i>
                      Docker信息将在测试连接后自动检测
                    </div>
                  </div>
                </div>
              </div>

              <!-- SSH认证配置 -->
              <div class="mb-3">
                <h6 class="mb-3 text-muted border-bottom pb-2">
                  <i class="fas fa-key me-2"></i>SSH认证配置
                </h6>
                
                <div class="mb-3">
                  <label class="form-label mb-2">
                    认证方式 <span class="text-danger">*</span>
                  </label>
                  <div class="btn-group w-100" role="group">
                    <input 
                      type="radio" 
                      class="btn-check" 
                      name="authType" 
                      id="authPassword"
                      value="password"
                      v-model="authType"
                    />
                    <label class="btn btn-outline-primary" for="authPassword">
                      <i class="fas fa-lock me-1"></i>密码认证
                    </label>
                    
                    <input 
                      type="radio" 
                      class="btn-check" 
                      name="authType" 
                      id="authKey"
                      value="key"
                      v-model="authType"
                    />
                    <label class="btn btn-outline-primary" for="authKey">
                      <i class="fas fa-key me-1"></i>密钥认证
                    </label>
                  </div>
                </div>

                <!-- 密码认证 -->
                <div v-if="authType === 'password'">
                  <div class="row g-3">
                    <div class="col-md-6">
                      <label class="form-label">
                        SSH用户名 <span class="text-danger">*</span>
                      </label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="hostForm.username"
                        placeholder="例如：root"
                        required
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">
                        SSH密码 <span class="text-danger">*</span>
                      </label>
                      <input 
                        type="password" 
                        class="form-control form-control-sm" 
                        v-model="hostForm.password"
                        placeholder="请输入SSH密码"
                        :required="authType === 'password'"
                      />
                    </div>
                  </div>
                  <small class="text-muted d-block mt-1" v-if="editingHost && editingHost.has_password">
                    留空表示不修改密码
                  </small>
                </div>

                <!-- 密钥认证 -->
                <div v-if="authType === 'key'">
                  <div class="mb-3">
                    <label class="form-label">
                      SSH用户名 <span class="text-danger">*</span>
                    </label>
                    <input 
                      type="text" 
                      class="form-control form-control-sm" 
                      v-model="hostForm.username"
                      placeholder="例如：root"
                      required
                    />
                  </div>
                  <div class="mb-3">
                    <label class="form-label">
                      SSH私钥 <span class="text-danger">*</span>
                    </label>
                    <textarea 
                      class="form-control form-control-sm font-monospace" 
                      v-model="hostForm.private_key"
                      rows="4"
                      placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;...&#10;-----END RSA PRIVATE KEY-----"
                      :required="authType === 'key'"
                      style="font-size: 0.8rem;"
                    ></textarea>
                    <small class="text-muted d-block mt-1">支持RSA、Ed25519、ECDSA、DSS格式</small>
                  </div>
                  <div>
                    <label class="form-label small">私钥密码（可选）</label>
                    <input 
                      type="password" 
                      class="form-control form-control-sm" 
                      v-model="hostForm.key_password"
                      placeholder="如果私钥有密码保护，请输入密码"
                    />
                  </div>
                </div>

                <!-- 测试连接 -->
                <div class="mt-3 pt-3 border-top">
                  <button 
                    type="button" 
                    class="btn btn-outline-info btn-sm"
                    @click="testConnectionFromForm"
                    :disabled="testingConnectionForm"
                  >
                    <span v-if="testingConnectionForm" class="spinner-border spinner-border-sm me-1"></span>
                    <i v-else class="fas fa-plug me-1"></i>
                    {{ testingConnectionForm ? '测试中...' : '测试连接' }}
                  </button>
                  
                  <!-- 测试结果 -->
                  <div v-if="testResult" class="mt-2">
                    <div v-if="testResult.success" class="alert alert-success py-2 mb-0">
                      <i class="fas fa-check-circle me-2"></i>
                      <span>{{ testResult.message }}</span>
                      <span v-if="testResult.docker_available" class="ms-2">
                        <i class="fas fa-docker me-1"></i>{{ testResult.docker_version }}
                      </span>
                    </div>
                    <div v-else class="alert alert-danger py-2 mb-0">
                      <i class="fas fa-times-circle me-2"></i>
                      <span>{{ testResult.message }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary btn-sm" @click="closeModal">
              取消
            </button>
            <button 
              type="button" 
              class="btn btn-primary btn-sm" 
              @click="saveHost"
              :disabled="saving || testingConnectionForm"
            >
              <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="fas fa-save me-1"></i>
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'HostManager',
  data() {
    return {
      hosts: [],
      loading: false,
      showAddModal: false,
      showEditModal: false,
      editingHost: null,
      saving: false,
      testingConnection: null,
      testingConnectionForm: false,
      testResult: null,
      authType: 'password',
      hostForm: {
        name: '',
        host: '',
        port: 22,
        username: '',
        password: '',
        private_key: '',
        key_password: '',
        docker_version: null,
        description: ''
      }
    }
  },
  mounted() {
    this.loadHosts()
  },
  methods: {
    async loadHosts() {
      this.loading = true
      try {
        const res = await axios.get('/api/hosts')
        if (res.data.hosts) {
          this.hosts = res.data.hosts || []
          // 自动检测每个主机的Docker信息
          this.checkDockerForAllHosts()
        }
      } catch (error) {
        console.error('加载主机列表失败:', error)
        alert('加载主机列表失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.loading = false
      }
    },
    async checkDockerForAllHosts() {
      // 为每个主机异步检测Docker信息
      for (const host of this.hosts) {
        // 如果已经有Docker版本信息，跳过检测
        if (host.docker_version) {
          continue
        }
        // 如果没有认证信息，跳过检测
        if (!host.has_password && !host.has_private_key) {
          continue
        }
        
        // 标记为检测中
        this.$set(host, 'checking_docker', true)
        
        try {
          const res = await axios.post(`/api/hosts/${host.host_id}/test-ssh`)
          if (res.data.success && res.data.docker_available) {
            this.$set(host, 'docker_available', true)
            if (res.data.docker_version) {
              this.$set(host, 'docker_version', res.data.docker_version)
              // 更新后端保存版本信息
              await axios.put(`/api/hosts/${host.host_id}`, {
                docker_version: res.data.docker_version
              })
            }
          } else {
            this.$set(host, 'docker_available', false)
          }
        } catch (error) {
          console.error(`检测主机 ${host.name} 的Docker信息失败:`, error)
          this.$set(host, 'docker_available', false)
        } finally {
          this.$set(host, 'checking_docker', false)
        }
      }
    },
    closeModal() {
      this.showAddModal = false
      this.showEditModal = false
      this.editingHost = null
      this.testResult = null
      this.authType = 'password'
      this.hostForm = {
        name: '',
        host: '',
        port: 22,
        username: '',
        password: '',
        private_key: '',
        key_password: '',
        docker_version: null,
        description: ''
      }
    },
    editHost(host) {
      this.editingHost = host
      this.showEditModal = true
      this.hostForm = {
        name: host.name,
        host: host.host,
        port: host.port,
        username: host.username,
        password: '', // 不显示密码
        private_key: '', // 不显示私钥
        key_password: '', // 不显示私钥密码
        docker_version: host.docker_version || null,
        description: host.description || ''
      }
      // 根据已有认证方式设置
      if (host.has_private_key) {
        this.authType = 'key'
      } else {
        this.authType = 'password'
      }
      this.testResult = null
    },
    async testConnectionFromForm() {
      if (!this.hostForm.host || !this.hostForm.username) {
        alert('请先填写主机地址和用户名')
        return
      }

      if (this.authType === 'password' && !this.hostForm.password) {
        alert('请填写SSH密码')
        return
      }

      if (this.authType === 'key' && !this.hostForm.private_key) {
        alert('请填写SSH私钥')
        return
      }

      this.testingConnectionForm = true
      this.testResult = null

      try {
        const res = await axios.post('/api/hosts/test-ssh', {
          host: this.hostForm.host,
          port: this.hostForm.port,
          username: this.hostForm.username,
          password: this.authType === 'password' ? this.hostForm.password : null,
          private_key: this.authType === 'key' ? this.hostForm.private_key : null,
          key_password: this.authType === 'key' ? this.hostForm.key_password : null
        })

        this.testResult = res.data

        // 如果测试成功且检测到Docker，更新版本信息
        if (this.testResult.success && this.testResult.docker_available) {
          if (this.testResult.docker_version) {
            this.hostForm.docker_version = this.testResult.docker_version
          }
        }
      } catch (error) {
        console.error('测试SSH连接失败:', error)
        this.testResult = {
          success: false,
          message: error.response?.data?.detail || error.message || '测试连接失败'
        }
      } finally {
        this.testingConnectionForm = false
      }
    },
    async testConnection(host) {
      this.testingConnection = host.host_id

      try {
        // 使用已保存的配置直接测试连接
        const res = await axios.post(`/api/hosts/${host.host_id}/test-ssh`)
        
        if (res.data.success) {
          alert(`✅ 连接成功！\n${res.data.message}${res.data.docker_available ? '\n🐳 Docker可用: ' + res.data.docker_version : '\n⚠️ Docker不可用'}`)
          // 更新Docker版本信息
          if (res.data.docker_available && res.data.docker_version) {
            await axios.put(`/api/hosts/${host.host_id}`, {
              docker_version: res.data.docker_version
            })
          }
          // 重新加载以获取最新状态
          this.loadHosts()
        } else {
          alert(`❌ 连接失败：${res.data.message}`)
        }
      } catch (error) {
        console.error('测试连接失败:', error)
        alert('测试连接失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.testingConnection = null
      }
    },
    async saveHost() {
      // 验证必填字段
      if (!this.hostForm.name || !this.hostForm.host || !this.hostForm.username) {
        alert('请填写必填字段')
        return
      }

      // 验证认证方式
      if (this.authType === 'password' && !this.hostForm.password && !this.editingHost) {
        alert('请填写SSH密码')
        return
      }

      if (this.authType === 'key' && !this.hostForm.private_key && !this.editingHost) {
        alert('请填写SSH私钥')
        return
      }

      this.saving = true
      try {
        const hostData = {}

        // 只传递有值的字段
        hostData.name = this.hostForm.name
        hostData.host = this.hostForm.host
        hostData.port = this.hostForm.port
        hostData.username = this.hostForm.username
        if (this.hostForm.docker_version) {
          hostData.docker_version = this.hostForm.docker_version
        }
        if (this.hostForm.description) {
          hostData.description = this.hostForm.description
        }

        // 根据认证方式添加认证信息
        if (this.authType === 'password') {
          // 新建时必须提供密码，编辑时如果提供了密码则更新
          if (!this.editingHost) {
            // 新建
            hostData.password = this.hostForm.password
            hostData.private_key = null
            hostData.key_password = null
          } else {
            // 编辑
            if (this.hostForm.password) {
              // 如果提供了新密码，则更新
              hostData.password = this.hostForm.password
            }
            // 如果原来使用私钥，现在切换到密码，需要清除私钥
            if (this.editingHost.has_private_key) {
              hostData.private_key = ''
              hostData.key_password = ''
            }
          }
        } else {
          // 密钥认证
          if (!this.editingHost) {
            // 新建
            hostData.private_key = this.hostForm.private_key
            hostData.key_password = this.hostForm.key_password || null
            hostData.password = null
          } else {
            // 编辑
            if (this.hostForm.private_key) {
              // 如果提供了新私钥，则更新
              hostData.private_key = this.hostForm.private_key
              hostData.key_password = this.hostForm.key_password || null
            }
            // 如果原来使用密码，现在切换到密钥，需要清除密码
            if (this.editingHost.has_password) {
              hostData.password = ''
            }
          }
        }

        let res
        if (this.editingHost) {
          res = await axios.put(`/api/hosts/${this.editingHost.host_id}`, hostData)
        } else {
          res = await axios.post('/api/hosts', hostData)
        }

        if (res.data.success) {
          alert(this.editingHost ? '主机更新成功' : '主机添加成功')
          this.closeModal()
          this.loadHosts()
        }
      } catch (error) {
        console.error('保存主机失败:', error)
        alert('保存主机失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.saving = false
      }
    },
    async deleteHost(host) {
      if (!confirm(`确定要删除主机 "${host.name}" 吗？`)) {
        return
      }

      try {
        const res = await axios.delete(`/api/hosts/${host.host_id}`)
        if (res.data.success) {
          alert('主机已删除')
          this.loadHosts()
        }
      } catch (error) {
        console.error('删除主机失败:', error)
        alert('删除主机失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    formatTime(timeStr) {
      if (!timeStr) return '-'
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.host-manager-panel {
  padding: 0;
}

.modal.show {
  display: block;
}

.font-monospace {
  font-family: 'Courier New', Courier, monospace;
}

/* 统一表单控件大小 */
.form-control-sm {
  font-size: 0.875rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #495057;
}

/* 按钮组样式 */
.btn-group .btn-check:checked + .btn {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: white;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .modal-dialog {
    margin: 0.5rem;
  }
}
</style>


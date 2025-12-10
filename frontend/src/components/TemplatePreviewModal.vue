<template>
  <div 
    class="modal fade" 
    :class="{ show: modelValue, 'd-block': modelValue }"
    tabindex="-1"
  >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header bg-info text-white">
          <h5 class="modal-title">
            <i class="fas fa-eye"></i> 模板预览
            <span v-if="template?.name" class="ms-2">{{ template.name }}</span>
            <span v-if="template?.type === 'builtin'" class="badge bg-warning ms-2">
              <i class="fas fa-lock"></i> 内置
            </span>
          </h5>
          <button type="button" class="btn-close btn-close-white" @click="close"></button>
        </div>
        
        <div class="modal-body">
          <div v-if="loading" class="text-center py-4">
            <div class="spinner-border spinner-border-sm me-2"></div>
            加载中...
          </div>
          
          <div v-else>
            <!-- 元数据 -->
            <div class="row mb-3">
              <div class="col-md-3">
                <label class="form-label fw-bold">模板名称</label>
                <div class="form-control-plaintext">{{ templateData?.name || '-' }}</div>
              </div>
              <div class="col-md-3">
                <label class="form-label fw-bold">项目类型</label>
                <div class="form-control-plaintext">
                  <span 
                    class="badge" 
                    :class="template?.project_type === 'jar' ? 'bg-primary' : 'bg-success'"
                  >
                    {{ template?.project_type === 'nodejs' ? 'Node.js' : 'JAR' }}
                  </span>
                </div>
              </div>
              <div class="col-md-3">
                <label class="form-label fw-bold">文件大小</label>
                <div class="form-control-plaintext">{{ formatSize(template?.size) }}</div>
              </div>
              <div class="col-md-3">
                <label class="form-label fw-bold">更新时间</label>
                <div class="form-control-plaintext">{{ formatDate(template?.updated_at) }}</div>
              </div>
            </div>

            <!-- 模板信息：参数和服务阶段 - Tab 布局 -->
            <div v-if="templateInfo && (templateInfo.params?.length > 0 || templateInfo.services?.length > 0)" class="mb-3">
              <ul class="nav nav-tabs mb-3" role="tablist">
                <li class="nav-item" v-if="templateInfo.params && templateInfo.params.length > 0">
                  <button 
                    class="nav-link" 
                    :class="{ active: activeTab === 'params' }"
                    @click="activeTab = 'params'"
                    type="button"
                  >
                    <i class="fas fa-sliders-h"></i> 模板参数 
                    <span class="badge bg-primary ms-1">{{ templateInfo.params.length }}</span>
                  </button>
                </li>
                <li class="nav-item" v-if="templateInfo.services && templateInfo.services.length > 0">
                  <button 
                    class="nav-link" 
                    :class="{ active: activeTab === 'services' }"
                    @click="activeTab = 'services'"
                    type="button"
                  >
                    <i class="fas fa-server"></i> 服务阶段 
                    <span class="badge bg-info ms-1">{{ templateInfo.services.length }}</span>
                  </button>
                </li>
              </ul>
              
              <div class="tab-content">
                <!-- 模板参数 Tab -->
                <div 
                  v-if="templateInfo.params && templateInfo.params.length > 0"
                  class="tab-pane fade" 
                  :class="{ 'show active': activeTab === 'params' }"
                >
                  <div class="card border-primary">
                    <div class="card-body p-3">
                      <div class="row g-2">
                        <div 
                          v-for="param in templateInfo.params" 
                          :key="param.name" 
                          class="col-md-6 col-lg-4"
                        >
                          <div class="card bg-light h-100">
                            <div class="card-body p-2">
                              <div class="d-flex align-items-start justify-content-between">
                                <div class="flex-grow-1">
                                  <code class="text-primary fw-bold">{{ param.name }}</code>
                                  <div v-if="param.default" class="text-muted small mt-1">
                                    默认值: <code class="text-dark">{{ param.default }}</code>
                                  </div>
                                </div>
                                <span v-if="param.required" class="badge bg-danger ms-2">必填</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 服务阶段 Tab -->
                <div 
                  v-if="templateInfo.services && templateInfo.services.length > 0"
                  class="tab-pane fade" 
                  :class="{ 'show active': activeTab === 'services' }"
                >
                  <div class="card border-info">
                    <div class="card-body p-3">
                      <div class="table-responsive">
                        <table class="table table-hover table-sm mb-0">
                          <thead class="table-light">
                            <tr>
                              <th style="width: 40%;">服务名称</th>
                              <th style="width: 30%;">端口</th>
                              <th style="width: 30%;">用户</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="service in templateInfo.services" :key="service.name">
                              <td>
                                <code class="text-primary">{{ service.name }}</code>
                              </td>
                              <td>
                                <span v-if="service.port" class="badge bg-secondary">{{ service.port }}</span>
                                <span v-else class="text-muted">-</span>
                              </td>
                              <td>
                                <span v-if="service.user" class="badge bg-info">{{ service.user }}</span>
                                <span v-else class="text-muted">-</span>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- CodeMirror 只读预览 -->
            <div class="mb-2">
              <label class="form-label fw-bold">
                <i class="fas fa-file-code"></i> 模板内容
              </label>
            </div>
            <codemirror
              v-model="content"
              :style="{ height: '500px', fontSize: '13px' }"
              :disabled="true"
              :extensions="extensions"
            />
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="close">
            <i class="fas fa-times"></i> 关闭
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <div v-if="modelValue" class="modal-backdrop fade show"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { Codemirror } from 'vue-codemirror'
import { oneDark } from '@codemirror/theme-one-dark'
import { StreamLanguage } from '@codemirror/language'
import { shell } from '@codemirror/legacy-modes/mode/shell'

const props = defineProps({
  modelValue: Boolean,
  template: Object
})

const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const content = ref('')
const templateData = ref(null)
const templateInfo = ref(null)  // 模板信息（参数和服务阶段）
const activeTab = ref('params')  // 当前激活的 tab

// CodeMirror 扩展配置（只读模式）
const extensions = [
  oneDark,
  StreamLanguage.define(shell)
]

watch(() => props.modelValue, async (show) => {
  if (show && props.template) {
    loading.value = true
    templateInfo.value = null
    // 重置 tab，优先显示参数 tab，如果没有参数则显示服务 tab
    activeTab.value = 'params'
    
    try {
      // 加载模板内容
      const res = await axios.get(`/api/templates?name=${encodeURIComponent(props.template.name)}`)
      templateData.value = res.data
      content.value = res.data.content || ''
      
      // 加载模板参数和服务阶段信息
      try {
        const infoRes = await axios.get('/api/template-params', {
          params: {
            template: props.template.name,
            project_type: props.template.project_type
          }
        })
        templateInfo.value = {
          params: infoRes.data.params || [],
          services: infoRes.data.services || []
        }
        // 如果没有参数但有服务，默认显示服务 tab
        if ((!templateInfo.value.params || templateInfo.value.params.length === 0) && 
            templateInfo.value.services && templateInfo.value.services.length > 0) {
          activeTab.value = 'services'
        }
      } catch (infoError) {
        console.error('加载模板信息失败:', infoError)
        // 不影响主流程，只记录错误
        templateInfo.value = {
          params: [],
          services: []
        }
      }
    } catch (error) {
      console.error('加载模板内容失败:', error)
      alert('加载模板内容失败')
      close()
    } finally {
      loading.value = false
    }
  }
})

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.modal.show {
  display: block !important;
}

.modal-backdrop.show {
  opacity: 0.5;
}

.nav-tabs {
  border-bottom: 2px solid #dee2e6;
}

.nav-tabs .nav-link {
  border: none;
  border-bottom: 2px solid transparent;
  color: #6c757d;
  padding: 0.75rem 1.25rem;
  transition: all 0.2s;
}

.nav-tabs .nav-link:hover {
  border-bottom-color: #dee2e6;
  color: #0d6efd;
}

.nav-tabs .nav-link.active {
  color: #0d6efd;
  border-bottom-color: #0d6efd;
  background-color: transparent;
  font-weight: 500;
}

.tab-content {
  min-height: 150px;
}

.tab-pane {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

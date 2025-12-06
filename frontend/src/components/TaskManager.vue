<template>
  <div class="task-manager">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">
        <i class="fas fa-tasks"></i> 任务管理
      </h5>
      <div class="d-flex gap-2 align-items-center">
        <select v-model="statusFilter" class="form-select form-select-sm" style="width: auto;">
          <option value="">全部状态</option>
          <option value="pending">等待中</option>
          <option value="running">进行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        <select v-model="categoryFilter" class="form-select form-select-sm" style="width: auto;">
          <option value="">全部类型</option>
          <option value="build">构建任务</option>
          <option value="export">导出任务</option>
        </select>
        <button class="btn btn-sm btn-outline-primary" @click="loadTasks">
          <i class="fas fa-sync-alt"></i> 刷新
        </button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
    </div>

    <div v-else-if="filteredTasks.length === 0" class="text-center py-4 text-muted">
      <i class="fas fa-inbox fa-2x mb-2"></i>
      <p class="mb-0">暂无任务</p>
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th style="width: 100px;">类型</th>
            <th style="width: 200px;">镜像/任务</th>
            <th style="width: 100px;">标签</th>
            <th style="width: 120px;">状态</th>
            <th style="width: 150px;">创建时间</th>
            <th style="width: 100px;">时长</th>
            <th style="width: 100px;">文件大小</th>
            <th style="width: 200px;" class="text-end">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in filteredTasks" :key="task.task_id">
            <td>
              <span v-if="task.task_category === 'build'" class="badge bg-info">
                <i class="fas fa-hammer"></i> 构建
              </span>
              <span v-else class="badge bg-secondary">
                <i class="fas fa-download"></i> 导出
              </span>
            </td>
            <td>
              <code class="small">{{ task.image || (task.task_type ? task.task_type : '未知') }}</code>
            </td>
            <td>{{ task.tag || '-' }}</td>
            <td>
              <span v-if="task.status === 'pending'" class="badge bg-secondary">
                <i class="fas fa-clock"></i> 等待中
              </span>
              <span v-else-if="task.status === 'running'" class="badge bg-primary">
                <span class="spinner-border spinner-border-sm me-1"></span> 进行中
              </span>
              <span v-else-if="task.status === 'completed'" class="badge bg-success">
                <i class="fas fa-check-circle"></i> 已完成
              </span>
              <span v-else-if="task.status === 'failed'" class="badge bg-danger">
                <i class="fas fa-times-circle"></i> 失败
              </span>
            </td>
            <td class="small text-muted">
              {{ formatTime(task.created_at) }}
            </td>
            <td class="small">
              <span v-if="task.status === 'running'" class="text-primary">
                <span class="spinner-border spinner-border-sm me-1" style="width: 0.7rem; height: 0.7rem;"></span>
                {{ calculateDuration(task.created_at, null) }}
              </span>
              <span v-else-if="task.completed_at" :class="{'text-success': task.status === 'completed', 'text-danger': task.status === 'failed'}">
                {{ calculateDuration(task.created_at, task.completed_at) }}
              </span>
              <span v-else class="text-muted">-</span>
            </td>
            <td class="small">
              <span v-if="task.file_size">{{ formatFileSize(task.file_size) }}</span>
              <span v-else>-</span>
            </td>
            <td class="text-end">
              <div class="btn-group btn-group-sm">
                <button 
                  v-if="task.task_category === 'build'"
                  class="btn btn-sm btn-outline-info"
                  @click="viewLogs(task)"
                  :disabled="viewingLogs === task.task_id"
                  :title="'查看构建日志'"
                >
                  <i class="fas fa-terminal"></i> 日志
                </button>
                <button 
                  v-if="task.status === 'failed' && task.error"
                  class="btn btn-sm btn-outline-warning"
                  @click="showErrorDetails(task)"
                  :title="'查看错误详情'"
                >
                  <i class="fas fa-exclamation-triangle"></i> 错误
                </button>
                <button 
                  v-if="task.task_category === 'export' && task.status === 'completed'"
                  class="btn btn-sm btn-success"
                  @click="downloadTask(task)"
                  :disabled="downloading === task.task_id"
                  :title="'下载导出文件'"
                >
                  <i class="fas fa-download"></i>
                  <span v-if="downloading === task.task_id" class="spinner-border spinner-border-sm ms-1"></span>
                </button>
                <button 
                  class="btn btn-sm btn-outline-danger"
                  @click="deleteTask(task)"
                  :disabled="deleting === task.task_id"
                  :title="'删除任务'"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="alert alert-danger mt-3 mb-0">
      <i class="fas fa-exclamation-circle"></i> {{ error }}
    </div>

    <!-- 错误详情模态框 -->
    <div v-if="showErrorModal && selectedErrorTask" class="modal fade show" style="display: block;" tabindex="-1" @click.self="closeErrorModal">
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header bg-danger text-white">
            <h5 class="modal-title">
              <i class="fas fa-exclamation-triangle"></i> 任务错误详情
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeErrorModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <strong>任务信息:</strong>
              <div class="mt-1">
                <code>{{ selectedErrorTask.image || selectedErrorTask.task_type }}:{{ selectedErrorTask.tag || 'latest' }}</code>
              </div>
            </div>
            <div class="mb-3">
              <strong>任务类型:</strong>
              <span class="badge" :class="selectedErrorTask.task_category === 'build' ? 'bg-info' : 'bg-secondary'">
                {{ selectedErrorTask.task_category === 'build' ? '构建任务' : '导出任务' }}
              </span>
            </div>
            <div class="mb-3">
              <strong>创建时间:</strong> {{ formatTime(selectedErrorTask.created_at) }}
            </div>
            <div class="mb-3" v-if="selectedErrorTask.completed_at">
              <strong>失败时间:</strong> {{ formatTime(selectedErrorTask.completed_at) }}
            </div>
            <div>
              <strong>错误信息:</strong>
              <pre class="bg-dark text-light p-3 rounded mt-2" style="max-height: 300px; overflow-y: auto; font-size: 0.85rem;">{{ selectedErrorTask.error }}</pre>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeErrorModal">关闭</button>
            <button 
              v-if="selectedErrorTask.task_category === 'build'"
              type="button" 
              class="btn btn-info" 
              @click="viewLogsFromError(selectedErrorTask)"
            >
              <i class="fas fa-terminal"></i> 查看完整日志
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showErrorModal" class="modal-backdrop fade show" @click="closeErrorModal"></div>

    <!-- 日志模态框 -->
    <div v-if="showLogModal && selectedTask" class="modal fade show" style="display: block;" tabindex="-1" @click.self="closeLogModal">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">任务日志 - {{ selectedTask.image }}:{{ selectedTask.tag }}</h5>
            <button type="button" class="btn-close" @click="closeLogModal"></button>
          </div>
          <div class="modal-body">
            <pre class="bg-dark text-light p-3 rounded" style="max-height: 500px; overflow-y: auto; font-size: 0.85rem;">{{ taskLogs }}</pre>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeLogModal">关闭</button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showLogModal" class="modal-backdrop fade show" @click="closeLogModal"></div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { computed, onMounted, onUnmounted, ref } from 'vue'

const tasks = ref([])
const loading = ref(false)
const error = ref(null)
const statusFilter = ref('')
const categoryFilter = ref('')
const downloading = ref(null)
const deleting = ref(null)
const viewingLogs = ref(null)
const showLogModal = ref(false)
const selectedTask = ref(null)
const taskLogs = ref('')
const showErrorModal = ref(false)
const selectedErrorTask = ref(null)
let refreshInterval = null

const filteredTasks = computed(() => {
  let result = tasks.value
  if (statusFilter.value) {
    result = result.filter(t => t.status === statusFilter.value)
  }
  if (categoryFilter.value) {
    result = result.filter(t => t.task_category === categoryFilter.value)
  }
  return result
})

function showErrorDetails(task) {
  selectedErrorTask.value = task
  showErrorModal.value = true
}

function closeErrorModal() {
  showErrorModal.value = false
  selectedErrorTask.value = null
}

function viewLogsFromError(task) {
  closeErrorModal()
  viewLogs(task)
}

function formatTime(isoString) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  
  // 显示完整精确时间（包括年月日时分秒）
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

function calculateDuration(startTime, endTime) {
  if (!startTime) return '-'
  
  const start = new Date(startTime)
  const end = endTime ? new Date(endTime) : new Date()
  
  const diffMs = end - start
  if (diffMs < 0) return '-'
  
  const seconds = Math.floor(diffMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes % 60}分`
  } else if (minutes > 0) {
    return `${minutes}分${seconds % 60}秒`
  } else {
    return `${seconds}秒`
  }
}

async function loadTasks() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    const res = await axios.get('/api/tasks', { params })
    tasks.value = res.data.tasks || []
  } catch (err) {
    error.value = err.response?.data?.error || err.message || '加载任务列表失败'
    console.error('加载任务列表失败:', err)
  } finally {
    loading.value = false
  }
}

async function viewLogs(task) {
  if (viewingLogs.value) return
  
  viewingLogs.value = task.task_id
  selectedTask.value = task
  showLogModal.value = true
  taskLogs.value = '加载中...'
  
  try {
    const res = await axios.get(`/api/build-tasks/${task.task_id}/logs`)
    // 直接使用 res.data,不设置 responseType
    if (typeof res.data === 'string') {
      taskLogs.value = res.data || '暂无日志'
    } else {
      // 如果返回的不是字符串,尝试转换
      taskLogs.value = JSON.stringify(res.data, null, 2)
    }
  } catch (err) {
    console.error('获取日志失败:', err)
    const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || '未知错误'
    taskLogs.value = `加载日志失败: ${errorMsg}`
  } finally {
    viewingLogs.value = null
  }
}

function closeLogModal() {
  showLogModal.value = false
  selectedTask.value = null
  taskLogs.value = ''
}

async function downloadTask(task) {
  if (downloading.value) return
  
  downloading.value = task.task_id
  try {
    const res = await axios.get(`/api/export-tasks/${task.task_id}/download`, {
      responseType: 'blob'
    })
    
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    
    // 生成文件名
    const image = task.image.replace(/\//g, '_')
    const tag = task.tag || 'latest'
    // 检查 compress 字段，支持多种格式
    const isCompressed = task.compress && ['gzip', 'gz', 'tgz', '1', 'true', 'yes'].includes(task.compress.toLowerCase())
    const ext = isCompressed ? '.tar.gz' : '.tar'
    a.download = `${image}-${tag}${ext}`
    
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('下载失败:', err)
    const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || '下载失败'
    error.value = `下载失败: ${errorMsg}`
    // 3秒后自动清除错误提示
    setTimeout(() => {
      if (error.value && error.value.includes('下载失败')) {
        error.value = null
      }
    }, 3000)
  } finally {
    downloading.value = null
  }
}

async function deleteTask(task) {
  const taskName = task.image || task.task_type || '未知任务'
  const taskTag = task.tag || '-'
  if (!confirm(`确定要删除任务 "${taskName}:${taskTag}" 吗？`)) {
    return
  }
  
  deleting.value = task.task_id
  try {
    if (task.task_category === 'build') {
      await axios.delete(`/api/build-tasks/${task.task_id}`)
    } else {
      await axios.delete(`/api/export-tasks/${task.task_id}`)
    }
    // 成功删除后刷新列表
    await loadTasks()
  } catch (err) {
    console.error('删除任务失败:', err)
    const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || '删除失败'
    error.value = `删除任务失败: ${errorMsg}`
    // 5秒后自动清除错误提示
    setTimeout(() => {
      if (error.value && error.value.includes('删除任务失败')) {
        error.value = null
      }
    }, 5000)
  } finally {
    deleting.value = null
  }
}

onMounted(() => {
  loadTasks()
  // 每5秒自动刷新一次（只刷新进行中的任务）
  refreshInterval = setInterval(() => {
    const hasRunning = tasks.value.some(t => t.status === 'running' || t.status === 'pending')
    if (hasRunning) {
      loadTasks()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.task-manager {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.table {
  font-size: 0.9rem;
}

code {
  font-size: 0.85rem;
  background-color: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>


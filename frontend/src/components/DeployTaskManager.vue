<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">
        <i class="fas fa-rocket text-primary"></i> 部署任务管理
      </h5>
      <div>
        <button class="btn btn-primary btn-sm" @click="showImportModal = true">
          <i class="fas fa-file-import me-1"></i> 导入配置
        </button>
        <button class="btn btn-success btn-sm ms-2" @click="showCreateModal = true">
          <i class="fas fa-plus me-1"></i> 新建任务
        </button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th width="10%">任务ID</th>
            <th width="15%">应用名称</th>
            <th width="10%">状态</th>
            <th width="15%">目标主机</th>
            <th width="15%">创建时间</th>
            <th width="15%">完成时间</th>
            <th width="20%">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="text-center py-4">
              <div class="spinner-border spinner-border-sm me-2"></div>
              加载中...
            </td>
          </tr>
          <tr v-else-if="tasks.length === 0">
            <td colspan="7" class="text-center py-4 text-muted">
              暂无部署任务
            </td>
          </tr>
          <tr v-else v-for="task in tasks" :key="task.task_id">
            <td>
              <code class="small">{{ task.task_id.substring(0, 8) }}</code>
            </td>
            <td>{{ task.config?.app?.name || '-' }}</td>
            <td>
              <span :class="getStatusBadgeClass(task.status?.status)" class="badge">
                {{ getStatusText(task.status?.status) }}
              </span>
            </td>
            <td>
              <span v-for="(target, idx) in task.status?.targets || []" :key="idx" class="badge bg-secondary me-1">
                {{ target.name }}
              </span>
            </td>
            <td>{{ formatTime(task.status?.created_at) }}</td>
            <td>{{ formatTime(task.status?.completed_at) || '-' }}</td>
            <td>
              <button class="btn btn-sm btn-outline-primary me-1" @click="viewTask(task)">
                <i class="fas fa-eye"></i> 查看
              </button>
              <button 
                v-if="task.status?.status === 'pending' || task.status?.status === 'failed'"
                class="btn btn-sm btn-outline-success me-1" 
                @click="executeTask(task)"
              >
                <i class="fas fa-play"></i> 执行
              </button>
              <button class="btn btn-sm btn-outline-info me-1" @click="exportTask(task)">
                <i class="fas fa-download"></i> 导出
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteTask(task)">
                <i class="fas fa-trash"></i> 删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建任务模态框 -->
    <div v-if="showCreateModal" class="modal fade show d-block" style="background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-plus me-2"></i> 新建部署任务
            </h5>
            <button type="button" class="btn-close" @click="showCreateModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">YAML 配置内容</label>
              <textarea 
                v-model="taskConfigContent" 
                class="form-control font-monospace" 
                rows="20"
                placeholder="请输入 deploy-config.yaml 格式的配置..."
              ></textarea>
            </div>
            <div class="row">
              <div class="col-md-6">
                <label class="form-label">镜像仓库（可选）</label>
                <input v-model="taskRegistry" type="text" class="form-control" placeholder="docker.io">
              </div>
              <div class="col-md-6">
                <label class="form-label">镜像标签（可选）</label>
                <input v-model="taskTag" type="text" class="form-control" placeholder="latest">
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">取消</button>
            <button type="button" class="btn btn-primary" @click="createTask" :disabled="creating">
              <span v-if="creating" class="spinner-border spinner-border-sm me-2"></span>
              创建
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 导入任务模态框 -->
    <div v-if="showImportModal" class="modal fade show d-block" style="background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-file-import me-2"></i> 导入部署配置
            </h5>
            <button type="button" class="btn-close" @click="showImportModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">选择 YAML 文件</label>
              <input type="file" class="form-control" @change="handleFileImport" accept=".yaml,.yml">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showImportModal = false">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务详情模态框 -->
    <div v-if="showDetailModal && selectedTask" class="modal fade show d-block" style="background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-info-circle me-2"></i> 任务详情 - {{ selectedTask.task_id.substring(0, 8) }}
            </h5>
            <button type="button" class="btn-close" @click="showDetailModal = false"></button>
          </div>
          <div class="modal-body">
            <ul class="nav nav-tabs mb-3">
              <li class="nav-item">
                <button class="nav-link" :class="{ active: detailTab === 'config' }" @click="detailTab = 'config'">
                  配置信息
                </button>
              </li>
              <li class="nav-item">
                <button class="nav-link" :class="{ active: detailTab === 'status' }" @click="detailTab = 'status'">
                  执行状态
                </button>
              </li>
            </ul>

            <div v-if="detailTab === 'config'">
              <pre class="bg-dark text-light p-3 rounded" style="max-height: 500px; overflow-y: auto;"><code>{{ selectedTask.config_content }}</code></pre>
            </div>

            <div v-if="detailTab === 'status'">
              <div class="mb-3">
                <strong>任务状态:</strong>
                <span :class="getStatusBadgeClass(selectedTask.status?.status)" class="badge ms-2">
                  {{ getStatusText(selectedTask.status?.status) }}
                </span>
              </div>
              <div v-if="selectedTask.status?.targets" class="mb-3">
                <strong>目标主机执行状态:</strong>
                <table class="table table-sm mt-2">
                  <thead>
                    <tr>
                      <th>主机名称</th>
                      <th>状态</th>
                      <th>结果</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="target in selectedTask.status.targets" :key="target.name">
                      <td>{{ target.name }}</td>
                      <td>
                        <span :class="getStatusBadgeClass(target.status)" class="badge">
                          {{ getStatusText(target.status) }}
                        </span>
                      </td>
                      <td>
                        <span v-if="target.result" class="text-muted small">
                          {{ target.result.message || '-' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showDetailModal = false">关闭</button>
            <button 
              v-if="selectedTask.status?.status === 'pending' || selectedTask.status?.status === 'failed'"
              class="btn btn-success" 
              @click="executeTask(selectedTask)"
            >
              <i class="fas fa-play me-1"></i> 执行任务
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
  name: 'DeployTaskManager',
  data() {
    return {
      tasks: [],
      loading: false,
      showCreateModal: false,
      showImportModal: false,
      showDetailModal: false,
      selectedTask: null,
      detailTab: 'config',
      taskConfigContent: '',
      taskRegistry: '',
      taskTag: '',
      creating: false
    }
  },
  mounted() {
    this.loadTasks()
  },
  methods: {
    async loadTasks() {
      this.loading = true
      try {
        const res = await axios.get('/api/deploy-tasks')
        this.tasks = res.data.tasks || []
      } catch (error) {
        console.error('加载部署任务失败:', error)
        alert('加载部署任务失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.loading = false
      }
    },
    async createTask() {
      if (!this.taskConfigContent.trim()) {
        alert('请输入配置内容')
        return
      }
      
      this.creating = true
      try {
        await axios.post('/api/deploy-tasks', {
          config_content: this.taskConfigContent,
          registry: this.taskRegistry || null,
          tag: this.taskTag || null
        })
        alert('创建成功')
        this.showCreateModal = false
        this.taskConfigContent = ''
        this.taskRegistry = ''
        this.taskTag = ''
        this.loadTasks()
      } catch (error) {
        console.error('创建部署任务失败:', error)
        alert('创建部署任务失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.creating = false
      }
    },
    async handleFileImport(event) {
      const file = event.target.files[0]
      if (!file) return
      
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const content = e.target.result
          const formData = new FormData()
          formData.append('file', file)
          
          await axios.post('/api/deploy-tasks/import', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
          alert('导入成功')
          this.showImportModal = false
          this.loadTasks()
        } catch (error) {
          console.error('导入部署任务失败:', error)
          alert('导入部署任务失败: ' + (error.response?.data?.detail || error.message))
        }
      }
      reader.readAsText(file)
    },
    async executeTask(task) {
      if (!confirm('确定要执行此部署任务吗？')) return
      
      try {
        await axios.post(`/api/deploy-tasks/${task.task_id}/execute`)
        alert('任务已开始执行')
        this.loadTasks()
        if (this.showDetailModal) {
          this.viewTask(task)
        }
      } catch (error) {
        console.error('执行部署任务失败:', error)
        alert('执行部署任务失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    async deleteTask(task) {
      if (!confirm('确定要删除此部署任务吗？')) return
      
      try {
        await axios.delete(`/api/deploy-tasks/${task.task_id}`)
        alert('删除成功')
        this.loadTasks()
        if (this.showDetailModal && this.selectedTask?.task_id === task.task_id) {
          this.showDetailModal = false
        }
      } catch (error) {
        console.error('删除部署任务失败:', error)
        alert('删除部署任务失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    async exportTask(task) {
      try {
        const res = await axios.get(`/api/deploy-tasks/${task.task_id}/export`, {
          responseType: 'blob'
        })
        const blob = new Blob([res.data], { type: 'application/x-yaml' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `deploy-task-${task.task_id}.yaml`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('导出部署任务失败:', error)
        alert('导出部署任务失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    async viewTask(task) {
      try {
        const res = await axios.get(`/api/deploy-tasks/${task.task_id}`)
        this.selectedTask = res.data.task
        this.detailTab = 'config'
        this.showDetailModal = true
      } catch (error) {
        console.error('获取任务详情失败:', error)
        alert('获取任务详情失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    getStatusBadgeClass(status) {
      const map = {
        'pending': 'bg-secondary',
        'running': 'bg-primary',
        'completed': 'bg-success',
        'failed': 'bg-danger'
      }
      return map[status] || 'bg-secondary'
    },
    getStatusText(status) {
      const map = {
        'pending': '待执行',
        'running': '执行中',
        'completed': '已完成',
        'failed': '失败'
      }
      return map[status] || status || '未知'
    },
    formatTime(time) {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.modal {
  z-index: 1050;
}
</style>


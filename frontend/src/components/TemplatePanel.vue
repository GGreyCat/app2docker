<template>
  <div class="template-panel">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="mb-0">
        <i class="fas fa-layer-group"></i> 模板列表
      </h6>
      <button class="btn btn-primary btn-sm" @click="openEditor(null, true)">
        <i class="fas fa-plus-circle"></i> 新增模板
      </button>
    </div>

    <!-- 模板列表表格 -->
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>模板名称</th>
            <th>项目类型</th>
            <th>文件大小</th>
            <th>更新时间</th>
            <th class="text-end">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="text-center py-4">
              <div class="spinner-border spinner-border-sm me-2"></div>
              加载中...
            </td>
          </tr>
          <tr v-else-if="templates.length === 0">
            <td colspan="5" class="text-center text-muted py-4">
              <i class="fas fa-file-code fa-2x mb-2 d-block"></i>
              暂无模板，请点击"新增模板"创建
            </td>
          </tr>
          <tr v-for="tpl in templates" :key="tpl.name">
            <td>
              <strong>{{ tpl.name }}</strong>
              <i v-if="tpl.type === 'builtin'" class="fas fa-lock text-muted ms-1" title="内置模板"></i>
            </td>
            <td>
              <span 
                class="badge" 
                :class="tpl.project_type === 'jar' ? 'bg-primary' : 'bg-success'"
              >
                {{ tpl.project_type === 'jar' ? 'JAR' : 'Node.js' }}
              </span>
            </td>
            <td>{{ formatBytes(tpl.size) }}</td>
            <td>{{ formatTime(tpl.updated_at) }}</td>
            <td class="text-end">
              <div class="btn-group btn-group-sm">
                <button 
                  class="btn btn-outline-secondary" 
                  @click="previewTemplate(tpl)"
                  title="预览"
                >
                  <i class="fas fa-eye"></i>
                </button>
                <button 
                  class="btn btn-outline-primary" 
                  @click="openEditor(tpl, false)"
                  title="编辑"
                >
                  <i class="fas fa-pen"></i>
                </button>
                <button 
                  class="btn btn-outline-danger" 
                  @click="deleteTemplate(tpl)"
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

    <!-- 模板编辑器模态框 -->
    <TemplateEditorModal 
      v-model="showEditor"
      :template="currentTemplate"
      :is-new="isNew"
      @saved="handleSaved"
    />

    <!-- 模板预览模态框 -->
    <TemplatePreviewModal 
      v-model="showPreview"
      :template="currentTemplate"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import TemplateEditorModal from './TemplateEditorModal.vue'
import TemplatePreviewModal from './TemplatePreviewModal.vue'

const templates = ref([])
const loading = ref(false)
const showEditor = ref(false)
const showPreview = ref(false)
const currentTemplate = ref(null)
const isNew = ref(false)

async function loadTemplates() {
  loading.value = true
  try {
    const res = await axios.get('/api/templates')
    templates.value = res.data.items || []
  } catch (error) {
    console.error('加载模板失败:', error)
    alert('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

function openEditor(tpl, isNewTemplate) {
  currentTemplate.value = tpl
  isNew.value = isNewTemplate
  showEditor.value = true
}

function previewTemplate(tpl) {
  currentTemplate.value = tpl
  showPreview.value = true
}

async function deleteTemplate(tpl) {
  const msg = tpl.type === 'builtin'
    ? `此为内置模板，删除后仍可通过系统恢复。\n确认删除用户覆盖的 ${tpl.name} 吗？`
    : `确认删除模板 ${tpl.name} 吗？该操作不可恢复。`
  
  if (!confirm(msg)) return
  
  try {
    await axios.delete('/api/templates', {
      data: { name: tpl.name }
    })
    
    alert('模板已删除')
    await loadTemplates()
  } catch (error) {
    alert(error.response?.data?.error || '删除失败')
  }
}

function handleSaved() {
  loadTemplates()
}

function formatBytes(bytes) {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let idx = 0
  let value = bytes
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024
    idx++
  }
  return `${value.toFixed(value < 10 && idx > 0 ? 1 : 0)} ${units[idx]}`
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  try {
    return new Date(timeStr).toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-panel {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.table th {
  font-weight: 600;
  font-size: 0.9rem;
}
</style>

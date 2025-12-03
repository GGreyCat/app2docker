<template>
  <div 
    class="modal fade" 
    :class="{ show: modelValue, 'd-block': modelValue }"
    tabindex="-1"
    @click.self="close"
  >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header bg-primary text-white">
          <h5 class="modal-title">
            <i class="fas fa-code"></i>
            {{ isNew ? '新增模板' : '编辑模板' }}
            <span v-if="isBuiltin" class="badge bg-warning ms-2">
              <i class="fas fa-lock"></i> 内置
            </span>
          </h5>
          <button type="button" class="btn-close btn-close-white" @click="close"></button>
        </div>
        
        <div class="modal-body">
          <!-- 元数据 -->
          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label">模板名称 <span class="text-danger">*</span></label>
              <input 
                v-model="form.name" 
                type="text" 
                class="form-control"
                :disabled="isBuiltin"
                placeholder="例如: my-custom-template"
              />
              <div v-if="isBuiltin" class="form-text text-warning">
                <i class="fas fa-info-circle"></i> 内置模板不可重命名，保存后将在用户目录创建覆盖
              </div>
            </div>
            <div class="col-md-6">
              <label class="form-label">项目类型 <span class="text-danger">*</span></label>
              <select 
                v-model="form.projectType" 
                class="form-select"
                :disabled="isBuiltin"
              >
                <option value="jar">Java 应用（JAR）</option>
                <option value="nodejs">Node.js 应用</option>
              </select>
              <div class="form-text">
                模板将保存到 data/templates/{{ form.projectType }}/ 目录
              </div>
            </div>
          </div>

          <!-- CodeMirror 编辑器 -->
          <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <label class="form-label mb-0">
                模板内容 <span class="text-danger">*</span>
              </label>
              <div class="btn-group btn-group-sm">
                <button 
                  type="button" 
                  class="btn btn-outline-secondary btn-sm"
                  @click="$refs.fileInput.click()"
                >
                  <i class="fas fa-upload"></i> 从文件加载
                </button>
              </div>
            </div>
            <input 
              ref="fileInput"
              type="file" 
              class="d-none"
              accept=".dockerfile,.Dockerfile,.txt"
              @change="handleFileUpload"
            />
            <codemirror
              v-model="form.content"
              :style="{ height: '500px', fontSize: '13px' }"
              :autofocus="true"
              :indent-with-tab="false"
              :tab-size="4"
              :extensions="extensions"
            />
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" @click="close">
            <i class="fas fa-times"></i> 取消
          </button>
          <button type="button" class="btn btn-primary" @click="save" :disabled="saving">
            <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="fas fa-save"></i>
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <div v-if="modelValue" class="modal-backdrop fade show"></div>
</template>

<script setup>
import { ref, watch, computed, shallowRef, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { Codemirror } from 'vue-codemirror'
import { oneDark } from '@codemirror/theme-one-dark'
import { StreamLanguage } from '@codemirror/language'
import { shell } from '@codemirror/legacy-modes/mode/shell'

const props = defineProps({
  modelValue: Boolean,
  template: Object,
  isNew: Boolean
})

const emit = defineEmits(['update:modelValue', 'saved'])

const form = ref({
  name: '',
  projectType: 'jar',
  content: ''
})

const saving = ref(false)
const originalName = ref('')
const fileInput = ref(null)

// CodeMirror 扩展配置
const extensions = [
  oneDark,
  StreamLanguage.define(shell)  // 使用 shell 模式近似 Dockerfile
]

const isBuiltin = computed(() => {
  return props.template?.type === 'builtin'
})

// ESC键关闭
function handleEscape(e) {
  if (e.key === 'Escape' && props.modelValue) {
    close()
  }
}

watch(() => props.modelValue, async (show) => {
  if (show) {
    if (props.isNew) {
      // 新建模板
      form.value = {
        name: '',
        projectType: 'jar',
        content: '# 新建 Dockerfile 模板\nFROM \n\nCOPY . /app\nWORKDIR /app\n\nEXPOSE 8080\n\nCMD []'
      }
      originalName.value = ''
    } else if (props.template) {
      // 编辑现有模板
      try {
        const res = await axios.get(`/api/templates?name=${encodeURIComponent(props.template.name)}`)
        form.value = {
          name: res.data.name,
          projectType: props.template.project_type || 'jar',
          content: res.data.content || ''
        }
        originalName.value = res.data.name
      } catch (error) {
        alert('加载模板内容失败')
        close()
      }
    }
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})

function handleFileUpload(e) {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (ev) => {
      form.value.content = ev.target.result
      // 如果是新建且未填写名称，从文件名提取
      if (props.isNew && !form.value.name) {
        const baseName = file.name
          .replace(/\.Dockerfile$/i, '')
          .replace(/\.[^/.]+$/, '')
          .replace(/[^a-zA-Z0-9_-]/g, '-')
        form.value.name = baseName
      }
    }
    reader.readAsText(file)
  }
}

async function save() {
  if (!form.value.name.trim()) {
    alert('模板名称不能为空')
    return
  }
  if (!form.value.content.trim()) {
    alert('模板内容不能为空')
    return
  }
  
  saving.value = true
  try {
    const payload = {
      name: form.value.name.trim(),
      content: form.value.content,
      project_type: form.value.projectType
    }
    
    if (!props.isNew) {
      payload.original_name = originalName.value
    }
    
    const method = props.isNew ? 'post' : 'put'
    const res = await axios[method]('/api/templates', payload)
    
    alert(res.data.message || '模板保存成功')
    emit('saved')
    close()
  } catch (error) {
    alert(error.response?.data?.error || '保存失败')
  } finally {
    saving.value = false
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
</style>

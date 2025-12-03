<template>
  <div class="compose-panel">
    <ul class="nav nav-pills nav-fill mb-3">
      <li class="nav-item">
        <button 
          class="nav-link" 
          :class="{ active: inputMode === 'file' }"
          @click="inputMode = 'file'"
          type="button"
        >
          <i class="fas fa-file-upload"></i> 上传文件
        </button>
      </li>
      <li class="nav-item">
        <button 
          class="nav-link" 
          :class="{ active: inputMode === 'text' }"
          @click="inputMode = 'text'"
          type="button"
        >
          <i class="fas fa-edit"></i> 文本输入
        </button>
      </li>
    </ul>

    <div class="mb-3">
      <input 
        v-if="inputMode === 'file'"
        type="file" 
        class="form-control" 
        accept=".yml,.yaml,.YML,.YAML,.txt"
        @change="handleFileChange"
      />
      <textarea 
        v-else
        v-model="composeText" 
        class="form-control font-monospace" 
        rows="6"
        placeholder="粘贴 docker-compose.yml 内容..."
      ></textarea>
      <div class="form-text small">自动提取镜像列表</div>
    </div>

    <button 
      type="button" 
      class="btn btn-info w-100 mb-3" 
      @click="parseCompose"
      :disabled="parsing"
    >
      <i class="fas fa-search"></i> 
      {{ parsing ? '解析中...' : '解析镜像' }}
    </button>

    <!-- 镜像列表 -->
    <div v-if="images.length > 0" class="mt-3">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <small class="text-muted">共 {{ images.length }} 个镜像</small>
        <div class="d-flex gap-2 align-items-center">
          <div class="form-check form-check-inline mb-0">
            <input 
              v-model="selectAll" 
              type="checkbox" 
              class="form-check-input" 
              id="selectAllImages"
              @change="toggleSelectAll"
            />
            <label class="form-check-label small" for="selectAllImages">全选</label>
          </div>
          <select v-model="compress" class="form-select form-select-sm" style="width: auto;">
            <option value="none">tar</option>
            <option value="gzip">tar.gz</option>
          </select>
          <button 
            class="btn btn-sm btn-outline-secondary" 
            @click="downloadSelected"
            :disabled="selectedImages.length === 0"
          >
            <i class="fas fa-download"></i> 下载
          </button>
        </div>
      </div>

      <div style="max-height: 300px; overflow-y: auto;">
        <table class="table table-sm table-striped align-middle mb-0">
          <thead class="table-light" style="position: sticky; top: 0;">
            <tr>
              <th style="width: 30px;"></th>
              <th>服务</th>
              <th>镜像:标签</th>
              <th class="text-end" style="width: 80px;">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(img, index) in images" :key="index">
              <td>
                <input 
                  v-model="img.selected" 
                  type="checkbox" 
                  class="form-check-input"
                />
              </td>
              <td>{{ img.service }}</td>
              <td>{{ img.image }}:{{ img.tag }}</td>
              <td class="text-end">
                <button 
                  class="btn btn-sm btn-outline-primary py-0" 
                  style="font-size: 0.8rem;"
                  @click="downloadImage(img)"
                >
                  <i class="fas fa-download"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import yaml from 'js-yaml'

const inputMode = ref('file')
const composeText = ref('')
const composeFile = ref(null)
const images = ref([])
const compress = ref('none')
const selectAll = ref(false)
const parsing = ref(false)

const selectedImages = computed(() => {
  return images.value.filter(img => img.selected)
})

function handleFileChange(e) {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (ev) => {
      composeText.value = ev.target.result
    }
    reader.readAsText(file)
  }
}

function toggleSelectAll() {
  images.value.forEach(img => {
    img.selected = selectAll.value
  })
}

async function parseCompose() {
  if (!composeText.value.trim()) {
    alert('请上传文件或输入 docker-compose.yml 内容')
    return
  }
  
  parsing.value = true
  try {
    const res = await axios.post('/api/parse-compose', {
      content: composeText.value
    })
    
    images.value = (res.data.images || []).map(img => ({
      ...img,
      selected: false
    }))
    
    alert(`解析成功，共 ${images.value.length} 个镜像`)
  } catch (error) {
    alert(error.response?.data?.error || '解析失败')
  } finally {
    parsing.value = false
  }
}

async function downloadImage(img) {
  try {
    const params = new URLSearchParams({
      image: img.image,
      tag: img.tag || 'latest',
      compress: compress.value
    })
    
    const res = await axios.get(`/api/export-image?${params.toString()}`, {
      responseType: 'blob'
    })
    
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${img.image.replace(/\//g, '_')}-${img.tag || 'latest'}.tar${compress.value === 'gzip' ? '.gz' : ''}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    alert(error.response?.data?.error || '导出失败')
  }
}

async function downloadSelected() {
  for (const img of selectedImages.value) {
    await downloadImage(img)
    await new Promise(resolve => setTimeout(resolve, 300))
  }
}
</script>

<style scoped>
.compose-panel {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.font-monospace {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}
</style>


<template>
  <div class="export-panel">
    <form @submit.prevent="handleExport">
      <div class="row g-3 mb-3">
        <div class="col-md-6">
          <label class="form-label">
            镜像名称 <span class="text-danger">*</span>
          </label>
          <input 
            v-model="form.image" 
            type="text" 
            class="form-control" 
            placeholder="myapp/demo" 
            required
          />
        </div>
        <div class="col-md-3">
          <label class="form-label">标签</label>
          <input v-model="form.tag" type="text" class="form-control" />
        </div>
        <div class="col-md-3">
          <label class="form-label">压缩</label>
          <select v-model="form.compress" class="form-select">
            <option value="none">不压缩</option>
            <option value="gzip">GZIP</option>
          </select>
        </div>
      </div>

      <button type="submit" class="btn btn-warning w-100" :disabled="exporting">
        <i class="fas fa-download"></i> 
        {{ exporting ? '导出中...' : '导出镜像' }}
        <span v-if="exporting" class="spinner-border spinner-border-sm ms-2"></span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const form = ref({
  image: 'myapp/demo',
  tag: 'latest',
  compress: 'none'
})

const exporting = ref(false)

async function handleExport() {
  if (!form.value.image) {
    alert('请输入镜像名称')
    return
  }
  
  exporting.value = true
  try {
    const params = new URLSearchParams({
      image: form.value.image,
      tag: form.value.tag,
      compress: form.value.compress
    })
    
    const res = await axios.get(`/api/export-image?${params.toString()}`, {
      responseType: 'blob'
    })
    
    // 下载文件
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    
    // 从响应头获取文件名
    const disposition = res.headers['content-disposition']
    let filename = `${form.value.image.replace(/\//g, '_')}-${form.value.tag}.tar${form.value.compress === 'gzip' ? '.gz' : ''}`
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/i)
      if (match && match[1]) {
        filename = match[1]
      }
    }
    
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    alert(`镜像 ${form.value.image}:${form.value.tag} 导出成功`)
  } catch (error) {
    alert(error.response?.data?.error || '导出失败')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.export-panel {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>


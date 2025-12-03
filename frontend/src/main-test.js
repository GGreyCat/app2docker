import { createApp } from 'vue'
import App from './App-simple.vue'

console.log('🚀 开始挂载 Vue 应用...')
console.log('App 组件:', App)

try {
  const app = createApp(App)
  app.mount('#app')
  console.log('✅ Vue 应用挂载成功！')
} catch (error) {
  console.error('❌ 挂载失败:', error)
}

// 测试所有导入是否正常
import { createApp } from 'vue'
import App from './App.vue'
import LoginPage from './components/LoginPage.vue'
import BuildPanel from './components/BuildPanel.vue'
import ExportPanel from './components/ExportPanel.vue'
import ComposePanel from './components/ComposePanel.vue'
import TemplatePanel from './components/TemplatePanel.vue'
import BuildLogModal from './components/BuildLogModal.vue'
import ConfigModal from './components/ConfigModal.vue'

console.log('✅ 所有组件导入成功')
console.log('App:', App)
console.log('LoginPage:', LoginPage)
console.log('BuildPanel:', BuildPanel)

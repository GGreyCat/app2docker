import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // 不需要 rewrite，直接转发 /api 路径
      }
    }
  },
  
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    assetsDir: 'assets'
  }
})

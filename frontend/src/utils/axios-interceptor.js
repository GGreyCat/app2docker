/**
 * Axios 拦截器配置
 */
import axios from 'axios'
import { getToken, clearAuth } from './auth'

/**
 * 设置 axios 拦截器
 */
export function setupAxiosInterceptors() {
  // 请求拦截器：自动添加 token
  axios.interceptors.request.use(
    (config) => {
      const token = getToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // 响应拦截器：处理认证失败
  axios.interceptors.response.use(
    (response) => {
      return response
    },
    (error) => {
      if (error.response?.status === 401) {
        // 如果是登录接口或测试仓库接口，不重新加载页面（让页面自己处理错误）
        const url = error.config?.url || ''
        const isLoginRequest = url.includes('/api/login')
        const isTestRegistryRequest = url.includes('/api/registries/test')
        const isSaveRegistryRequest = url.includes('/api/registries') && error.config?.method === 'post' && !url.includes('/test')
        
        // 只有真正的认证错误才清除 token（排除登录、测试仓库等接口）
        // 测试仓库接口即使返回 401（没有 token 的情况），也不应该退出登录
        if (!isLoginRequest && !isTestRegistryRequest) {
          // Token 过期或无效，清除认证信息并重新加载页面
          clearAuth()
          window.location.reload()
        }
      }
      return Promise.reject(error)
    }
  )
}


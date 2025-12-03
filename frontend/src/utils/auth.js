/**
 * 认证工具函数
 */

/**
 * 获取存储的 token
 */
export function getToken() {
  return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
}

/**
 * 获取当前用户名
 */
export function getUsername() {
  return localStorage.getItem('username') || sessionStorage.getItem('username')
}

/**
 * 保存认证信息
 */
export function saveAuth(token, username, remember = true) {
  const storage = remember ? localStorage : sessionStorage
  storage.setItem('auth_token', token)
  storage.setItem('username', username)
}

/**
 * 清除认证信息
 */
export function clearAuth() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('username')
  sessionStorage.removeItem('auth_token')
  sessionStorage.removeItem('username')
}

/**
 * 检查是否已登录
 */
export function isAuthenticated() {
  return !!getToken()
}

/**
 * 登出
 */
export async function logout() {
  try {
    const axios = (await import('axios')).default
    await axios.post('/api/logout')
  } catch (error) {
    console.error('登出请求失败:', error)
  } finally {
    clearAuth()
  }
}


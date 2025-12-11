/**
 * Git 分支和标签缓存工具
 * 缓存有效期：30分钟
 */

const CACHE_PREFIX = 'git_cache_'
const CACHE_EXPIRY = 30 * 60 * 1000 // 30分钟（毫秒）

/**
 * 生成缓存键
 * @param {string} gitUrl Git仓库地址
 * @param {string|null} sourceId 数据源ID（可选）
 * @returns {string} 缓存键
 */
function getCacheKey(gitUrl, sourceId = null) {
  if (sourceId) {
    return `${CACHE_PREFIX}${sourceId}`
  }
  // 使用git_url作为key，但需要规范化（去除尾随斜杠等）
  const normalizedUrl = gitUrl.trim().replace(/\/$/, '').replace(/\.git$/, '')
  return `${CACHE_PREFIX}${normalizedUrl}`
}

/**
 * 获取缓存的Git信息
 * @param {string} gitUrl Git仓库地址
 * @param {string|null} sourceId 数据源ID（可选）
 * @returns {Object|null} 缓存的数据，包含 { branches, tags, default_branch, timestamp }，如果已过期或不存在则返回null
 */
export function getGitCache(gitUrl, sourceId = null) {
  try {
    const key = getCacheKey(gitUrl, sourceId)
    const cached = localStorage.getItem(key)
    
    if (!cached) {
      return null
    }
    
    const data = JSON.parse(cached)
    const now = Date.now()
    
    // 检查是否过期
    if (now - data.timestamp > CACHE_EXPIRY) {
      // 过期了，删除缓存
      localStorage.removeItem(key)
      return null
    }
    
    // 返回缓存数据（不包含timestamp）
    return {
      branches: data.branches || [],
      tags: data.tags || [],
      default_branch: data.default_branch || null
    }
  } catch (error) {
    console.error('读取Git缓存失败:', error)
    return null
  }
}

/**
 * 保存Git信息到缓存
 * @param {string} gitUrl Git仓库地址
 * @param {string|null} sourceId 数据源ID（可选）
 * @param {Object} data 要缓存的数据，包含 { branches, tags, default_branch }
 */
export function setGitCache(gitUrl, sourceId = null, data) {
  try {
    const key = getCacheKey(gitUrl, sourceId)
    const cacheData = {
      ...data,
      timestamp: Date.now()
    }
    localStorage.setItem(key, JSON.stringify(cacheData))
  } catch (error) {
    console.error('保存Git缓存失败:', error)
    // localStorage可能已满，尝试清理旧的缓存
    try {
      clearExpiredGitCache()
      localStorage.setItem(key, JSON.stringify(cacheData))
    } catch (e) {
      console.error('清理过期缓存后仍然保存失败:', e)
    }
  }
}

/**
 * 清除指定Git仓库的缓存
 * @param {string} gitUrl Git仓库地址
 * @param {string|null} sourceId 数据源ID（可选）
 */
export function clearGitCache(gitUrl, sourceId = null) {
  try {
    const key = getCacheKey(gitUrl, sourceId)
    localStorage.removeItem(key)
  } catch (error) {
    console.error('清除Git缓存失败:', error)
  }
}

/**
 * 清除所有过期的Git缓存
 */
function clearExpiredGitCache() {
  try {
    const keys = Object.keys(localStorage)
    const now = Date.now()
    
    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        try {
          const cached = localStorage.getItem(key)
          if (cached) {
            const data = JSON.parse(cached)
            if (now - data.timestamp > CACHE_EXPIRY) {
              localStorage.removeItem(key)
            }
          }
        } catch (e) {
          // 解析失败，删除无效的缓存项
          localStorage.removeItem(key)
        }
      }
    })
  } catch (error) {
    console.error('清理过期缓存失败:', error)
  }
}

/**
 * 获取缓存的Git信息或从API获取（带自动缓存）
 * @param {Function} fetchFn 获取数据的异步函数，应该返回 { branches, tags, default_branch }
 * @param {string} gitUrl Git仓库地址
 * @param {string|null} sourceId 数据源ID（可选）
 * @param {boolean} forceRefresh 是否强制刷新（忽略缓存）
 * @returns {Promise<Object>} Git信息 { branches, tags, default_branch }
 */
export async function getGitInfoWithCache(fetchFn, gitUrl, sourceId = null, forceRefresh = false) {
  // 如果不需要强制刷新，先尝试从缓存获取
  if (!forceRefresh) {
    const cached = getGitCache(gitUrl, sourceId)
    if (cached) {
      console.log('使用缓存的Git信息:', gitUrl)
      return cached
    }
  }
  
  // 从API获取
  console.log('从API获取Git信息:', gitUrl, forceRefresh ? '(强制刷新)' : '')
  const data = await fetchFn()
  
  // 保存到缓存
  if (data && (data.branches || data.tags)) {
    setGitCache(gitUrl, sourceId, {
      branches: data.branches || [],
      tags: data.tags || [],
      default_branch: data.default_branch || null
    })
  }
  
  return data
}

// 在模块加载时清理过期缓存
if (typeof window !== 'undefined') {
  clearExpiredGitCache()
}


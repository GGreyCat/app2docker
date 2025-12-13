// frontend/src/utils/agentWebSocket.js
/**
 * Agent WebSocket连接管理工具
 * 用于管理Agent主机的WebSocket连接和消息
 */

class AgentWebSocketManager {
  constructor() {
    this.connections = new Map() // host_id -> WebSocket
    this.reconnectIntervals = new Map() // host_id -> intervalId
    this.reconnectAttempts = new Map() // host_id -> attempts
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000 // 3秒
    this.heartbeatInterval = 30000 // 30秒
    this.heartbeatTimers = new Map() // host_id -> timerId
  }

  /**
   * 连接WebSocket
   * @param {string} hostId - 主机ID
   * @param {string} token - Token
   * @param {Function} onMessage - 消息回调
   * @param {Function} onError - 错误回调
   */
  connect(hostId, token, onMessage, onError) {
    // 如果已连接，先关闭
    if (this.connections.has(hostId)) {
      this.disconnect(hostId)
    }

    // 构建WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/ws/agent/${token}`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log(`✅ Agent WebSocket连接成功: ${hostId}`)
        this.reconnectAttempts.set(hostId, 0)
        
        // 启动心跳
        this.startHeartbeat(hostId, ws)
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          if (onMessage) {
            onMessage(hostId, message)
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      ws.onerror = (error) => {
        console.error(`⚠️ Agent WebSocket错误 (${hostId}):`, error)
        if (onError) {
          onError(hostId, error)
        }
      }

      ws.onclose = () => {
        console.log(`🔌 Agent WebSocket连接关闭: ${hostId}`)
        this.stopHeartbeat(hostId)
        this.connections.delete(hostId)
        
        // 尝试重连
        this.scheduleReconnect(hostId, token, onMessage, onError)
      }

      this.connections.set(hostId, ws)
    } catch (error) {
      console.error(`❌ 创建WebSocket连接失败 (${hostId}):`, error)
      if (onError) {
        onError(hostId, error)
      }
    }
  }

  /**
   * 断开WebSocket连接
   * @param {string} hostId - 主机ID
   */
  disconnect(hostId) {
    // 清除重连定时器
    if (this.reconnectIntervals.has(hostId)) {
      clearTimeout(this.reconnectIntervals.get(hostId))
      this.reconnectIntervals.delete(hostId)
    }

    // 停止心跳
    this.stopHeartbeat(hostId)

    // 关闭连接
    const ws = this.connections.get(hostId)
    if (ws) {
      ws.close()
      this.connections.delete(hostId)
    }

    this.reconnectAttempts.delete(hostId)
  }

  /**
   * 发送消息
   * @param {string} hostId - 主机ID
   * @param {Object} message - 消息对象
   */
  send(hostId, message) {
    const ws = this.connections.get(hostId)
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
      return true
    } else {
      console.warn(`⚠️ WebSocket未连接，无法发送消息 (${hostId})`)
      return false
    }
  }

  /**
   * 发送心跳
   * @param {string} hostId - 主机ID
   */
  sendHeartbeat(hostId) {
    this.send(hostId, {
      type: 'heartbeat',
      timestamp: Date.now()
    })
  }

  /**
   * 启动心跳
   * @param {string} hostId - 主机ID
   * @param {WebSocket} ws - WebSocket连接
   */
  startHeartbeat(hostId, ws) {
    // 立即发送一次心跳
    this.sendHeartbeat(hostId)

    // 设置定时心跳
    const timerId = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        this.sendHeartbeat(hostId)
      } else {
        this.stopHeartbeat(hostId)
      }
    }, this.heartbeatInterval)

    this.heartbeatTimers.set(hostId, timerId)
  }

  /**
   * 停止心跳
   * @param {string} hostId - 主机ID
   */
  stopHeartbeat(hostId) {
    const timerId = this.heartbeatTimers.get(hostId)
    if (timerId) {
      clearInterval(timerId)
      this.heartbeatTimers.delete(hostId)
    }
  }

  /**
   * 安排重连
   * @param {string} hostId - 主机ID
   * @param {string} token - Token
   * @param {Function} onMessage - 消息回调
   * @param {Function} onError - 错误回调
   */
  scheduleReconnect(hostId, token, onMessage, onError) {
    const attempts = this.reconnectAttempts.get(hostId) || 0
    
    if (attempts >= this.maxReconnectAttempts) {
      console.warn(`⚠️ 达到最大重连次数，停止重连 (${hostId})`)
      return
    }

    this.reconnectAttempts.set(hostId, attempts + 1)
    
    const delay = this.reconnectDelay * (attempts + 1) // 递增延迟
    
    const timeoutId = setTimeout(() => {
      console.log(`🔄 尝试重连 (${hostId}), 第 ${attempts + 1} 次`)
      this.connect(hostId, token, onMessage, onError)
    }, delay)

    this.reconnectIntervals.set(hostId, timeoutId)
  }

  /**
   * 检查连接状态
   * @param {string} hostId - 主机ID
   * @returns {boolean}
   */
  isConnected(hostId) {
    const ws = this.connections.get(hostId)
    return ws && ws.readyState === WebSocket.OPEN
  }

  /**
   * 断开所有连接
   */
  disconnectAll() {
    const hostIds = Array.from(this.connections.keys())
    hostIds.forEach(hostId => {
      this.disconnect(hostId)
    })
  }
}

// 导出单例实例
export default new AgentWebSocketManager()


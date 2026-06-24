class SocketService {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.eventListeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) return

    const serverUrl = '/api/v1/chat/ws/send'

    try {
      this.socket = new WebSocket(serverUrl)

      this.socket.onopen = (event) => {
        console.log('✅ WebSocket 连接已建立')
        this.isConnected = true
        this.reconnectAttempts = 0
        this.emitEvent('connected', event)
      }

      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket 连接已关闭', event.code, event.reason)
        this.isConnected = false
        this.emitEvent('disconnected', event)

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++
            console.log(`🔄 尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
            this.connect()
          }, 3000)
        }
      }

      this.socket.onerror = (error) => {
        console.error('❌ WebSocket 错误:', error)
        this.emitEvent('error', error)
      }

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📨 收到服务器消息:', data)

          if (data.event) {
            this.emitEvent(data.event, data.data || data)
          } else if (data.status) {
            this.emitEvent('server_response', data)
          }
        } catch (error) {
          console.error('❌ 消息解析错误:', error, event.data)
        }
      }
    } catch (error) {
      console.error('❌ WebSocket 创建失败:', error)
    }
  }

  sendMessage(messageData) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket 未连接，无法发送消息')
      this.emitEvent('error', { message: 'WebSocket 未连接' })
      return false
    }

    try {
      const dataToSend = {
        user_input: messageData.user_input || messageData.message || '',
        user_id: messageData.user_id || 'anonymous',
        user_info: messageData.user_info || {},
        context: messageData.context || {},
        timestamp: new Date().toISOString(),
      }

      this.socket.send(JSON.stringify(dataToSend))
      console.log('📤 发送消息:', dataToSend)
      return true
    } catch (error) {
      console.error('❌ 发送消息失败:', error)
      this.emitEvent('error', error)
      return false
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close(1000, '用户主动断开')
      this.socket = null
      this.isConnected = false
    }
  }

  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event).push(callback)
  }

  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event)
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  emitEvent(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach((callback) => {
        try {
          callback(data)
        } catch (error) {
          console.error(`事件处理错误 (${event}):`, error)
        }
      })
    }
  }
}

// 创建单例
export const socketService = new SocketService()

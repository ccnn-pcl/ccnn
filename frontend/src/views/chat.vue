<template>
  <div class="dashboard-container">
    <!-- 侧边栏 -->
    <Sidebar
      :visible="sidebarVisible"
      :user="user"
      :score="score"
      @logout="handleLogout"
    />
    <!-- 切换按钮（侧边栏显示时） -->
    <button class="toggle-btn toggle-btn-sidebar" @click="toggleSidebar">◀</button>

    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'main-content-full': !sidebarVisible }">
      <!-- 切换按钮（侧边栏隐藏时） -->
      <button class="toggle-btn toggle-btn-chat" @click="toggleSidebar">▶</button>

      <!-- 聊天区域 -->
      <div class="chat-container">
        <div class="messages-container" ref="messagesContainer">
          <ChatMessage v-for="(msg, index) in chatHistory" :key="index" :message="msg" />
        </div>

        <ChatInput
          ref="chatInputRef"
          v-model="userInput"
          :disabled="waiting"
          :attachments="chatAttachments"
          @send="sendMessage_by_erbsocket"
          @remove-attachment="removeAttachment"
          @file-upload="handleChatFileUpload"
        />
      </div>

      <!-- 历史记录 -->
      <HistoryPanel v-if="showHistory" :messages="chatHistory" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUpdated, onUnmounted, nextTick } from 'vue'
import { socketService } from '@/services/socketService'
import useDeviceDetect from '@/plugins/deviceDetect'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import Sidebar from '@/components/chat/Sidebar.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import HistoryPanel from '@/components/chat/HistoryPanel.vue'
import { chatApi } from '@/api/chat'

// 用户状态
const user = ref({})
const score = ref(0)

// 聊天状态
const userInput = ref('')
const userInputCopy = ref('')
const chatHistory = ref([])
const showHistory = ref(false)
const messagesContainer = ref(null)
const chatAttachments = ref([])
const waiting = ref(false)
const sidebarVisible = ref(true)
const chatInputRef = ref(null)

// 设备检测
const { deviceInfo } = useDeviceDetect()

// 侧边栏
const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value
}

// 登出
const handleLogout = () => {
  localStorage.removeItem('authState')
  window.location.href = '/logout'
}

// 文件上传
const handleChatFileUpload = (event) => {
  const files = event.target.files
  if (!files || files.length === 0) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const maxSize = 20 * 1024 * 1024
    if (file.size > maxSize) {
      alert(`文件 ${file.name} 大小超过限制（最大20MB）`)
      continue
    }
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf']
    if (!allowedTypes.includes(file.type)) {
      alert(`不支持的文件类型 ${file.type}。请选择 JPG、JPEG、PNG 或 PDF 文件`)
      continue
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      chatAttachments.value.push({
        file: file,
        preview: e.target.result,
        type: file.type,
      })
    }
    reader.readAsDataURL(file)
  }
}

const removeAttachment = (index) => {
  chatAttachments.value.splice(index, 1)
}

// 发送消息（WebSocket）
const sendMessage_by_erbsocket = () => {
  if (!userInput.value.trim() || !user.value?.username) return

  const timestamp = new Date().toLocaleString('zh-CN')
  const imageUrls = chatAttachments.value
    .filter((a) => a.type.startsWith('image/'))
    .map((a) => a.preview)

  const userMessage = {
    role: 'user',
    content: userInput.value,
    timestamp,
    images: imageUrls,
  }
  userInputCopy.value = userInput.value
  chatHistory.value.push(userMessage)

  const messageData = {
    user_id: user.value.userid,
    username: user.value.username,
    user_input: userInput.value.trim(),
    timestamp,
    imageUrls,
  }

  userInput.value = ''
  chatAttachments.value = []
  scrollToBottom()

  // 同时发 HTTP（保持兼容）
  chatApi.sendMessage(messageData).catch(() => {})

  // 通过 WebSocket 发送
  const success = socketService.sendMessage(messageData)
  if (!success) {
    chatHistory.value.push({
      role: 'system',
      content: '发送失败：WebSocket未连接',
      timestamp: new Date().toLocaleString('zh-CN'),
      isError: true,
    })
    scrollToBottom()
  }
}

// Socket 初始化
const initSocket = () => {
  socketService.connect()

  socketService.on('connected', () => {
    console.log('Connected to server')
  })

  socketService.on('disconnected', () => {
    console.log('Disconnected from server')
  })

  socketService.on('server_response', (data) => {
    console.log('📨 收到服务器响应:', data)

    if (data.status === 'ok' || data.event === 'acknowledge') {
      const responseData = data.data || data
      const aiResponse = {
        role: 'assistant',
        content: responseData.response,
        agent_name: responseData.agent_name || 'AI助手',
        timestamp: new Date().toLocaleString('zh-CN'),
        metadata: responseData.metadata || {},
      }
      chatHistory.value.push(aiResponse)
      saveMessages()

      if (data.metadata?.redirect == 1) {
        const params = new URLSearchParams({
          user_input: userInputCopy.value.trim(),
        })
        setTimeout(() => {
          window.open(`${process.env.MEDICAL_FRONTEND}/?${params.toString()}`, '_blank')
        }, 1500)
      }
      scrollToBottom()
    }
  })

  socketService.on('error', (data) => {
    console.error('服务器错误:', data)
    chatHistory.value.push({
      role: 'system',
      content: `错误: ${data.message || '请求失败'}`,
      timestamp: new Date().toLocaleString('zh-CN'),
      isError: true,
    })
    scrollToBottom()
  })
}

// 保存聊天记录
const saveMessages = () => {
  if (user.value.username) {
    localStorage.setItem(`chat_history_${user.value.username}`, JSON.stringify(chatHistory.value))
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 历史记录
const toggleHistory = () => {
  showHistory.value = !showHistory.value
}

const clearChat = () => {
  if (confirm('确定要清空所有聊天记录吗？')) {
    localStorage.removeItem(`chat_history_${user.value.username}`)
    chatHistory.value = []
  }
}

// 心跳轮询
let pollTimer = null
const POLL_INTERVAL = 10 * 60 * 100

const keepAuth = async () => {
  try {
    const data = await chatApi.keepAuth(deviceInfo.value)
    score.value = data?.trustscore ?? score.value
    if (score.value < 0.4) {
      handleLogout()
    }
  } catch (error) {
    console.error('请求失败:', error)
  }
}

const startPolling = () => {
  stopPolling()
  keepAuth()
  pollTimer = setInterval(keepAuth, POLL_INTERVAL)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 生命周期
onMounted(() => {
  // 获取用户信息
  fetch('/api/me', { method: 'GET', credentials: 'include' })
    .then((r) => r.json())
    .then((data) => {
      if (data?.username) {
        user.value = { username: data.username, userid: data.userid || '' }
      }
      score.value = data?.trustscore ?? 0
    })

  // 加载聊天历史
  if (user.value.username) {
    const savedHistory = localStorage.getItem(`chat_history_${user.value.username}`)
    if (savedHistory) {
      chatHistory.value = JSON.parse(savedHistory)
    }
  }

  scrollToBottom()
  initSocket()
  startPolling()
})

onUpdated(() => {
  scrollToBottom()
})

onUnmounted(() => {
  socketService.disconnect()
  stopPolling()
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  height: 100%;
  position: relative;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.main-content-full {
  margin-left: 0;
  width: 100%;
}
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 切换按钮 */
.toggle-btn {
  transition: all 0.3s ease;
  position: absolute;
  top: 110px;
  width: 24px;
  height: 48px;
  background-color: #2196f3;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 200;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}
.toggle-btn:hover {
  background-color: #1976d2;
  transform: scale(1.05);
}
.toggle-btn-sidebar {
  left: 340px;
  top: 45%;
  border-radius: 0 4px 4px 0;
}
.toggle-btn-chat {
  left: 0;
  top: 45%;
  border-radius: 0 4px 4px 0;
  display: none;
  transform: translateX(-10px);
  opacity: 0;
}
.sidebar-hidden + .toggle-btn-sidebar {
  opacity: 0;
  visibility: hidden;
  transform: translateX(-10px);
}
.sidebar-hidden ~ .main-content .toggle-btn-chat {
  display: flex;
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}
</style>

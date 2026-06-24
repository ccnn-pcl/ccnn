import request from './request'

export const chatApi = {
  sendMessage(data) {
    return request.post('/api/v1/chat/send', data)
  },

  getMe() {
    return request.get('/api/me')
  },

  keepAuth(deviceInfo) {
    return request.post('/api/keep-auth', { deviceInfo })
  },
}

import request from './request'

export const chatApi = {
  sendMessage(data) {
    return request.post('/api/v1/chat/send', data)
  },

  getMe() {
    return request.get('/api/me')
  },

  keepAuth({ deviceInfo, location }) {
    const data = { deviceInfo }
    if (location) data.location = location
    return request.post('/api/keep-auth', data)
  },
}

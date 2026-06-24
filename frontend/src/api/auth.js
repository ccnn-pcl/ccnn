import request from './request'

export default {
  register(userData) {
    return request.post('/api/register', userData)
  },
  login(userData) {
    return request.post('/api/login', userData)
  },
}

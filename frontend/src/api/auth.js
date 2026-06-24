import request from './request'

export default {
  register(userData) {
    return request.post('/api/register', filterNull(userData))
  },
  login(userData) {
    return request.post('/api/login', filterNull(userData))
  },
}

// 过滤掉 null/undefined 字段，避免后端 .get() 报错
function filterNull(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([_, v]) => v != null)
  )
}

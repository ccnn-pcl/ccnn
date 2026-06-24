import axios from 'axios'

const request = axios.create({
  timeout: 120000,
})

// 请求拦截器 - 自动携带 session
request.interceptors.request.use((config) => {
  config.withCredentials = true
  return config
})

// 响应拦截器 - 直接返回 data
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      // 登录/注册接口的 401 是正常业务失败，不跳转
      const isAuthApi = error.config.url?.includes('/login') || error.config.url?.includes('/register')
      switch (error.response.status) {
        case 401:
          if (!isAuthApi) window.location.href = '/logout'
          break
        case 500:
          console.error('服务器内部错误')
          break
      }
    } else if (error.request) {
      console.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request

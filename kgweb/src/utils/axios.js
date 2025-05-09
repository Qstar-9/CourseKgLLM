import axios from 'axios'

// 创建 axios 实例
const instance = axios.create({
  baseURL: 'http://localhost:5180',  // 修改为正确的后端服务器地址和端口
  timeout: 5000,  // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  config => {
    console.log('发送请求:', config.method.toUpperCase(), config.url, config.data)
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  response => {
    console.log('收到响应:', response.status, response.data)
    return response
  },
  error => {
    if (error.response) {
      console.error('响应错误:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config.url
      })
      switch (error.response.status) {
        case 401:
          console.error('未授权')
          break
        case 404:
          console.error('API不存在:', error.config.url)
          break
        default:
          console.error('服务器错误:', error.response.status)
      }
    } else if (error.request) {
      console.error('未收到响应:', error.request)
    } else {
      console.error('请求配置错误:', error.message)
    }
    return Promise.reject(error)
  }
)

export default instance 
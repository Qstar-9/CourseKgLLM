<template>
  <div class="login-container">
    <div class="login-box">
      <h2>登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <input type="text" v-model="username" placeholder="用户名" required>
        </div>
        <div class="form-group">
          <input type="password" v-model="password" placeholder="密码" required>
        </div>
        <button type="submit" class="login-btn">登录</button>
        <div class="links">
          <RouterLink to="/register">还没有账号？立即注册</RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from '@/utils/axios'

const router = useRouter()
const username = ref('')
const password = ref('')

const handleLogin = async () => {
  try {
    const response = await axios.post('/api/login', {
      username: username.value,
      password: password.value
    })

    if (response.data.success) {
      // 保存token和用户信息
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('username', response.data.username)
      alert('登录成功！')
      router.push('/')
    } else {
      alert(response.data.message || '登录失败')
    }
  } catch (error) {
    console.error('登录失败:', error)
    alert(error.response?.data?.message || '登录失败，请稍后重试')
  }
}
</script>

<style lang="less" scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.login-box {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);

  h2 {
    text-align: center;
    margin-bottom: 2rem;
    color: #005f77;
  }
}

.form-group {
  margin-bottom: 1rem;

  input {
    width: 100%;
    padding: 0.8rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;

    &:focus {
      outline: none;
      border-color: #005f77;
    }
  }
}

.login-btn {
  width: 100%;
  padding: 0.8rem;
  background: #005f77;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background: #004c5f;
  }
}

.links {
  margin-top: 1rem;
  text-align: center;

  a {
    color: #005f77;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style> 
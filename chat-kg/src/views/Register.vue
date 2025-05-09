<template>
  <div class="register-container">
    <div class="register-box">
      <h2>注册</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <input type="text" v-model="username" placeholder="用户名" required>
        </div>
        <div class="form-group">
          <input type="password" v-model="password" placeholder="密码" required>
        </div>
        <div class="form-group">
          <input type="password" v-model="confirmPassword" placeholder="确认密码" required>
        </div>
        <button type="submit" class="register-btn">注册</button>
        <div class="links">
          <RouterLink to="/login">已有账号？立即登录</RouterLink>
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
const confirmPassword = ref('')

const handleRegister = async () => {
  try {
    if (password.value !== confirmPassword.value) {
      alert('两次输入的密码不一致')
      return
    }
    
    const response = await axios.post('/api/register', {
      username: username.value,
      password: password.value
    })

    if (response.data.success) {
      alert('注册成功！')
      router.push('/login')
    } else {
      alert(response.data.message || '注册失败')
    }
  } catch (error) {
    console.error('注册失败:', error)
    alert(error.response?.data?.message || '注册失败，请稍后重试')
  }
}
</script>

<style lang="less" scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.register-box {
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

.register-btn {
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
<script setup>
import { ref, onMounted, computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

// 打印当前页面的路由信息，使用 vue3 的 setup composition API
const route = useRoute()
const router = useRouter()
const isLoggedIn = ref(false)
const username = ref('')

// 计算属性：判断是否显示导航栏
const showNavbar = computed(() => {
  return !['login', 'register'].includes(route.name)
})

onMounted(() => {
  checkLoginStatus()
})

const checkLoginStatus = () => {
  const token = localStorage.getItem('token')
  const storedUsername = localStorage.getItem('username')
  isLoggedIn.value = !!token
  username.value = storedUsername || ''
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  isLoggedIn.value = false
  username.value = ''
  router.push('/login')
}
</script>

<template>
  <header class="header" v-if="showNavbar">
    <nav class="nav">
      <div class="nav-links">
        <RouterLink to="/" class="nav-item" active-class="active">主页</RouterLink>
        <RouterLink to="/chat" class="nav-item" active-class="active">问答</RouterLink>
        <RouterLink to="/kg" class="nav-item" active-class="active">图谱</RouterLink>
        <RouterLink to="/history" class="nav-item" active-class="active">历史</RouterLink>
        <RouterLink to="/about" class="nav-item" active-class="active">关于</RouterLink>
      </div>
      <div class="user-section" v-if="isLoggedIn">
        <span class="username">{{ username }}</span>
        <button class="logout-btn" @click="handleLogout">退出</button>
      </div>
      <div class="auth-buttons" v-else>
        <RouterLink to="/login" class="nav-item" active-class="active">登录</RouterLink>
        <RouterLink to="/register" class="nav-item" active-class="active">注册</RouterLink>
      </div>
    </nav>
  </header>

    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
</template>

<style lang="less" scoped>
.header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 40px 0;
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  height: 45px;
  width: 100%;
  max-width: 800px;
  padding: 0 20px;
}

.nav-links {
  display: flex;
  align-items: center;
}

.nav-item {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: transparent;
  color: #333;
  font-size: 16px;
  transition: background-color 0.2s ease-in-out;
  margin: 0 10px;
  text-decoration: none;
}

.nav-item:hover {
  background-color: #e2eef3;
  cursor: pointer;
}

.nav-item.active {
  font-weight: bold;
  color: #005f77;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  display: block;
  width: 2rem;
  height: 2px;
  background-color: #005f77;
  margin-top: 4px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 1rem;

  .username {
    color: #005f77;
    font-weight: 500;
  }

  .logout-btn {
    padding: 6px 12px;
    border: 1px solid #005f77;
    border-radius: 4px;
    background-color: transparent;
    color: #005f77;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background-color: #005f77;
      color: white;
    }
  }
}

.auth-buttons {
  display: flex;
  align-items: center;
}
</style>

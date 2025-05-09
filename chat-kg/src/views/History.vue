<template>
  <div class="history-container">
    <h2>对话历史记录</h2>
    
    <!-- 会话列表 -->
    <div class="sessions-list" v-if="sessions.length > 0">
      <div v-for="session in sessions" :key="session.id" class="session-item">
        <div class="session-header">
          <h3 class="title">{{ session.title }}</h3>
          <div class="session-info">
            <span class="time">{{ formatTime(session.updated_at) }}</span>
            <span class="count">{{ session.message_count }}条对话</span>
          </div>
          <div class="actions">
            <button class="view-btn" @click="viewSession(session.id)">查看</button>
            <button class="continue-btn" @click="continueChat(session.id)">继续对话</button>
            <button class="delete-btn" @click="handleDelete(session.id)">删除</button>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="pagination" v-if="total > pageSize">
        <button 
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button 
          :disabled="currentPage === totalPages"
          @click="handlePageChange(currentPage + 1)"
        >下一页</button>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      暂无对话记录
    </div>

    <!-- 会话详情弹窗 -->
    <a-modal
      v-model:visible="dialogVisible"
      :title="currentSession?.title"
      width="800px"
      @cancel="closeDialog"
    >
      <div class="session-messages" v-if="currentSession">
        <div v-for="message in sessionMessages" :key="message.created_at" class="message-item">
          <div class="message-time">{{ formatTime(message.created_at) }}</div>
          <div class="question">
            <strong>问：</strong>{{ message.question }}
          </div>
          <div class="answer">
            <strong>答：</strong>{{ message.answer }}
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from '@/utils/axios'

const router = useRouter()
const sessions = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const currentSession = ref(null)
const sessionMessages = ref([])

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载会话列表
const loadSessions = async (page = 1) => {
  try {
    console.log('开始加载会话列表，页码：', page)
    const response = await axios.get('/api/chat-sessions', {
      params: {
        page,
        page_size: pageSize.value
      }
    })
    console.log('会话列表API响应：', response.data)
    
    if (response.data.success) {
      sessions.value = response.data.data.records
      total.value = response.data.data.total
      currentPage.value = page
      console.log('加载到的会话数：', sessions.value.length)
      console.log('总会话数：', total.value)
    } else {
      console.error('获取会话列表失败：', response.data.message)
      alert(response.data.message || '获取会话列表失败')
    }
  } catch (error) {
    console.error('获取会话列表出错：', error)
    console.error('错误详情：', error.response?.data)
    alert(error.response?.data?.message || '获取会话列表失败，请稍后重试')
  }
}

// 查看会话详情
const viewSession = async (sessionId) => {
  try {
    console.log('查看会话详情，ID：', sessionId)
    const response = await axios.get(`/api/chat-sessions/${sessionId}`)
    
    if (response.data.success) {
      currentSession.value = response.data.data.session
      sessionMessages.value = response.data.data.messages
      dialogVisible.value = true
    } else {
      console.error('获取会话详情失败：', response.data.message)
      alert(response.data.message || '获取会话详情失败')
    }
  } catch (error) {
    console.error('获取会话详情出错：', error)
    alert(error.response?.data?.message || '获取会话详情失败，请稍后重试')
  }
}

// 继续对话
const continueChat = (sessionId) => {
  router.push({
    path: '/chat',
    query: { session: sessionId }
  })
}

// 删除会话
const handleDelete = async (sessionId) => {
  if (!confirm('确定要删除这个会话吗？所有相关的对话记录都会被删除。')) {
    return
  }
  
  try {
    console.log('删除会话，ID：', sessionId)
    const response = await axios.delete(`/api/chat-sessions/${sessionId}`)
    if (response.data.success) {
      console.log('会话删除成功')
      alert('删除成功')
      // 重新加载当前页
      await loadSessions(currentPage.value)
    } else {
      console.error('删除会话失败：', response.data.message)
      alert(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除会话出错：', error)
    console.error('错误详情：', error.response?.data)
    alert(error.response?.data?.message || '删除失败，请稍后重试')
  }
}

// 切换页面
const handlePageChange = (page) => {
  if (page < 1 || page > totalPages.value) {
    return
  }
  loadSessions(page)
}

// 关闭对话详情
const closeDialog = () => {
  dialogVisible.value = false
  currentSession.value = null
  sessionMessages.value = []
}

// 组件挂载时加载数据
onMounted(async () => {
  console.log('History组件已挂载，开始加载数据')
  await loadSessions()
})
</script>

<style lang="less" scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  h2 {
    color: #005f77;
    margin-bottom: 2rem;
    text-align: center;
  }
}

.sessions-list {
  .session-item {
    background: #fff;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    .session-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;

      .title {
        font-size: 1.1rem;
        color: #005f77;
        margin: 0;
        flex: 1;
      }

      .session-info {
        display: flex;
        align-items: center;
        gap: 1rem;
        color: #666;
        font-size: 0.9rem;
      }

      .actions {
        display: flex;
        gap: 0.5rem;

        button {
          padding: 0.3rem 0.8rem;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.9rem;
          transition: all 0.2s;

          &.view-btn {
            background: #e8f0fe;
            color: #005f77;

            &:hover {
              background: #d0e3fc;
            }
          }

          &.continue-btn {
            background: #005f77;
            color: white;

            &:hover {
              background: #004c5f;
            }
          }

          &.delete-btn {
            background: #ff4d4f;
            color: white;

            &:hover {
              background: #ff7875;
            }
          }
        }
      }
    }
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 2rem;
  gap: 1rem;

  button {
    padding: 0.5rem 1rem;
    background: #005f77;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;

    &:disabled {
      background: #ccc;
      cursor: not-allowed;
    }

    &:not(:disabled):hover {
      background: #004c5f;
    }
  }
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-size: 1.1rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.session-messages {
  max-height: 60vh;
  overflow-y: auto;
  padding: 1rem;

  .message-item {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;

    &:last-child {
      border-bottom: none;
    }

    .message-time {
      font-size: 0.9rem;
      color: #666;
      margin-bottom: 0.5rem;
    }

    .question, .answer {
      margin: 0.5rem 0;
      line-height: 1.6;

      strong {
        color: #005f77;
        margin-right: 0.5rem;
      }
    }
  }
}
</style> 
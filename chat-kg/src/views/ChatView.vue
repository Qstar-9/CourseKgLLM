<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>{{ info.title }}</h1>
    </div>
    <div class="chat-content">
      <div class="chat">
        <div ref="chatBox" class="chat-box">
          <div
            v-for="message in state.messages"
            :key="message.id"
            class="message-box"
            :class="message.type"
          >
            <img v-if="message.filetype === 'image'" :src="message.url" class="message-image" alt="">
            <p v-else style="white-space: pre-line" class="message-text">{{ message.text }}</p>
          </div>
        </div>
        <div class="input-box">
          <a-button size="large" @click="clearChat">
            <template #icon> <ClearOutlined /> </template>
          </a-button>
          <a-input
            type="text"
            class="user-input"
            v-model:value="state.inputText"
            @keydown.enter="sendMessage"
            placeholder="输入问题……"
          />
          <a-button size="large" @click="sendMessage" :disabled="!state.inputText">
            <template #icon> <SendOutlined /> </template>
          </a-button>
        </div>
      </div>
      <div class="info">
        <div class="process-result" v-if="info.wiki?.process_result">
          <h3>处理结果</h3>
          
          <!-- 实体识别结果 -->
          <div class="result-section">
            <h4>实体识别</h4>
            
            <div class="entities" v-if="info.wiki.process_result.entity_recognition.entities.length">
              <div v-for="(entity, index) in info.wiki.process_result.entity_recognition.entities" 
                   :key="index" class="entity-tag">
                {{ entity }}
              </div>
            </div>
          </div>

          <!-- 意图识别结果 -->
          <div class="result-section">
            <h4>意图识别</h4>
           
            <div class="intents" v-if="info.wiki.process_result.intent_recognition.intents.length">
              <div v-for="(intent, index) in info.wiki.process_result.intent_recognition.intents" 
                   :key="index" class="intent-tag">
                {{ intent }}
              </div>
            </div>
          </div>

          <!-- 知识图谱查询结果 -->
          <div class="result-section">
            <h4>知识图谱查询</h4>
           
            <div class="kg-answers" v-if="info.wiki.process_result.kg_query.answers.length">
              <div v-for="(answer, index) in info.wiki.process_result.kg_query.answers" 
                   :key="index" class="answer-item">
                <div class="answer-header">
                  <span class="course">{{ answer[0] }}</span>
                  <span class="intent">{{ answer[1] }}</span>
                </div>
                <div class="answer-content">{{ answer[2] }}</div>
              </div>
            </div>
          </div>
        </div>

        <p class="description" v-if="info.description && typeof info.description === 'string'">{{ info.description }}</p>
        <div v-else-if="info.description && Array.isArray(info.description)">
          <p class="description" v-for="(desc, index) in info.description" :key="index">{{ desc }}</p>
        </div>

        <img v-if="info.image && typeof info.image === 'string'" :src="info.image" class="info-image" alt="">
        <div v-else-if="info.image && Array.isArray(info.image)">
          <img v-for="(img, index) in info.image" :key="index" :src="img" class="info-image" alt="">
        </div>

        <p v-show="info.graph?.nodes?.length > 0"><b>关联图谱</b></p>
        <div id="lite_graph" v-show="info.graph?.nodes?.length > 0"></div>
        <a-collapse v-model:activeKey="state.activeKey" v-if="info.graph?.sents?.length > 0" accordion>
          <a-collapse-panel
            v-for="(sent, index) in info.graph.sents"
            :key="index"
            :header="'相关描述 ' + (index + 1)"
            :show-arrow="false"
            ghost
          >
            <p>{{ sent }}</p>
          </a-collapse-panel>
        </a-collapse>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as echarts from 'echarts';
import { reactive, ref, onMounted, inject, watch } from 'vue'
import { SendOutlined, ClearOutlined } from '@ant-design/icons-vue'
import axios from '@/utils/axios'
import { useRoute } from 'vue-router'

let myChart = null;
const chatBox = ref(null)
const route = useRoute()
const state = reactive({
  sessionId: null,
  history: [],
  messages: [],
  activeKey: [],
  inputText: '',
  sessionTitle: ''
})

const default_info = {
  title: '基于知识图谱与大模型联合推理的智能问答系统',
  description: '',
  image: [],
  graph: null,
}

const info = reactive({
  ...default_info
})

const scrollToBottom = () => {
  setTimeout(() => {
    chatBox.value.scrollTop = chatBox.value.scrollHeight - chatBox.value.clientHeight
  }, 10) // 10ms 后滚动到底部
}

const appendMessage = (message, type) => {
  state.messages.push({
    id: state.messages.length + 1,
    type,
    text: message
  })
  scrollToBottom()
}


// const appendPicMessage = (pic, type) => {
//   state.messages.push({
//     id: state.messages.length + 1,
//     type,
//     filetype: "image",
//     url: pic
//   })
//   scrollToBottom()
// }

const updateLastReceivedMessage = (message, id) => {
  const lastReceivedMessage = state.messages.find((message) => message.id === id)
  if (lastReceivedMessage) {
    lastReceivedMessage.text = message
  } else {
    state.messages.push({
      id,
      type: 'received',
      text: message
    })
  }
  scrollToBottom()
}

const saveToHistory = async (question, answer) => {
  try {
    console.log('保存对话到历史记录：', { question, answer })
    const response = await axios.post('/api/chat-history', {
      question,
      answer,
      category: '问答对话'
    })
    
    if (response.data.success) {
      console.log('对话历史记录保存成功')
    } else {
      console.error('保存对话历史记录失败：', response.data.message)
    }
  } catch (error) {
    console.error('保存对话历史记录出错：', error)
  }
}

// 创建新会话
const createSession = async (title) => {
  try {
    console.log('创建新会话：', title)
    const response = await axios.post('/api/chat-sessions', {
      title: title || '新对话'
    })
    
    if (response.data.success) {
      state.sessionId = response.data.data.id
      state.sessionTitle = response.data.data.title
      console.log('会话创建成功，ID：', state.sessionId)
      return true
    } else {
      console.error('创建会话失败：', response.data.message)
      return false
    }
  } catch (error) {
    console.error('创建会话出错：', error)
    return false
  }
}

// 加载会话历史
const loadSessionHistory = async (sessionId) => {
  try {
    console.log('加载会话历史，ID：', sessionId)
    const response = await axios.get(`/api/chat-sessions/${sessionId}`)
    
    if (response.data.success) {
      const { session, messages } = response.data.data
      state.sessionId = session.id
      state.sessionTitle = session.title
      state.history = messages.map(msg => ({
        role: 'user',
        content: msg.question,
        response: msg.answer
      }))
      
      // 重建消息列表
      state.messages = []
      messages.forEach(msg => {
        appendMessage(msg.question, 'sent')
        appendMessage(msg.answer, 'received')
      })
      
      console.log('会话历史加载成功')
      return true
    } else {
      console.error('加载会话历史失败：', response.data.message)
      return false
    }
  } catch (error) {
    console.error('加载会话历史出错：', error)
    return false
  }
}

// 保存消息到会话
const saveToSession = async (question, answer) => {
  try {
    if (!state.sessionId) {
      console.log('没有活动会话，创建新会话')
      const success = await createSession(`对话 ${new Date().toLocaleString('zh-CN')}`)
      if (!success) {
        console.error('创建会话失败，无法保存消息')
        return false
      }
    }
    
    console.log('保存消息到会话，ID：', state.sessionId)
    console.log('问题：', question)
    console.log('回答：', answer)
    
    const response = await axios.post(`/api/chat-sessions/${state.sessionId}/messages`, {
      question,
      answer
    })
    
    if (response.data.success) {
      console.log('消息保存成功')
      return true
    } else {
      console.error('保存消息失败：', response.data.message)
      return false
    }
  } catch (error) {
    console.error('保存消息出错：', error)
    return false
  }
}

// 监听路由参数变化
watch(
  () => route.query.session,
  async (newSessionId) => {
    if (newSessionId) {
      console.log('检测到会话ID变化：', newSessionId)
      await loadSessionHistory(newSessionId)
    }
  },
  { immediate: true }
)

const sendMessage = () => {
  if (state.inputText.trim()) {
    const userQuestion = state.inputText.trim()
    appendMessage(userQuestion, 'sent')
    appendMessage('检索中……', 'received')
    const user_input = userQuestion
    const cur_res_id = state.messages[state.messages.length - 1].id
    state.inputText = ''
    
    fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        prompt: user_input,
        history: state.history,
        session_id: state.sessionId
      }),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    }).then(response => {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let pic
      let wiki
      let graph
      let finalAnswer = ''
      let isComplete = false
      
      // 逐步读取响应文本
      const readChunk = () => {
        return reader.read().then(({ done, value }) => {
          if (done) {
            if (finalAnswer && !isComplete) {
              isComplete = true
              console.log('对话完成，准备保存到会话')
              console.log('问题：', userQuestion)
              console.log('回答：', finalAnswer)
              // 保存到会话
              saveToSession(userQuestion, finalAnswer)
            }
            return
          }

          info.image = pic
          info.graph = graph
          // 处理维基百科的内容
          info.title = wiki?.title
          info.description = wiki?.summary
          if (info.graph && info.graph.nodes) {
            myChart.setOption(graphOption(info.graph))
          }

          buffer += decoder.decode(value, { stream: true })
          const messages = buffer.split('\n')
          
          // 处理每一条消息
          for (const message of messages) {
            if (!message.trim()) continue
            
            try {
              const data = JSON.parse(message.replace('data: ', ''))
              finalAnswer = data.updates.response
              updateLastReceivedMessage(finalAnswer, cur_res_id)
              state.history = data.history
              pic = data.image
              wiki = data.wiki
              graph = data.graph
              
              // 添加调试日志
              console.log('处理结果数据:', {
                entity_recognition: data.wiki?.process_result?.entity_recognition,
                intent_recognition: data.wiki?.process_result?.intent_recognition,
                kg_query: data.wiki?.process_result?.kg_query
              })
              
              // 更新 info 对象
              info.title = wiki?.title
              info.description = wiki?.summary
              info.wiki = wiki
              info.graph = graph
              
              if (info.graph && info.graph.nodes) {
                myChart.setOption(graphOption(info.graph))
              }
            } catch (e) {
              console.log('解析响应出错：', e)
            }
          }
          buffer = ''

          return readChunk()
        })
      }
      return readChunk()
    }).catch(error => {
      console.error('发送消息出错：', error)
      updateLastReceivedMessage('抱歉，发生错误，请稍后重试', cur_res_id)
    })
  } else {
    console.log('Please enter a message')
  }
}

const graphOption = (graph) => {
  console.log(graph)
  graph.nodes.forEach(node => {
    node.symbolSize = 5;
    node.label = {
      show: true
    }
  });
  let option = {
    tooltip: {
      show: true, //默认值为true
      showContent: true, //是否显示提示框浮层
      trigger: 'item', //触发类型，默认数据项触发
      triggerOn: 'mousemove', //提示触发条件，mousemove鼠标移至触发，还有click点击触发
      alwaysShowContent: false, //默认离开提示框区域隐藏，true为一直显示
      showDelay: 0, //浮层显示的延迟，单位为 ms，默认没有延迟，也不建议设置。在 triggerOn 为 'mousemove' 时有效。
      hideDelay: 200, //浮层隐藏的延迟，单位为 ms，在 alwaysShowContent 为 true 的时候无效。
      enterable: false, //鼠标是否可进入提示框浮层中，默认为false，如需详情内交互，如添加链接，按钮，可设置为 true。
      position: 'right', //提示框浮层的位置，默认不设置时位置会跟随鼠标的位置。只在 trigger 为'item'的时候有效。
      confine: false, //是否将 tooltip 框限制在图表的区域内。外层的 dom 被设置为 'overflow: hidden'，或者移动端窄屏，导致 tooltip 超出外界被截断时，此配置比较有用。
      // transitionDuration: 0.1, //提示框浮层的移动动画过渡时间，单位是 s，设置为 0 的时候会紧跟着鼠标移动。
      formatter: (x) => x.data.name
    },
    series: [
      {
        type: 'graph',
        draggable: true,
        layout: 'force',
        data: graph.nodes.map(function (node, idx) {
          node.id = idx;
          return node;
        }),
        links: graph.links,
        categories: graph.categories,
        roam: true,
        label: {
          position: 'right'
        },
        force: {
          repulsion: 100
        },
        lineStyle: {
          color: 'source',
          curveness: 0.1
        },
      }
    ]
  };

  return option
}


const sendDeafultMessage = () => {
  setTimeout(() => {
    appendMessage('你好？我是 ChatKG，有什么可以帮你？😊', 'received')
  }, 1000);
}

const clearChat = async () => {
  state.messages = []
  state.history = []
  state.sessionId = null
  state.sessionTitle = ''
  info.title = default_info.title
  info.description = default_info.description
  info.image = default_info.image
  info.graph = default_info.graph
  info.sents = default_info.sents
  sendDeafultMessage()
}

onMounted(() => {
  sendDeafultMessage()
  myChart = echarts.init(document.getElementById('lite_graph'))
  
  // 检查是否有会话ID
  const sessionId = route.query.session
  if (sessionId) {
    loadSessionHistory(sessionId)
  }
})
</script>

<style lang="less" scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 135px);
}

.chat-header {
  padding: 20px;
  text-align: center;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  border-radius: 8px;

  h1 {
    margin: 0;
    font-size: 24px;
    color: #333;
  }
}

.chat-content {
  display: flex;
  gap: 1.5rem;
  flex: 1;
  overflow: hidden;
}

.chat {
  display: flex;
  width: 100%;
  max-width: 800px;
  flex-grow: 1;
  margin: 0 auto;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0px 0.3px 0.9px rgba(0, 0, 0, 0.12), 0px 0.6px 2.3px rgba(0, 0, 0, 0.1),
    0px 1px 5px rgba(0, 0, 0, 0.08);
}

.chat-box {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;

  // 平滑滚动
  scroll-behavior: smooth;

  &::-webkit-scrollbar {
    width: 0rem;
  }
}

.message-box {
  width: fit-content;
  display: inline-block;
  padding: 0.5rem;
  border-radius: 0.5rem;
  margin: 0.5rem 0;
  box-sizing: border-box;
  padding: 10px 16px;
  user-select: text;
  word-break: break-word;
  font-size: 14px;
  line-height: 20px;
  font-variation-settings: 'wght' 400, 'opsz' 10.5;
  font-weight: 400;
  box-shadow: 0px 0.3px 0.9px rgba(0, 0, 0, 0.12), 0px 1.6px 3.6px rgba(0, 0, 0, 0.16);
  max-width: 80%;
}

.message-box.sent {
  color: white;
  background-color: #efefef;
  // background: linear-gradient(90deg, #006880 10.79%, #005366 87.08%);
  background: linear-gradient(90deg, #40788c 10.79%, #005f77 87.08%);
  // background-color: #333;
  align-self: flex-end;
}

.message-box.received {
  color: #111111;
  background-color: #ffffff;
  text-align: left;
}

p.message-text {
  word-wrap: break-word;
  margin-bottom: 0;
}

img.message-image {
  max-width: 300px;
  max-height: 50vh;
  object-fit: contain;
}

.input-box {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-top: 1px solid #ccc;
}

input.user-input {
  flex: 1;
  height: 40px;
  padding: 0.5rem 1rem;
  background-color: #fff;
  border: none;
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.1);
  font-size: 1.2rem;
  margin: 0 0.6rem;
  color: #111111;
  font-size: 16px;
  // line-height: 22px;
  font-variation-settings: 'wght' 400, 'opsz' 10.5;
}

.ant-btn-icon-only {
  font-size: 16px;
  border-radius: 8px;
  cursor: pointer;
}

// button:disabled {
//   // background: #ccc;
//   cursor: not-allowed;
// }

div.info {
  width: 400px;
  min-width: 400px;
  height: 100%;
  overflow-y: auto;
  flex-grow: 0;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0px 0.3px 0.9px rgba(0, 0, 0, 0.12), 0px 0.6px 2.3px rgba(0, 0, 0, 0.1),
    0px 1px 5px rgba(0, 0, 0, 0.08);

  & > h1 {
    font-size: 1.5rem;
    margin: 0.5rem 0;
    // padding: 0.5rem;
    // text-align: center;
  }

  p.description {
    font-size: 1rem;
    margin: 0;
    // padding: 0.5rem;
    // max-height: 10rem;
    margin-bottom: 20px;
    // text-align: center;
  }

  img {
    width: 100%;
    height: fit-content;
    object-fit: contain;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }

  #lite_graph {
    width: 400px;
    height: 300px;
    background: #f5f5f5;
    // border: 4px solid #ccc;
    border-radius: 8px;
    margin-bottom: 1rem;
    box-shadow: 0px 0.3px 0.9px rgba(0, 0, 0, 0.12), 0px 0.6px 2.3px rgba(0, 0, 0, 0.1),
      0px 1px 5px rgba(0, 0, 0, 0.08);
  }
}

.process-result {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;

  h3 {
    margin: 0 0 15px 0;
    font-size: 18px;
    color: #333;
    font-weight: 600;
    border-bottom: 2px solid #1890ff;
    padding-bottom: 8px;
  }

  .result-section {
    margin-bottom: 15px;
    padding: 12px;
    background: #fff;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border: 1px solid #f0f0f0;

    h4 {
      margin: 0 0 10px 0;
      font-size: 16px;
      color: #333;
      font-weight: 500;
    }

    .status {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 4px;
      font-size: 13px;
      margin-bottom: 10px;
      font-weight: 500;

      &.success {
        background: #e6f7ff;
        color: #1890ff;
        border: 1px solid #91d5ff;
      }

      &.failed {
        background: #fff1f0;
        color: #ff4d4f;
        border: 1px solid #ffa39e;
      }
    }
  }

  .entities, .intents {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
  }

  .entity-tag, .intent-tag {
    padding: 6px 12px;
    background: #f0f5ff;
    border-radius: 4px;
    font-size: 13px;
    color: #2f54eb;
    border: 1px solid #adc6ff;
    font-weight: 500;
  }

  .answer-item {
    margin-bottom: 12px;
    padding: 12px;
    background: #fafafa;
    border-radius: 6px;
    border: 1px solid #f0f0f0;

    .answer-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;

      .course {
        color: #1890ff;
        font-weight: 600;
      }

      .intent {
        color: #666;
        font-weight: 500;
      }
    }

    .answer-content {
      font-size: 14px;
      color: #333;
      line-height: 1.6;
      background: #fff;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid #f0f0f0;
    }
  }
}
</style>

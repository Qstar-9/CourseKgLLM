<template>
  <div class="welcome">
    <h1>{{ title }}</h1>
    <p class="main-description">{{ description }}</p>
    <div class="features">
      <h2>系统功能</h2>
      <ul>
        <li v-for="(feature, index) in features" :key="index">
          {{ feature }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const title = ref('基于知识图谱与大模型联合推理的智能问答系统')
const features = ref([
  '1. 图谱问答：输入问题，获取相关的答案',
  '2. 多轮筛选：在对话页面，可以通过多轮对话筛选来缩小搜索范围。例如，可以根据实体、具体类别、类型等进行筛选，以快速找到所需的专业知识。',
  '3. 知识图谱可视化：在知识图谱页面，用户可以通过可视化界面直观地了解实体之间的关系。可以缩放、平移和旋转图谱以查看不同层次的关系，还可以点击实体节点查看更多详细信息。',
  '4. 实体相关信息查看：可以通过右侧知识图谱下方的相关信息查看实体所有出现的地方，帮助全面查询理解，更清晰全面。'
])
</script>

<style scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 50px;
  color: #333;
  text-align: center;
  padding: 0 20px;
}

h1 {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 20px;
  margin-top: 50px;
}

.main-description {
  font-size: 20px;
  text-align: center;
  margin-bottom: 30px;
  color: #666;
}

.features {
  max-width: 800px;
  margin: 0 auto 40px;
  text-align: left;
}

.features h2 {
  font-size: 24px;
  margin-bottom: 20px;
  text-align: center;
}

.features ul {
  list-style: none;
  padding: 0;
}

.features li {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

img {
  width: 700px;
  height: 400px;
  object-fit: cover;
  margin-top: 30px;
  box-shadow: 0px 5px 10px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}
</style>

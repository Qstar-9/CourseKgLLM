<template>
  <div class="graph-container">
    <div class="graph-header">
      <div class="switch-buttons">
        <button 
          :class="{ active: state.currentView === 'all' }" 
          @click="switchView('all')"
        >全部图谱</button>
          <button 
          :class="{ active: state.currentView === 'sub' }" 
          @click="switchView('sub')"
        >子图谱</button>
      </div>
    </div>
    <div id="graph-main" ref="chartRef"></div>
    <div id="node-attr-info" v-if="state.showAttrInfo">
      <h3>{{ state.selectedNode?.name }}</h3>
      <ul>
        <li v-for="(val, key) in state.selectedNode?.attributes" :key="key">
          <strong>{{ key }}：</strong>{{ val }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const chartRef = ref(null)
const state = reactive({
  graph: {},
  searchText: '',
  showInfo: true,
  nodeInfo: [],
  currentView: 'sub', // 'sub' 或 'all'
  showAttrInfo: false,
  selectedNode: null
})

let myChart;

const fetchGraphData = async (viewType) => {
  const endpoint = viewType === 'sub' ? '/api/graph' : '/api/graph/all'
  try {
    const response = await axios.get(endpoint)
    const webkitDep = response.data.data
    state.graph = webkitDep
    myChart.hideLoading()
    
    webkitDep.nodes.forEach(function (node) {
      node.label = {
        show: node.symbolSize > 100
      }
      node.symbolSize = node.symbolSize / 10
    })
    
    const option = {
      tooltip: {
        show: true,
        showContent: true,
        trigger: 'item',
        triggerOn: 'mousemove',
        alwaysShowContent: false,
        showDelay: 0,
        hideDelay: 200,
        enterable: false,
        position: 'right',
        confine: false,
        formatter: (x) => {
          if (x.data.attributes) {
            return `${x.data.name}<br/>${Object.entries(x.data.attributes)
              .map(([key, val]) => `${key}: ${val}`)
              .join('<br/>')}`
          }
          return x.data.name
        }
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          animation: false,
          label: {
            position: 'right',
            formatter: '{b}'
          },
          draggable: true,
          data: webkitDep.nodes.map(function (node, idx) {
            node.id = idx;
            return node;
          }),
          modularity: true,
          categories: webkitDep.categories,
          force: {
            edgeLength: 5,
            repulsion: 20,
            gravity: 0.2
          },
          lineStyle: {
            color: 'source',
            curveness: 0.1
          },
          edges: webkitDep.links,
          roam: true,
          focusNodeAdjacency: true,
        }
      ],
    }
    myChart.setOption(option)
  } catch (error) {
    console.error('获取图谱数据失败:', error)
  }
}

const switchView = (viewType) => {
  state.currentView = viewType
  state.showAttrInfo = false
  state.selectedNode = null
  fetchGraphData(viewType)
}

const clickNode = (param) => {
  if (param.dataType === 'node') {
    state.selectedNode = param.data
    state.showAttrInfo = true
  }
}

onMounted(() => {
  myChart = echarts.init(chartRef.value)
  myChart.showLoading()
  fetchGraphData('sub')
  myChart.on('click', clickNode)
})
</script>

<style lang="less" scoped>
.graph-container {
  display: flex;
  flex-direction: row;
  max-width: 100%;
  height: calc(100vh - 200px);
  gap: 20px;
}

.graph-header {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 100;
  
  .switch-buttons {
    display: flex;
    gap: 10px;
    
    button {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      background: #f0f0f0;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        background: #e0e0e0;
      }
      
      &.active {
        background: #1890ff;
        color: white;
      }
    }
  }
}

#graph-main {
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  border-radius: 8px;
}

#node-attr-info {
  width: 350px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 8px #eee;
  padding: 1rem;
  margin-left: 20px;
  max-height: 100%;
  overflow-y: auto;
  
  h3 {
    margin-bottom: 1rem;
    color: #333;
  }
  
  ul {
    list-style: none;
    padding: 0;
    
    li {
      margin-bottom: 0.5rem;
      padding: 0.5rem;
      background: #f9f9f9;
      border-radius: 4px;
      
      strong {
        color: #666;
        margin-right: 0.5rem;
      }
    }
  }
}
</style>

<template>
  <div class="terminal-page">
    <div class="terminal-header">
      <div class="terminal-logo">
        <span class="logo-icon">S</span>
        <div>
          <div class="terminal-title">SanyMES 终端机</div>
          <div class="terminal-sub">{{ currentStation?.name || '请选择工位' }}</div>
        </div>
      </div>
      <div class="terminal-time">{{ currentTime }}</div>
    </div>

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="never" class="panel">
          <template #header>工位选择</template>
          <div
            v-for="st in stations"
            :key="st.id"
            class="station-select"
            :class="{ active: selectedStationId === st.id }"
            @click="selectStation(st.id)"
          >
            <div class="st-code">{{ st.code }}</div>
            <div class="st-name">{{ st.name }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card shadow="never" class="panel" v-if="currentTask">
          <template #header>
            <div class="task-title-bar">
              <span>当前任务 — {{ currentTask.work_order?.order_no || '' }}</span>
              <span :class="['status-tag', `status-${currentTask.status}`]">
                {{ STATUS_LABELS[currentTask.status] }}
              </span>
            </div>
          </template>

          <el-row :gutter="16">
            <el-col :span="14">
              <h3 style="margin-bottom: 12px; color: #fff">标准作业指导 (SOP)</h3>
              <div class="sop-box sop-large">{{ currentTask.sop_content }}</div>
              <div v-if="currentTask.safety_notes" class="safety-alert safety-large">
                ⚠ 安全提示：{{ currentTask.safety_notes }}
              </div>
            </el-col>
            <el-col :span="10">
              <h3 style="margin-bottom: 12px; color: #fff">操作面板</h3>
              <el-form label-position="top">
                <el-form-item label="操作员">
                  <el-input v-model="operator" placeholder="输入工号/姓名" size="large" />
                </el-form-item>
                <el-form-item label="报工备注">
                  <el-input v-model="reportNote" type="textarea" :rows="3" placeholder="可选" />
                </el-form-item>
              </el-form>

              <div class="action-buttons">
                <el-button
                  type="warning"
                  size="large"
                  :disabled="currentTask.status !== 'waiting'"
                  @click="handleStart"
                  :loading="acting"
                  style="width: 100%; margin-bottom: 12px"
                >
                  <el-icon><VideoPlay /></el-icon> 开工
                </el-button>
                <el-button
                  type="success"
                  size="large"
                  :disabled="currentTask.status !== 'in_progress'"
                  @click="handleComplete"
                  :loading="acting"
                  style="width: 100%"
                >
                  <el-icon><CircleCheck /></el-icon> 报完工
                </el-button>
              </div>

              <div class="task-info" v-if="currentTask.operator">
                <div>操作员：{{ currentTask.operator }}</div>
                <div v-if="currentTask.started_at">开工：{{ formatTime(currentTask.started_at) }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <el-card shadow="never" class="panel" v-else>
          <el-empty description="当前工位暂无待执行任务" />
        </el-card>

        <el-card shadow="never" class="panel" style="margin-top: 16px" v-if="stationTasks.length">
          <template #header>工位任务队列</template>
          <el-table :data="stationTasks" size="small">
            <el-table-column label="工单" width="160">
              <template #default="{ row }">{{ getOrderNo(row) }}</template>
            </el-table-column>
            <el-table-column prop="sequence" label="工序" width="60" align="center" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <span :class="['status-tag', `status-${row.status}`]">
                  {{ STATUS_LABELS[row.status] }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="selectTask(row)">选择</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { completeTask, getStations, getWorkOrders, startTask, STATUS_LABELS } from '../api'

const stations = ref([])
const orders = ref([])
const selectedStationId = ref(null)
const selectedTaskId = ref(null)
const operator = ref('张师傅')
const reportNote = ref('')
const acting = ref(false)
const currentTime = ref('')
let timer = null

const currentStation = computed(() => stations.value.find(s => s.id === selectedStationId.value))

const stationTasks = computed(() => {
  const tasks = []
  orders.value.forEach(o => {
    o.station_tasks?.forEach(t => {
      if (t.station.id === selectedStationId.value) {
        tasks.push({ ...t, work_order: o })
      }
    })
  })
  return tasks.sort((a, b) => {
    const statusOrder = { in_progress: 0, waiting: 1, completed: 2 }
    return (statusOrder[a.status] ?? 3) - (statusOrder[b.status] ?? 3) || a.sequence - b.sequence
  })
})

const currentTask = computed(() => {
  if (selectedTaskId.value) {
    return stationTasks.value.find(t => t.id === selectedTaskId.value)
  }
  return stationTasks.value.find(t => t.status === 'in_progress')
    || stationTasks.value.find(t => t.status === 'waiting')
})

function getOrderNo(task) {
  return task.work_order?.order_no || '-'
}

function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN')
}

function selectStation(id) {
  selectedStationId.value = id
  selectedTaskId.value = null
}

function selectTask(task) {
  selectedTaskId.value = task.id
}

async function reload() {
  orders.value = await getWorkOrders()
}

async function handleStart() {
  if (!operator.value) {
    ElMessage.warning('请输入操作员')
    return
  }
  acting.value = true
  try {
    await startTask(currentTask.value.id, operator.value)
    ElMessage.success('开工成功')
    await reload()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '开工失败')
  } finally {
    acting.value = false
  }
}

async function handleComplete() {
  if (!operator.value) {
    ElMessage.warning('请输入操作员')
    return
  }
  acting.value = true
  try {
    await completeTask(currentTask.value.id, operator.value, reportNote.value || null)
    ElMessage.success('报完工成功')
    reportNote.value = ''
    selectedTaskId.value = null
    await reload()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '报工失败')
  } finally {
    acting.value = false
  }
}

watch(selectedStationId, () => {
  selectedTaskId.value = null
})

onMounted(async () => {
  stations.value = await getStations()
  orders.value = await getWorkOrders()
  if (stations.value.length) {
    selectedStationId.value = stations.value[3]?.id || stations.value[0].id
  }
  currentTime.value = new Date().toLocaleString('zh-CN')
  timer = setInterval(() => {
    currentTime.value = new Date().toLocaleString('zh-CN')
  }, 1000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.terminal-page {
  margin: -24px;
  padding: 0;
}

.terminal-header {
  background: var(--sany-red);
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.terminal-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  color: #fff;
}

.terminal-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.terminal-sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.terminal-time {
  font-size: 16px;
  color: #fff;
  font-variant-numeric: tabular-nums;
}

.panel {
  margin-top: 16px;
}

.station-select {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.station-select:hover {
  border-color: var(--sany-red);
}

.station-select.active {
  border-color: var(--sany-red);
  background: rgba(230, 0, 18, 0.1);
}

.station-select .st-code {
  font-size: 11px;
  color: var(--text-muted);
}

.station-select .st-name {
  font-size: 14px;
  font-weight: 600;
  margin-top: 2px;
}

.sop-large {
  font-size: 16px;
  min-height: 200px;
}

.safety-large {
  font-size: 15px;
  padding: 14px 18px;
}

.task-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-buttons {
  margin-top: 16px;
}

.task-info {
  margin-top: 16px;
  padding: 12px;
  background: #0d1117;
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.8;
}
</style>

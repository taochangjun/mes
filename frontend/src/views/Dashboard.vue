<template>
  <div>
    <h1 class="page-title">PCC 生产控制中心</h1>
    <el-row :gutter="16" v-loading="loading">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ borderTop: `3px solid ${item.color}` }">
          <div class="label">{{ item.label }}</div>
          <div class="value">{{ item.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <span>在制工单</span>
          </template>
          <el-table :data="activeOrders" stripe>
            <el-table-column prop="order_no" label="工单号" width="160" />
            <el-table-column label="产品">
              <template #default="{ row }">{{ row.product.name }}</template>
            </el-table-column>
            <el-table-column label="客户" prop="customer" />
            <el-table-column label="进度" width="200">
              <template #default="{ row }">
                <el-progress
                  :percentage="calcProgress(row)"
                  :stroke-width="8"
                  :color="'#e60012'"
                />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <span :class="['status-tag', `status-${row.status}`]">
                  {{ STATUS_LABELS[row.status] }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <span>工位实时状态</span>
          </template>
          <div class="station-grid">
            <div
              v-for="st in stationStatus"
              :key="st.code"
              class="station-item"
              :class="st.active ? 'active' : ''"
            >
              <div class="st-code">{{ st.code }}</div>
              <div class="st-name">{{ st.name }}</div>
              <div class="st-status">{{ st.active ? '作业中' : '空闲' }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>
            <span>系统架构</span>
          </template>
          <div class="arch-flow">
            <div class="arch-layer">ERP / CRM / PLM</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-layer highlight">SanyMES（本系统）</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-layer">LES / WMS / AGV</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-layer">DNC / IoT / 设备</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getDashboard, getStations, getWorkOrders, STATUS_LABELS } from '../api'

const loading = ref(true)
const stats = ref({})
const orders = ref([])
const stations = ref([])

const statCards = computed(() => [
  { label: '工单总数', value: stats.value.total_orders ?? '-', color: '#3b82f6' },
  { label: '生产中', value: stats.value.in_progress_orders ?? '-', color: '#f59e0b' },
  { label: '已完工', value: stats.value.completed_orders ?? '-', color: '#22c55e' },
  { label: '质检合格率', value: `${stats.value.quality_pass_rate ?? '-'}%`, color: '#e60012' },
])

const activeOrders = computed(() =>
  orders.value.filter(o => ['released', 'in_progress'].includes(o.status))
)

const stationStatus = computed(() => {
  const activeStationIds = new Set()
  orders.value.forEach(o => {
    o.station_tasks?.forEach(t => {
      if (t.status === 'in_progress') activeStationIds.add(t.station.id)
    })
  })
  return stations.value.map(s => ({
    ...s,
    active: activeStationIds.has(s.id),
  }))
})

function calcProgress(order) {
  const tasks = order.station_tasks || []
  if (!tasks.length) return 0
  const done = tasks.filter(t => t.status === 'completed').length
  return Math.round((done / tasks.length) * 100)
}

onMounted(async () => {
  try {
    ;[stats.value, orders.value, stations.value] = await Promise.all([
      getDashboard(),
      getWorkOrders(),
      getStations(),
    ])
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.station-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.station-item {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.station-item.active {
  border-color: #f59e0b;
  background: #422006;
}

.st-code {
  font-size: 12px;
  color: var(--text-muted);
}

.st-name {
  font-size: 13px;
  font-weight: 600;
  margin: 4px 0;
}

.st-status {
  font-size: 11px;
  color: var(--text-muted);
}

.station-item.active .st-status {
  color: #fbbf24;
}

.arch-flow {
  text-align: center;
  padding: 8px 0;
}

.arch-layer {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
}

.arch-layer.highlight {
  background: rgba(230, 0, 18, 0.15);
  border-color: var(--sany-red);
  color: #fff;
  font-weight: 600;
}

.arch-arrow {
  color: var(--text-muted);
  padding: 4px 0;
  font-size: 12px;
}
</style>

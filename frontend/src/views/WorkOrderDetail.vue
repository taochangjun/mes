<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/work-orders')" style="margin-bottom: 20px">
      <template #content>
        <span style="font-size: 18px; font-weight: 600">{{ order?.order_no }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="16" v-if="order">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>工艺流程 — 工位任务</template>
          <el-steps :active="activeStep" finish-status="success" align-center style="margin-bottom: 24px">
            <el-step
              v-for="task in order.station_tasks"
              :key="task.id"
              :title="task.station.name"
              :description="STATUS_LABELS[task.status]"
            />
          </el-steps>

          <el-timeline>
            <el-timeline-item
              v-for="task in order.station_tasks"
              :key="task.id"
              :type="task.status === 'completed' ? 'success' : task.status === 'in_progress' ? 'warning' : 'info'"
              :timestamp="task.completed_at ? formatTime(task.completed_at) : (task.started_at ? formatTime(task.started_at) : '待开工')"
            >
              <div class="task-card">
                <div class="task-header">
                  <strong>{{ task.station.code }} — {{ task.station.name }}</strong>
                  <span :class="['status-tag', `status-${task.status}`]">
                    {{ STATUS_LABELS[task.status] }}
                  </span>
                </div>
                <div class="sop-box">{{ task.sop_content }}</div>
                <div v-if="task.safety_notes" class="safety-alert">
                  ⚠ 安全提示：{{ task.safety_notes }}
                </div>
                <div v-if="task.operator" style="margin-top: 8px; font-size: 13px; color: var(--text-muted)">
                  操作员：{{ task.operator }}
                  <span v-if="task.report_note"> · 备注：{{ task.report_note }}</span>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header>工单信息</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="产品">{{ order.product.name }}</el-descriptions-item>
            <el-descriptions-item label="客户">{{ order.customer || '-' }}</el-descriptions-item>
            <el-descriptions-item label="数量">{{ order.quantity }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <span :class="['status-tag', `status-${order.status}`]">
                {{ STATUS_LABELS[order.status] }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="优先级">P{{ order.priority }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(order.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>物料配送</template>
          <el-table :data="materials" size="small">
            <el-table-column label="物料">
              <template #default="{ row }">{{ row.material.name }}</template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="60" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'delivered' ? 'success' : row.status === 'shortage' ? 'danger' : 'info'"
                  size="small"
                >
                  {{ { pending: '待配送', delivered: '已送达', shortage: '缺料' }[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getOrderMaterials, getWorkOrder, STATUS_LABELS } from '../api'

const route = useRoute()
const loading = ref(true)
const order = ref(null)
const materials = ref([])

const activeStep = computed(() => {
  if (!order.value) return 0
  const tasks = order.value.station_tasks
  const inProgress = tasks.findIndex(t => t.status === 'in_progress')
  if (inProgress >= 0) return inProgress
  const lastDone = tasks.reduce((acc, t, i) => (t.status === 'completed' ? i : acc), -1)
  return lastDone + 1
})

function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(async () => {
  const id = route.params.id
  try {
    ;[order.value, materials.value] = await Promise.all([
      getWorkOrder(id),
      getOrderMaterials(id),
    ])
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.task-card {
  padding-bottom: 8px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
</style>

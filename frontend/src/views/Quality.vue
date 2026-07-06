<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h1 class="page-title" style="margin-bottom: 0">质量管理</h1>
      <el-button type="danger" @click="showCreate = true">
        <el-icon><Plus /></el-icon> 录入质检
      </el-button>
    </div>

    <el-table :data="records" v-loading="loading" stripe>
      <el-table-column label="工单" width="170">
        <template #default="{ row }">{{ getOrderNo(row.work_order_id) }}</template>
      </el-table-column>
      <el-table-column label="工位" width="140">
        <template #default="{ row }">{{ row.station.name }}</template>
      </el-table-column>
      <el-table-column prop="check_item" label="检验项" min-width="140" />
      <el-table-column prop="standard" label="标准" min-width="160" />
      <el-table-column prop="inspector" label="检验员" width="90" />
      <el-table-column label="结果" width="90">
        <template #default="{ row }">
          <span :class="['status-tag', row.result === 'pass' ? 'status-completed' : row.result === 'fail' ? 'status-blocked' : 'status-pending']">
            {{ STATUS_LABELS[row.result] }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.inspected_at) }}</template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="录入质检记录" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="工单">
          <el-select v-model="form.work_order_id" placeholder="选择工单" style="width: 100%">
            <el-option v-for="o in orders" :key="o.id" :label="o.order_no" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="工位">
          <el-select v-model="form.station_id" placeholder="选择工位" style="width: 100%">
            <el-option v-for="s in stations" :key="s.id" :label="`${s.code} ${s.name}`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="检验项">
          <el-input v-model="form.check_item" placeholder="如：底盘水平度" />
        </el-form-item>
        <el-form-item label="标准">
          <el-input v-model="form.standard" placeholder="如：≤ 2mm" />
        </el-form-item>
        <el-form-item label="检验员">
          <el-input v-model="form.inspector" />
        </el-form-item>
        <el-form-item label="结果">
          <el-radio-group v-model="form.result">
            <el-radio value="pass">合格</el-radio>
            <el-radio value="fail">不合格</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="danger" @click="handleCreate" :loading="creating">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createQualityRecord, getQualityRecords, getStations, getWorkOrders, STATUS_LABELS } from '../api'

const loading = ref(true)
const creating = ref(false)
const showCreate = ref(false)
const records = ref([])
const orders = ref([])
const stations = ref([])
const form = ref({
  work_order_id: null,
  station_id: null,
  check_item: '',
  standard: '',
  inspector: '王质检',
  result: 'pass',
  remark: '',
})

const orderMap = ref({})

function getOrderNo(id) {
  return orderMap.value[id] || `#${id}`
}

function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN')
}

async function load() {
  loading.value = true
  try {
    records.value = await getQualityRecords()
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!form.value.work_order_id || !form.value.station_id || !form.value.check_item) {
    ElMessage.warning('请填写完整信息')
    return
  }
  creating.value = true
  try {
    await createQualityRecord(form.value)
    ElMessage.success('质检记录已录入')
    showCreate.value = false
    await load()
  } catch (e) {
    ElMessage.error('录入失败')
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  ;[records.value, orders.value, stations.value] = await Promise.all([
    getQualityRecords(),
    getWorkOrders(),
    getStations(),
  ])
  orderMap.value = Object.fromEntries(orders.value.map(o => [o.id, o.order_no]))
  loading.value = false
})
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h1 class="page-title" style="margin-bottom: 0">工单管理</h1>
      <el-button type="danger" @click="showCreate = true">
        <el-icon><Plus /></el-icon> 新建工单
      </el-button>
    </div>

    <el-table :data="orders" v-loading="loading" stripe>
      <el-table-column prop="order_no" label="工单号" width="170" />
      <el-table-column label="产品" min-width="160">
        <template #default="{ row }">
          <div>{{ row.product.name }}</div>
          <div style="font-size: 12px; color: var(--text-muted)">{{ row.product.code }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="customer" label="客户" width="120" />
      <el-table-column prop="quantity" label="数量" width="70" align="center" />
      <el-table-column label="优先级" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.priority <= 2 ? 'danger' : row.priority <= 5 ? 'warning' : 'info'" size="small">
            P{{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <span :class="['status-tag', `status-${row.status}`]">
            {{ STATUS_LABELS[row.status] }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="140">
        <template #default="{ row }">
          <el-progress :percentage="calcProgress(row)" :stroke-width="6" color="#e60012" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/work-orders/${row.id}`)">详情</el-button>
          <el-button link type="warning" v-if="row.status === 'pending'" @click="handleRelease(row)">
            下达
          </el-button>
          <el-button link type="success" v-if="row.status !== 'pending'" @click="handleIssue(row)">
            配送物料
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建生产工单" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="产品">
          <el-select v-model="form.product_id" placeholder="选择产品" style="width: 100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.name} (${p.code})`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.quantity" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="form.customer" placeholder="客户名称" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-slider v-model="form.priority" :min="1" :max="10" :marks="{ 1: '最高', 5: '中', 10: '低' }" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="danger" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createWorkOrder, getProducts, getWorkOrders, issueMaterials, releaseWorkOrder, STATUS_LABELS } from '../api'

const loading = ref(true)
const creating = ref(false)
const showCreate = ref(false)
const orders = ref([])
const products = ref([])
const form = ref({ product_id: null, quantity: 1, customer: '', priority: 5 })

function calcProgress(order) {
  const tasks = order.station_tasks || []
  if (!tasks.length) return 0
  return Math.round((tasks.filter(t => t.status === 'completed').length / tasks.length) * 100)
}

async function load() {
  loading.value = true
  try {
    orders.value = await getWorkOrders()
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!form.value.product_id) {
    ElMessage.warning('请选择产品')
    return
  }
  creating.value = true
  try {
    await createWorkOrder(form.value)
    ElMessage.success('工单创建成功，已自动生成工位任务和物料清单')
    showCreate.value = false
    form.value = { product_id: null, quantity: 1, customer: '', priority: 5 }
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleRelease(row) {
  try {
    await releaseWorkOrder(row.id)
    ElMessage.success('工单已下达至车间')
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '下达失败')
  }
}

async function handleIssue(row) {
  try {
    await issueMaterials(row.id)
    ElMessage.success('物料配送指令已下达至 LES')
    await load()
  } catch (e) {
    ElMessage.error('配送失败')
  }
}

onMounted(async () => {
  ;[orders.value, products.value] = await Promise.all([getWorkOrders(), getProducts()])
  loading.value = false
})
</script>

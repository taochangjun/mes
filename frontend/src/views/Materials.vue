<template>
  <div>
    <h1 class="page-title">物料管理</h1>
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="8">
        <div class="stat-card">
          <div class="label">物料种类</div>
          <div class="value">{{ materials.length }}</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="label">关重件</div>
          <div class="value">{{ criticalCount }}</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="label">低库存关重件</div>
          <div class="value" style="color: #f87171">{{ lowStockCount }}</div>
        </div>
      </el-col>
    </el-row>

    <el-table :data="materials" v-loading="loading" stripe>
      <el-table-column prop="code" label="物料编码" width="160" />
      <el-table-column prop="name" label="物料名称" min-width="160" />
      <el-table-column prop="unit" label="单位" width="70" align="center" />
      <el-table-column label="关重件" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_critical" type="danger" size="small">关重</el-tag>
          <span v-else style="color: var(--text-muted)">-</span>
        </template>
      </el-table-column>
      <el-table-column label="库存" width="120">
        <template #default="{ row }">
          <span :style="{ color: row.is_critical && row.stock_qty < 5 ? '#f87171' : '#fff' }">
            {{ row.stock_qty }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="库存状态" width="120">
        <template #default="{ row }">
          <el-tag
            v-if="row.is_critical && row.stock_qty < 5"
            type="danger"
            size="small"
          >库存不足</el-tag>
          <el-tag v-else type="success" size="small">正常</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getMaterials } from '../api'

const loading = ref(true)
const materials = ref([])

const criticalCount = computed(() => materials.value.filter(m => m.is_critical).length)
const lowStockCount = computed(() =>
  materials.value.filter(m => m.is_critical && m.stock_qty < 5).length
)

onMounted(async () => {
  materials.value = await getMaterials()
  loading.value = false
})
</script>

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('./views/Dashboard.vue'), meta: { title: 'PCC 生产控制中心' } },
  { path: '/work-orders', component: () => import('./views/WorkOrders.vue'), meta: { title: '工单管理' } },
  { path: '/work-orders/:id', component: () => import('./views/WorkOrderDetail.vue'), meta: { title: '工单详情' } },
  { path: '/terminal', component: () => import('./views/Terminal.vue'), meta: { title: 'MES 终端机' } },
  { path: '/materials', component: () => import('./views/Materials.vue'), meta: { title: '物料管理' } },
  { path: '/quality', component: () => import('./views/Quality.vue'), meta: { title: '质量管理' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

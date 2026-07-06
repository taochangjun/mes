import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDashboard = () => api.get('/dashboard').then(r => r.data)
export const getProducts = () => api.get('/products').then(r => r.data)
export const getMaterials = () => api.get('/materials').then(r => r.data)
export const getStations = () => api.get('/stations').then(r => r.data)
export const getWorkOrders = () => api.get('/work-orders').then(r => r.data)
export const getWorkOrder = (id) => api.get(`/work-orders/${id}`).then(r => r.data)
export const createWorkOrder = (data) => api.post('/work-orders', data).then(r => r.data)
export const releaseWorkOrder = (id) => api.post(`/work-orders/${id}/release`).then(r => r.data)
export const issueMaterials = (id) => api.post(`/work-orders/${id}/issue-materials`).then(r => r.data)
export const getOrderMaterials = (id) => api.get(`/work-orders/${id}/materials`).then(r => r.data)
export const getProductBom = (id) => api.get(`/products/${id}/bom`).then(r => r.data)
export const startTask = (id, operator) => api.post(`/station-tasks/${id}/start`, { operator }).then(r => r.data)
export const completeTask = (id, operator, report_note) =>
  api.post(`/station-tasks/${id}/complete`, { operator, report_note }).then(r => r.data)
export const getQualityRecords = (workOrderId) =>
  api.get('/quality-records', { params: { work_order_id: workOrderId } }).then(r => r.data)
export const createQualityRecord = (data) => api.post('/quality-records', data).then(r => r.data)

export const STATUS_LABELS = {
  pending: '待下达',
  released: '已下达',
  in_progress: '生产中',
  completed: '已完工',
  closed: '已关闭',
  waiting: '待开工',
  blocked: '异常',
  pass: '合格',
  fail: '不合格',
}

export default api

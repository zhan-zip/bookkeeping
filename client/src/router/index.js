import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/overview',
  },
  {
    path: '/overview',
    name: 'Overview',
    component: () => import('@/views/Overview.vue'),
    meta: { title: '总览' },
  },
  {
    path: '/records',
    name: 'Records',
    component: () => import('@/views/Records.vue'),
    meta: { title: '流水' },
  },
  {
    path: '/wishes',
    name: 'Wishes',
    component: () => import('@/views/Wishes.vue'),
    meta: { title: '心愿' },
  },
  {
    path: '/report',
    name: 'Report',
    component: () => import('@/views/Report.vue'),
    meta: { title: '月报' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '设置' },
  },
]

const router = createRouter({
  history: createWebHistory('/bookkeeping/'),
  routes,
})

export default router
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'
import { useFormStore } from './stores/useFormStore'

// 布局组件可以在首屏加载
import MainLayout from './layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/login', 
      component: () => import('./views/Login.vue') // 懒加载
    },
    {
      path: '/',
      component: MainLayout,
      redirect: () => {
        const formStore = useFormStore()
        return formStore.role === 'doctor' ? '/workbench' : '/patient/home'
      },
      children: [
        // 优化：路由懒加载，用到时才加载对应文件的代码
        { path: 'workbench', component: () => import('./views/Workbench.vue') },
        { path: 'history', component: () => import('./views/History.vue') },
        { path: 'profile', component: () => import('./views/Profile.vue') },
        { path: 'patient/home', component: () => import('./views/patient/PatientHome.vue') },
        { path: 'patient/report', component: () => import('./views/patient/PatientReport.vue') },
        { path: 'patient/knowledge', component: () => import('./views/patient/PatientKnowledge.vue') }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const formStore = useFormStore()
  // 如果已经登录了，还去访问 login 页，就重定向回首页
  if (to.path !== '/login' && !formStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && formStore.isLoggedIn) {
    next('/') 
  } else {
    next()
  }
})

const app = createApp(App)

app.use(createPinia()) 
app.use(ElementPlus)
app.use(router)

app.mount('#app')
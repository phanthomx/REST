import { createRouter, createWebHistory } from 'vue-router'
import Landing from '../view/Landing.vue'    // or '../views/...'
import Login from '../view/Login.vue'
import Register from '../view/Register.vue'
import Dashboard from '../view/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Landing },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { 
      path: '/dashboard', 
      component: Dashboard,
      meta: { requiresAuth: true } // Mark this as protected
    }
  ]
})

// GLOBAL GUARD
router.beforeEach((to, from) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { path: '/login' } // Kick them out if no token
  }
})

export default router
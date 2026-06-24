import { createRouter, createWebHistory } from 'vue-router';
import Login from '@/views/Login.vue';
import Register from '@/views/Register.vue';
import chat from '@/views/chat.vue';
import home from '@/views/home.vue';
// import Login from '../views/Login';
// import Register from '../views/Register';
// import Dashboard from '../views/Dashboard.vue';
import { authStore } from '@/store/auth'; // 导入authStore
const routes = [
  {
    path: '/',
    name: 'home',
    component: home  },
  {
    path: '/ctlogin',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/chat',
    name: 'chat',
    component: chat,
    meta: { requiresAuth: false }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 导航守卫 - 检查登录状态
router.beforeEach((to, from, next) => {
  const isAuthenticated = authStore.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/ctlogin');
  }

  if (to.path === '/highApp') {
    const userData = localStorage.getItem('user');
    const userObj = userData ? JSON.parse(userData) : {};
    if (!isAuthenticated || userObj.level !== '高') {
      return next('/ctlogin');
    }
  }

  next();
});

export default router;
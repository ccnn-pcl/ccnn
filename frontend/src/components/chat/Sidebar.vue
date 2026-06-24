<template>
  <div class="sidebar" :class="{ 'sidebar-hidden': !visible }">
    <div class="user-card">
      <p class="card-label">当前登录用户</p>
      <h3 v-if="user.username" class="user-info">
        👤 {{ user.username }}<br>
        ⭐ 信任评分：{{ score }}
      </h3>
      <h3 v-else class="user-info">👤 未登录</h3>
    </div>
    <button class="btn-primary logout-btn" @click="$emit('logout')">
      退出登录
    </button>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: true },
  user: { type: Object, default: () => ({}) },
  score: { type: Number, default: 0 },
})
defineEmits(['logout'])
</script>

<style scoped>
.sidebar {
  width: 300px;
  background-color: white;
  border-right: 1px solid #e0e0e0;
  padding: 20px;
  overflow: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  transition: all 0.3s ease;
}
.sidebar::-webkit-scrollbar {
  display: none;
}
.sidebar-hidden {
  opacity: 0;
  width: 0;
  padding: 0;
  border: none;
  overflow: hidden;
}
.user-card {
  background-color: white;
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.card-label {
  margin: 0;
  color: #666;
  font-size: 20px;
}
.user-info {
  margin: 5px 0;
  color: #2196f3;
}
.btn-primary {
  background-color: #2196f3;
  color: white;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  border: none;
  transition: all 0.3s;
  cursor: pointer;
}
.btn-primary:hover {
  background-color: #64b5f6;
  transform: translateY(-2px);
}
.logout-btn {
  width: 100%;
}
</style>

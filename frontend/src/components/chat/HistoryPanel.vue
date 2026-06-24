<template>
  <div class="history-panel">
    <h3>📜 聊天历史记录</h3>
    <div v-for="(msg, index) in messages" :key="index" class="history-message">
      <div v-if="msg.role === 'user'">
        <strong>👤 用户 ({{ msg.timestamp }}):</strong>
        <p>{{ msg.content }}</p>
        <div v-if="msg.images && msg.images.length" class="history-images">
          <div v-for="(img, imgIndex) in msg.images" :key="imgIndex" class="history-image">
            <img :src="img" alt="历史图片">
          </div>
        </div>
      </div>
      <div v-else>
        <strong>🤖 AI ({{ msg.timestamp }}):</strong>
        <p v-html="msg.content"></p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  messages: { type: Array, default: () => [] },
})
</script>

<style scoped>
.history-panel {
  overflow-y: auto;
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
}
.history-message {
  margin-bottom: 15px;
}
.history-images {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.history-image img {
  max-width: 150px;
  border-radius: 8px;
}
</style>

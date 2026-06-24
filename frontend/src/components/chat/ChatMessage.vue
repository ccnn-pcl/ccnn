<template>
  <div class="message">
    <div v-if="message.role === 'user'" class="user-message">
      <div class="message-content">
        <div class="message-timestamp">{{ message.timestamp }}</div>
        <div class="message-text">{{ message.content }}</div>
        <div v-if="message.images && message.images.length" class="message-images">
          <div v-for="(img, imgIndex) in message.images" :key="imgIndex" class="message-image">
            <img :src="img" alt="聊天图片">
          </div>
        </div>
      </div>
      <div class="message-avatar">👤</div>
    </div>
    <div v-else class="assistant-message">
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <div class="message-timestamp">{{ message.timestamp }}</div>
        <div class="message-text" v-html="message.content"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: { type: Object, required: true },
})
</script>

<style scoped>
.message {
  margin-bottom: 15px;
}
.user-message,
.assistant-message {
  display: flex;
  gap: 10px;
}
.user-message {
  justify-content: flex-end;
}
.assistant-message {
  justify-content: flex-start;
}
.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.user-message .message-avatar {
  background-color: #e3f2fd;
}
.assistant-message .message-avatar {
  background-color: #e8f5e9;
}
.message-content {
  max-width: 70%;
}
.user-message .message-content {
  background-color: #e3f2fd;
  border-radius: 18px 18px 5px 18px;
  padding: 10px 15px;
}
.assistant-message .message-content {
  background-color: #e8f5e9;
  border-radius: 18px 18px 18px 5px;
  padding: 10px 15px;
}
.message-timestamp {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}
.message-text {
  color: #333;
  font-size: 17px;
  line-height: 1.65;
  letter-spacing: 0.2px;
}
.message-images {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.message-image img {
  max-width: 200px;
  border-radius: 8px;
}
</style>

<template>
  <div class="chat-input-container">
    <div class="chat-input-wrapper">
      <div class="input-section">
        <div v-if="attachments.length" class="attachments-preview">
          <div v-for="(attachment, index) in attachments" :key="index" class="attachment-item">
            <div v-if="isImageFile(attachment)" class="attachment-image">
              <img :src="attachment.preview" alt="附件预览">
            </div>
            <div v-else class="attachment-file">
              📄 {{ attachment.file.name }}
            </div>
            <button class="remove-btn" @click="$emit('remove-attachment', index)">×</button>
          </div>
        </div>

        <div class="input-wrapper">
          <textarea
            v-model="inputText"
            placeholder="请输入问题..."
            class="text-input auto-height"
            rows="2"
            @keydown.enter.prevent="$emit('send')"
          ></textarea>
          <div class="upload-section">
            <div class="upload-btn" @click="triggerUpload" title="上传图片或文件">
              📎
            </div>
            <input
              ref="fileInputRef"
              type="file"
              multiple
              @change="onFileChange"
              style="display: none"
            />
          </div>
          <button class="send-btn" @click="$emit('send')" :disabled="!inputText || disabled">
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  attachments: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'send', 'remove-attachment', 'file-upload'])

const inputText = ref(props.modelValue)
const fileInputRef = ref(null)

// 用户输入时通知父组件
watch(inputText, (val) => {
  emit('update:modelValue', val)
})

// 父组件重置时同步到子组件
watch(() => props.modelValue, (val) => {
  inputText.value = val
})

const triggerUpload = () => {
  fileInputRef.value?.click()
}

const onFileChange = (event) => {
  emit('file-upload', event)
  event.target.value = ''
}

const isImageFile = (attachment) => {
  return attachment.type.startsWith('image/')
}
</script>

<style scoped>
.chat-input-container {
  border-top: none;
  padding: 10px 20px 20px;
  background-color: transparent;
  display: flex;
  justify-content: center;
}
.chat-input-wrapper {
  max-width: 70%;
  width: 100%;
  background-color: #ffffff;
  border-radius: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 10px 14px;
  border: 1px solid #d0e3f0;
  transition: border-color 0.3s ease;
}
.chat-input-wrapper:hover {
  border-color: #2196f3;
}
.input-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.attachments-preview {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}
.attachment-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #eee;
}
.attachment-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.attachment-file {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f1f1f1;
}
.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
}
.input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}
.text-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 18px;
  padding: 8px 12px;
  background: transparent;
}
.text-input.auto-height {
  font-size: 17px;
  line-height: 1.6;
  padding: 12px 18px;
  border-radius: 20px;
  resize: none;
  outline: none;
  overflow-y: hidden;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
  background: transparent;
  transition: border-color 0.3s ease;
  max-height: 124px !important;
  overflow-y: auto !important;
}
.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.upload-btn {
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 5px;
}
.send-btn {
  background-color: #2196f3;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  cursor: pointer;
  font-size: 17px;
}
.send-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>

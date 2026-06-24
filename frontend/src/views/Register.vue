<template>
  <div class="register-container">
    <h2>注册</h2>
    <div class="register-card">
      <div class="input-section">
        <div class="form-group">
          <label><i class="fas fa-user"></i> 用户名：
            <input 
              v-model="username" 
              type="text" 
              class="form-control"
              placeholder="设置您的用户名"
              required
              :disabled="isSubmitting"
            >
          </label>
        </div>
        <div class="form-group">
          <label><i class="fas fa-lock"></i> 密&nbsp;&nbsp;&nbsp;码：
            <input 
              v-model="password" 
              type="password" 
              class="form-control"
              placeholder="设置您的密码（至少6位）"
              required
              :disabled="isSubmitting"
            >
          </label>
        </div>
        <div class="form-group">
          <label><i class="fas fa-lock"></i> 确认密码：
            <input 
              v-model="confirmPassword" 
              type="password" 
              class="form-control"
              placeholder="再次输入密码"
              required
              :disabled="isSubmitting"
            >
          </label>
        </div>
        <div class="form-group">
          <label><i class="fas fa-envelope"></i> 邮&nbsp;&nbsp;&nbsp;箱：
            <input
              v-model="email"
              type="email"
              class="form-control"
              placeholder="请输入邮箱地址"
              required
              :disabled="isSubmitting"
            >
          </label>
        </div>
        <!-- 人脸采集区域 -->
        <div class="camera-section">
          <div class="section-header">
            <i class="fas fa-camera"></i>
            <span>人脸采集</span>
            <div class="privacy-note">
              <i class="fas fa-shield-alt"></i> 仅用于身份验证
            </div>
          </div>
          
          <!-- 使用 FaceCamera 组件 -->
          <FaceCamera 
            ref="faceCamera"
            @captured="handleFaceCaptured"
            @error="handleCameraError"
            @preview="setPreviewImage"
            @retake="handleRetake"
          />
          
          <div class="preview-controls" v-if="previewImage">
            <div class="preview-container">
              <div>
                  <img :src="previewImage" alt="人脸预览" class="preview-image">
              </div>
              <div>
                <button 
                  @click="retakePhoto" 
                  class="btn btn-sm btn-outline"
                  type="button"
                >
                <i class="fas fa-redo"></i> 重新拍摄
              </button>
              </div>
              
            </div>
          </div>
        </div>
        <!-- 操作按钮 -->
        <div class="action-section">
          <button 
            @click="handleSubmit"
            class="btn btn-primary btn-block"
            :disabled="isSubmitting || !canSubmit"
          >
            <span v-if="isSubmitting">
              <i class="fas fa-spinner fa-spin"></i> 注册中...
            </span>
            <span v-else>
              <i class="fas fa-user-plus"></i> 注册
            </span>
          </button>
        </div>
      </div>
      <!-- 状态消息 -->
      <div v-if="message" class="alert" :class="alertClass">
        <i :class="statusIcon"></i> {{ message }}
      </div>
    
      <div class="login-link">
        已有账号? <router-link to="/ctlogin">立即登录</router-link>
      </div>
    </div>      
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import FaceCamera from '@/components/FaceCamera.vue';
import authApi from '@/api/auth';
import useGeolocation from '@/composables/useGeolocation';

export default {
  components: { FaceCamera },
  setup() {
    const username = ref('');
    const password = ref('');
    const confirmPassword = ref('');
    const email = ref('');
    const faceData = ref(null);
    const previewImage = ref(null);
    const isSubmitting = ref(false);
    const message = ref('');
    const alertClass = ref('');
    const similarityError = ref(false);
    const existingUser = ref('');
    const similarity = ref(0);
    const router = useRouter();
    const faceCamera = ref(null);
    const { getLocation } = useGeolocation();
    let cachedLocation = null;
    let locationTimer = null;

    const refreshLocation = () => {
      getLocation().then((loc) => {
        if (loc) cachedLocation = loc
        console.log('📍 注册页位置:', loc)
      })
    }

    onMounted(() => {
      refreshLocation()
      locationTimer = setInterval(refreshLocation, 2 * 60 * 1000)
    })

    onUnmounted(() => {
      if (locationTimer) clearInterval(locationTimer)
    })

    const canSubmit = computed(() => {
      return username.value && password.value && confirmPassword.value && faceData.value;
    });

    // 用户名校验
    const validateUsername = () => {
      if (!username.value) return '用户名不能为空';
      if (username.value.length < 2) return '用户名至少2个字符';
      if (username.value.length > 20) return '用户名不能超过20个字符';
      if (/[^a-zA-Z0-9_\u4e00-\u9fa5]/.test(username.value)) return '用户名只能包含中文、字母、数字和下划线';
      return null;
    };

    // 密码校验
    const validatePassword = () => {
      if (!password.value) return '密码不能为空';
      if (password.value.length < 6) return '密码至少6位';
      if (password.value.length > 32) return '密码不能超过32位';
      return null;
    };

    // 确认密码校验
    const validateConfirmPassword = () => {
      if (!confirmPassword.value) return '请再次输入密码';
      if (password.value !== confirmPassword.value) return '两次密码输入不一致';
      return null;
    };

    const statusIcon = computed(() => {
      return {
        'alert-success': 'fas fa-check-circle',
        'alert-danger': 'fas fa-exclamation-circle',
        'alert-info': 'fas fa-info-circle'
      }[alertClass.value] || 'fas fa-info-circle';
    });

    const handleFaceCaptured = (base64Data) => {
      faceData.value = base64Data;
      message.value = '人脸照片已拍摄';
      alertClass.value = 'alert-info';
    };

    const setPreviewImage = (dataUrl) => {
      previewImage.value = dataUrl;
    };

    const handleCameraError = (error) => {
      message.value = error;
      alertClass.value = 'alert-danger';
    };

    const handleRetake = () => {
      faceData.value = null;
      previewImage.value = null;
    };

    const retakePhoto = () => {
      faceData.value = null;
      previewImage.value = null;
      if (faceCamera.value) {
        faceCamera.value.retake();
      }
    };
    // email正则校验
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    const validateEmail = () => {
      if (!email.value) return '邮箱不能为空';
      if (!emailRegex.test(email.value)) return '邮箱格式不正确';
      return null;
    };
    const handleSubmit = async () => {
      // 逐项校验
      const errors = [
        validateUsername(),
        validatePassword(),
        validateConfirmPassword(),
        validateEmail(),
      ].filter(Boolean)

      if (errors.length > 0) {
        message.value = errors[0];
        alertClass.value = 'alert-danger';
        return;
      }

      if (!faceData.value) {
        message.value = '请先拍照完成人脸采集';
        alertClass.value = 'alert-danger';
        return;
      }

      isSubmitting.value = true;
      message.value = '注册中...';
      alertClass.value = 'alert-info';

      try {
        if (!cachedLocation) {
          cachedLocation = await Promise.race([
            getLocation(),
            new Promise((r) => setTimeout(() => r(null), 2000)),
          ])
        }

        const data = await authApi.register({
          username: username.value,
          password: password.value,
          image: faceData.value,
          email: email.value,
          location: cachedLocation,
        });

        if (data.success) {
          message.value = '注册成功！';
          alertClass.value = 'alert-success';
          setTimeout(() => {
            router.push('/');
          }, 2000);
        } else {
          console.log(data.message);
          if (data.message.includes('高度相似')) {
            similarityError.value = true;
            existingUser.value = data.existingUser || '现有用户';
            similarity.value = Math.round((data.similarity || 0.7) * 100);
            message.value = `检测到您可能与用户 ${existingUser.value} 高度相似 (相似度 ${similarity.value}%)`;
          } else {
            message.value = '注册失败: ' + data.message;
          }
          alertClass.value = 'alert-danger';
        }
      } catch (error) {
        if (error.response && error.response.status === 409) {
          const responseData = error.response.data;
          similarityError.value = true;
          existingUser.value = responseData.existingUser || '现有用户';
          similarity.value = Math.round((responseData.similarity || 0.7) * 100);
          message.value = '检测到您与现有用户高度相似,注册失败';
          alertClass.value = 'alert-danger';
        } else {
          message.value = '请求错误:' + error.message;
          alertClass.value = 'alert-danger';
        }
      } finally {
        isSubmitting.value = false;
      }
    };

    const tryLogin = () => {
      router.push({
        path: '/ctlogin',
        query: { username: existingUser.value }
      });
    };

    return {
      username,
      password,
      email,
      faceData,
      previewImage,
      isSubmitting,
      message,
      alertClass,
      similarityError,
      existingUser,
      similarity,
      canSubmit,
      statusIcon,
      handleFaceCaptured,
      setPreviewImage,
      handleCameraError,
      handleRetake,
      retakePhoto,
      handleSubmit,
      tryLogin,
      faceCamera
    };
  }
};
</script>

<style scoped>
.register-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: white;
  overflow: hidden;

}
.register-card {
  background: white;
  border-radius: 10px;
  padding: 30px;
  max-height: 50vh;
  overflow-y: auto;
}
h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 25px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 500;
  color: #495057;
}

.form-group label i {
  margin-right: 10px;
  width: 22px;
  text-align: center;
  color: #3494e6;
}

.form-control {
  width: 70%;
  padding: 12px 15px;
  border: 1px solid #ced4da;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-control:focus {
  border-color: #3494e6;
  box-shadow: 0 0 0 3px rgba(52, 148, 230, 0.15);
  outline: none;
}

.camera-section {
  margin: 25px 0;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e9ecef;
}

.section-header i {
  margin-right: 10px;
  font-size: 1.2rem;
  color: #3494e6;
}

.section-header span {
  flex: 1;
  font-weight: 500;
}

.privacy-note {
  font-size: 0.85rem;
  color: #6c757d;
  background: #e9f7fe;
  padding: 5px 10px;
  border-radius: 4px;
  margin-left: 15px;
}

.preview-controls {
  margin-top: 15px;
}

 .preview-container {
 text-align: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.preview-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  margin-bottom: 10px;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn-primary {
  background: #3494e6;
  color: white;
}

.btn-primary:hover {
  background: #2878c8;
}

.btn-outline {
  background: transparent;
  border: 1px solid #3494e6;
  color: #3494e6;
}

.btn-outline:hover {
  background: #e3f2fd;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-section {
  margin-top: 30px;
}

.btn-block {
  width: 100%;
  padding: 14px;
  font-size: 1.1rem;
  font-weight: 600;
}

.alert {
  padding: 15px;
  border-radius: 8px;
  margin-top: 20px;
  display: flex;
  align-items: center;
}

.alert i {
  margin-right: 10px;
  font-size: 1.3rem;
}

.alert-success {
  background: #d4f8e8;
  color: #0c5c2c;
  border: 1px solid #a3e6c5;
}

.alert-danger {
  background: #fce4e1;
  color: #cc0000;
  border: 1px solid #f5b7b1;
}

.alert-info {
  background: #e3f2fd;
  color: #0c5460;
  border: 1px solid #bbdefb;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  font-size: 0.95rem;
  color: #6c757d;
}

.login-link a {
  color: #3494e6;
  font-weight: 500;
  text-decoration: none;
}

/* 相似用户提示 */
.similarity-highlight {
  font-weight: bold;
  color: #e74c3c;
}
</style>

<template>
  <div class="login-container">
    <h2>认证登录</h2>
    
    <div class="login-card">
      <!-- 用户名密码输入区域 -->
      <div class="input-section">
        <div class="form-group">
          <label>
            <i class="fas fa-user"></i> 用户名：
            <input 
              v-model="username" 
              type="text" 
              class="form-control"
              placeholder="请输入用户名"
              required
            >
          </label>
        </div>
        <div class="form-group">
          <label>
            <i class="fas fa-lock"></i> 密&nbsp;&nbsp;&nbsp;&nbsp;码：
            <input 
              v-model="password" 
              type="password" 
              class="form-control"
              placeholder="请输入密码"
              required
            >
          </label>
          
        </div>
        <div class="section-header">
          <i class="fas fa-camera"></i>
          <span>人脸识别</span>
          <button 
            v-if="cameraActive" 
            @click="toggleCamera" 
            class="btn btn-sm btn-secondary"
          >
            关闭摄像头
          </button>
          <button 
            v-else 
            @click="toggleCamera" 
            class="btn btn-sm btn-primary"
          >
            启动摄像头
          </button>
        </div>
        
        <div v-if="cameraActive" class="camera-container">
          <FaceCamera 
            ref="faceCamera"
            @captured="handleFaceCaptured"
            @error="handleCameraError"
            @preview="setPreviewImage"
            @retake="handleRetake"
          />
          
          <div class="camera-controls">
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
        </div>
        
        <div v-else class="camera-placeholder">
          <i class="fas fa-user-circle"></i>
          <p>摄像头未激活</p>
        </div>
      </div>

      
      
      <!-- 操作按钮 -->
      <div class="action-section">
        <button 
          @click="handleLogin"
          class="btn btn-primary btn-block"
          :disabled="isLoggingIn || !canLogin"
        >
          <span v-if="isLoggingIn">
            <i class="fas fa-spinner fa-spin"></i> 登录中...
          </span>
          <span v-else>
            <i class="fas fa-sign-in-alt"></i> 登录
          </span>
        </button>
        
        <div class="login-options">
          <router-link to="/register">注册新账号</router-link>
          <!-- <router-link to="/forgot-password">忘记密码？</router-link> -->
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, defineComponent, watch, onMounted, onUnmounted } from 'vue';
import FaceCamera from '@/components/FaceCamera.vue';
import authApi from '@/api/auth';
import { authActions } from '@/store/auth'
import useDeviceDetect from '@/plugins/deviceDetect';
import useGeolocation from '@/composables/useGeolocation';


export default defineComponent({
  name: 'LoginView',
  components: {
    FaceCamera
  },
  setup() {
    // 响应式数据
    const username = ref('');
    const password = ref('');
    const faceData = ref(null);
    const faceImage = ref(null);
    const cameraActive = ref(false);
    const isLoggingIn = ref(false);
    const message = ref('');
    const alertClass = ref('');
    const similarity = ref(null);
    const faceCamera = ref(null);
    const previewImage = ref(null);
    const { deviceInfo } = useDeviceDetect();
    const { getLocation } = useGeolocation();
    let cachedLocation = null;  // 提前获取，登录时不等待
    let locationTimer = null;

    // 获取并缓存位置
    const refreshLocation = () => {
      getLocation().then((loc) => {
        if (loc) cachedLocation = loc
        console.log('📍 登录页位置:', loc)
      })
    }

    // 页面加载时立刻开始获取位置
    onMounted(() => {
      refreshLocation()
      // 每2分钟刷新，防止用户停留过久位置过期
      locationTimer = setInterval(refreshLocation, 2 * 60 * 1000)
    })

    onUnmounted(() => {
      if (locationTimer) clearInterval(locationTimer)
    })


    // 修复1：监听输入变化重置错误状态
    watch([username, password], () => {
      if (message.value) {
        resetStatus();
      }
    });

    // 计算属性
    const canLogin = computed(() => {
      // return username.value && password.value && faceData.value;
          return (username.value && password.value) || faceData.value ;

    });
    
    const alertIcon = computed(() => {
      return {
        'alert-success': 'fas fa-check-circle',
        'alert-danger': 'fas fa-exclamation-circle',
        'alert-info': 'fas fa-info-circle'
      }[alertClass.value] || 'fas fa-info-circle';
    });
    
    // 方法
    const resetStatus = () => {
      message.value = '';
      alertClass.value = '';
      similarity.value = null;
    };

    const toggleCamera = () => {
      cameraActive.value = !cameraActive.value;
      if (!cameraActive.value) {
        faceData.value = null;
        faceImage.value = null;
      }
    };
    
    const captureFace = () => {
      if (faceCamera.value) {
        faceCamera.value.capture();
      }
    };
    
    // 修复2：正确处理人脸拍摄
    const handleFaceCaptured = (base64Data) => {
      // 只有在未登录状态下才更新人脸数据
      if (!isLoggingIn.value) {
        faceData.value = base64Data;
        faceImage.value = `data:image/jpeg;base64,${base64Data}`;
        message.value = '人脸照片已拍摄';
        alertClass.value = 'alert-info';
      }
    };
    
    const setPreviewImage = (dataUrl) => {
      previewImage.value = dataUrl;
    };
    
    // 修复3：完整重新拍摄逻辑
    const handleRetake = () => {
      faceData.value = null;
      faceImage.value = null;
      previewImage.value = null;
      resetStatus();
      // cameraActive.value = false;
      
    };
    
    const retakePhoto = () => {
      handleRetake();
      if (faceCamera.value) {
        faceCamera.value.retake();
      }
    };
    
    const handleCameraError = (error) => {
      message.value = error;
      alertClass.value = 'alert-danger';
      cameraActive.value = false;
    };
    const mkInput = (name, value) => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    return input;
}
    const handleLogin = async () => {
      if (!canLogin.value) {
        if (!faceData.value) {
          message.value = '请拍摄人脸照片';
        } else {
          message.value = '请输入用户名和密码';
        }
        alertClass.value = 'alert-danger';
        return;
      }
      
      isLoggingIn.value = true;
      message.value = '正在进行认证...';
      alertClass.value = 'alert-info';
      
      try {
        // 如果后台还没拿到位置，再给 2 秒机会（不卡太久）
        if (!cachedLocation) {
          cachedLocation = await Promise.race([
            getLocation(),
            new Promise((r) => setTimeout(() => r(null), 2000)),
          ])
        }

        const data = await authApi.login({
          username: username.value,
          password: password.value,
          image: faceData.value,
          deviceInfo: deviceInfo.value,
          location: cachedLocation,  // 提前获取的经纬度（可能为 null）
        });
        if (data.success) {
          authActions.login({
            username: data.username,
            level: data.trustscore,
          })
          message.value = data.message;
          similarity.value = Math.round(data.similarity * 100);
          alertClass.value = 'alert-success';
          // 人脸通过 → 提交 OIDC 登录（只带 username）
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = '/api/auth/login';

          form.appendChild(mkInput('username', data.username));
          form.appendChild(mkInput('trustscore', data.trustscore));
          document.body.appendChild(form);
          form.submit();
        } else {
          // 登录失败时重置状态
          isLoggingIn.value = false;
          faceData.value = null;
          faceImage.value = null;
          previewImage.value = null;
          
          message.value = data.message;
          alertClass.value = 'alert-danger';
          similarity.value = data.similarity ? 
            Math.round(data.similarity * 100) : null;
        }
      } catch (error) {
        // 修复5：确保异常情况下重置状态
        isLoggingIn.value = false;
        faceData.value = null;
        faceImage.value = null;
        previewImage.value = null;
        
        message.value = '请求错误: ' + error.message;
        alertClass.value = 'alert-danger';
        toggleCamera();

        setTimeout(() => {
            retakePhoto();
            username.value = null;
            password.value = null;
          }, 1500);
        
      }
    };
    
    return {
      username,
      password,
      faceData,
      faceImage,
      cameraActive,
      isLoggingIn,
      message,
      alertClass,
      similarity,
      faceCamera,
      previewImage,
      canLogin,
      alertIcon,
      toggleCamera,
      captureFace,
      handleFaceCaptured,
      handleCameraError,
      handleLogin,
      setPreviewImage,
      handleRetake, 
      retakePhoto   
    };
  }
});
</script>

<style scoped>
.login-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: white;
  overflow: hidden;
}

.login-card {
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

.login-options {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  font-size: 0.9rem;
}

.login-options a {
  color: #6c757d;
  text-decoration: none;
  transition: color 0.3s;
}

.login-options a:hover {
  color: #3494e6;
}

.alert {
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
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

.similarity {
  font-weight: bold;
  margin-left: 10px;
}

</style>
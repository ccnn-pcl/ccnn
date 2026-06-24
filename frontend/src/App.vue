<template>
  <div id="app">
    <header class="app-header">
      <h1>AI Twin</h1>
    </header>

    <main >
      <router-view></router-view> 
    </main>
    
    <footer class="app-footer">
      <p>AI Twin &copy; CCNN</p>
    </footer>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import { authStore, authActions } from './store/auth'
import useDeviceDetect from './plugins/deviceDetect';

export default {
  name: 'App',
  setup() {
    authActions.initAuthState()

    const { deviceInfo } = useDeviceDetect();

    const router = useRouter();

    const handleLogout = () => {
      authActions.logout();
      router.push('/ctlogin');
    };
    
    return {
      authStore,
      handleLogout,
      deviceInfo,
    };
  }
};
</script>

<style scoped>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.level-high {
  color: green;
}

.level-medium {
  color: yellow;
}
.app-header {
      height: 10vh;
      background: linear-gradient(135deg, #3494e6, #ec6ead);
      color: white;
      padding: 0 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: relative;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .app-header h1 {
      /* padding: 0, 20px; */
      font-size: 28px;
      font-weight: 700;
      letter-spacing: 2px;
      text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
    }
    
    .user-section {
      display: flex;
      align-items: center;
      gap: 15px;
      position: absolute;
      right: 20px;
      bottom: 10px;
    }
    
    .user-info {
      color: rgba(255, 255, 255, 0.9);
      font-size: 14px;
      text-align: right;
      line-height: 1.4;
      background: rgba(0, 0, 0, 0.2);
      padding: 6px 12px;
      border-radius: 4px;
    }
    
    .logout-btn {
      background: rgba(255, 255, 255, 0.9);
      color: #e74c3c;
      border: none;
      border-radius: 4px;
      padding: 6px 12px;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      transition: all 0.2s ease;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .logout-btn:hover {
      background: white;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
    }
    
    .logout-btn i {
      margin-right: 5px;
      font-size: 12px;
    }
main {
  margin: 0 auto;
  width: 100%;
  flex: 1;
  overflow: hidden;
}

.app-footer {
  height: 5vh;
  background: linear-gradient(135deg, #3494e6, #ec6ead);
  color: white;
  text-align: center;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

nav {
  margin-top: 1rem;
}

nav a, nav button {
  color: white;
  text-decoration: none;
  margin: 0 10px;
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 15px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

nav a:hover, nav button:hover {
  background: rgba(255, 255, 255, 0.3);
}

nav button {
  border: none;
  cursor: pointer;
  font: inherit;
}
.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #2c3e50;
}

.device-info {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.info-item {
  display: flex;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eaeaea;
}

.info-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.label {
  font-weight: 600;
  color: #555;
  width: 120px;
  flex-shrink: 0;
}

.value {
  color: #333;
  flex-grow: 1;
}
</style>

<style>
body {
  margin: 0;
  padding: 0;
}
</style>

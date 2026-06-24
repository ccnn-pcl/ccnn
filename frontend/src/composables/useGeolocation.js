import { ref } from 'vue'

// 获取高德 Web API Key（运行时配置，K8s ConfigMap 注入）
const getAmapKey = () => window.__APP_CONFIG__?.AMAP_KEY || import.meta.env.VITE_AMAP_KEY || ''

/**
 * 高德逆地理编码（在线，精确到街道）
 */
async function amapReverseGeocode(lat, lng) {
  const key = getAmapKey()
  if (!key) return null
  try {
    const url = `https://restapi.amap.com/v3/geocode/regeo?location=${lng},${lat}&key=${key}&extensions=base`
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 3000)
    const res = await fetch(url, { signal: controller.signal })
    clearTimeout(timer)
    const data = await res.json()
    if (data.status === '1' && data.regeocode) {
      const addr = data.regeocode.addressComponent
      // 格式：深圳市 南山区，直辖市只返回区（如 朝阳区）
      if (addr.district && addr.city && !addr.city.startsWith(addr.district)) {
        return addr.city + addr.district  // 地级市 + 区
      }
      return addr.district || addr.city || addr.province || null
    }
  } catch (e) {
    console.warn('高德解码失败:', e.message)
  }
  return null
}

// 离线城市匹配：用矩形范围覆盖主要城市（精度有限，作为高德失败的兜底）
const CITY_BOUNDS = [
  { name: '北京', latMin: 39.4, latMax: 41.1, lngMin: 115.4, lngMax: 117.5 },
  { name: '上海', latMin: 30.7, latMax: 31.6, lngMin: 120.9, lngMax: 122.0 },
  { name: '广州', latMin: 22.5, latMax: 23.6, lngMin: 112.9, lngMax: 113.9 },
  { name: '深圳', latMin: 22.4, latMax: 22.9, lngMin: 113.8, lngMax: 114.6 },
  { name: '成都', latMin: 30.1, latMax: 31.0, lngMin: 103.7, lngMax: 104.5 },
  { name: '杭州', latMin: 29.8, latMax: 30.6, lngMin: 119.7, lngMax: 120.8 },
  { name: '武汉', latMin: 29.9, latMax: 31.4, lngMin: 113.7, lngMax: 115.1 },
  { name: '重庆', latMin: 28.8, latMax: 30.1, lngMin: 106.0, lngMax: 107.0 },
  { name: '南京', latMin: 31.1, latMax: 32.6, lngMin: 118.4, lngMax: 119.4 },
  { name: '天津', latMin: 38.6, latMax: 40.3, lngMin: 116.7, lngMax: 118.1 },
  { name: '苏州', latMin: 30.8, latMax: 31.8, lngMin: 120.1, lngMax: 121.1 },
  { name: '西安', latMin: 33.7, latMax: 34.8, lngMin: 108.6, lngMax: 109.5 },
  { name: '长沙', latMin: 27.8, latMax: 28.7, lngMin: 112.5, lngMax: 113.6 },
  { name: '厦门', latMin: 24.2, latMax: 24.9, lngMin: 117.9, lngMax: 118.5 },
  { name: '福州', latMin: 25.5, latMax: 26.7, lngMin: 118.7, lngMax: 119.9 },
  { name: '青岛', latMin: 35.5, latMax: 37.2, lngMin: 119.5, lngMax: 121.0 },
  { name: '大连', latMin: 38.4, latMax: 39.6, lngMin: 121.0, lngMax: 122.3 },
  { name: '郑州', latMin: 34.2, latMax: 35.0, lngMin: 113.0, lngMax: 114.2 },
  { name: '济南', latMin: 36.0, latMax: 37.0, lngMin: 116.5, lngMax: 117.6 },
  { name: '昆明', latMin: 24.3, latMax: 25.6, lngMin: 102.3, lngMax: 103.2 },
  { name: '合肥', latMin: 31.3, latMax: 32.5, lngMin: 116.7, lngMax: 117.9 },
  { name: '东莞', latMin: 22.6, latMax: 23.3, lngMin: 113.5, lngMax: 114.3 },
  { name: '佛山', latMin: 22.6, latMax: 23.4, lngMin: 112.8, lngMax: 113.5 },
  { name: '珠海', latMin: 21.8, latMax: 22.5, lngMin: 113.1, lngMax: 113.8 },
]

function offlineDecodeCity(lat, lng) {
  for (const city of CITY_BOUNDS) {
    if (lat >= city.latMin && lat <= city.latMax && lng >= city.lngMin && lng <= city.lngMax) {
      return city.name
    }
  }
  return null
}

/**
 * 解码城市：优先高德 API，失败则离线匹配
 */
async function decodeCity(lat, lng) {
  const city = await amapReverseGeocode(lat, lng)
  if (city) return city
  return offlineDecodeCity(lat, lng)
}

export default function useGeolocation() {
  const location = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const cityName = ref(null)

  /**
   * 获取用户地理位置
   * @returns {Promise<{lat: number, lng: number, city: string|null} | null>}
   */
  const getLocation = () => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        error.value = '浏览器不支持地理位置功能'
        resolve(null)
        return
      }

      loading.value = true
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords
          const city = await decodeCity(latitude, longitude)
          cityName.value = city
          location.value = { lat: latitude, lng: longitude }
          error.value = null
          loading.value = false
          resolve({ lat: latitude, lng: longitude, city })
        },
        (err) => {
          // HTTP 环境下浏览器禁止定位是预期行为，静默处理
          if (!err.message.includes('secure origin')) {
            console.warn('获取地理位置失败:', err.message)
          }
          error.value = err.message
          loading.value = false
          resolve(null)
        },
        {
          enableHighAccuracy: true,
          timeout: 20000,
          maximumAge: 60000,
        }
      )
    })
  }

  return { location, loading, error, cityName, getLocation }
}

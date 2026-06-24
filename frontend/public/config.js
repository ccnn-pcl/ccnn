// 运行时配置（由 K8s ConfigMap 注入，无需重新打包镜像即可修改）
window.__APP_CONFIG__ = {
  AMAP_KEY: '',  // 高德地图 Key，K8s 部署时通过 ConfigMap 覆盖
}

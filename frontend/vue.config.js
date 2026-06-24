const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  lintOnSave: false,
  transpileDependencies: true,
  configureWebpack: {
    performance: {
      maxEntrypointSize: 500000,
      maxAssetSize: 500000,
    },
  },
  devServer: {
    https: false,
  },
})
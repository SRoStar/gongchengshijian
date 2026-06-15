const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  publicPath: '/pichemdata/',
  outputDir: 'dist',
  assetsDir: 'static',
  transpileDependencies: true,
  productionSourceMap: false,
  devServer: {
    port: 8080,
    open: true,
    proxy: {
      '/pichemdata/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: { '^/pichemdata/api': '/api' }
      }
    }
  }
})

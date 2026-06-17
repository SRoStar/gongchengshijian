import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './utils/request'
import i18n from './i18n'

// 导入 Element UI 的语言包，避免出现 "el.pageheader.title" 等英文键名
import elementZhLocale from 'element-ui/lib/locale/lang/zh-CN'
import elementEnLocale from 'element-ui/lib/locale/lang/en'
i18n.mergeLocaleMessage('zh', { el: elementZhLocale.el })
i18n.mergeLocaleMessage('en', { el: elementEnLocale.el })

Vue.config.productionTip = false
Vue.use(ElementUI, { i18n: (key, value) => i18n.t(key, value) })

new Vue({
  router,
  store,
  i18n,
  render: h => h(App)
}).$mount('#app')

  使用方式

##   开发模式（前后端分离）：

终端1：启动后端

  cd backend && python main.py

终端2：启动前端开发服务器

  cd frontend && npm run serve

前端通过代理访问后端 API

##   生产模式（前端构建后）：

  cd frontend && npm run build
  cd ../backend && python main.py

访问 http://localhost:8000/ 或 http://localhost:8000/pichemdata/

  注意事项

  - XRD 接口保持 /api/* 路径（与前端 vue.config.js 代理配置一致）
  - 如需添加 /pichemdata/api/v1/* 路由，可在 routers/ 中新增文件并注册到 main.py
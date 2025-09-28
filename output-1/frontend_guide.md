# 前端开发指导文档（Vue + Node.js + SQLite）

## 项目概述
基于Vue构建前端界面，实现内容展示、公开分享、用户评论等核心功能。前端通过API与Node.js后端交互，数据存储于SQLite数据库。

## 页面结构与文件规划

### 目录结构
```
frontend/
├── public/                 # 静态资源（Vue CLI构建后）
│   ├── index.html
│   └── ...
├── src/
│   ├── components/         # 通用组件
│   │   ├── CommentForm.vue
│   │   ├── CommentList.vue
│   │   └── ShareButton.vue
│   ├── views/             # 页面组件
│   │   ├── Home.vue       # 首页/列表页
│   │   ├── Detail.vue     # 详情页（含评论）
│   │   └── ShareView.vue  # 公开分享页
│   ├── api/               # API调用封装
│   │   └── api.js
│   ├── router/            # 路由配置
│   │   └── index.js
│   └── main.js
├── package.json
└── vue.config.js          # 配置代理解决开发环境跨域
```

### 核心页面说明

1. **首页/列表页 (Home.vue)**
   - 功能：展示内容列表，支持分页
   - 调用接口：`GET /api/v1/items?page=1&limit=10`

2. **详情页 (Detail.vue)**
   - 功能：展示单个内容详情及评论列表，提供评论表单
   - 调用接口：
     - `GET /api/v1/items/:id` - 获取详情
     - `GET /api/v1/comments?item_id=:id&page=1&limit=10` - 获取评论
     - `POST /api/v1/comments` - 提交评论

3. **公开分享页 (ShareView.vue)**
   - 功能：通过唯一分享链接访问内容（无需登录）
   - 调用接口：`GET /api/v1/shared/:share_token`

## API调用约定

- **基础路径**: `/api/v1`
- **开发环境代理**: 在 `vue.config.js` 中配置
  ```js
  module.exports = {
    devServer: {
      proxy: {
        '/api': {
          target: 'http://localhost:3000',
          changeOrigin: true
        }
      }
    }
  }
  ```

## 安全边界实现

- **评论功能**:
  - 前端对评论内容进行长度限制（≤500字符）
  - 提交时自动附加时间戳，防止重复提交
- **分享功能**:
  - 分享链接包含唯一token，前端通过token获取内容
  - 分享页不显示敏感操作按钮

## 构建与部署

- 开发命令: `npm run serve`
- 构建命令: `npm run build` (输出到 `dist/` 目录)
- 生产环境: 后端需托管 `dist/` 目录下的静态文件
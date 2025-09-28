# 前端开发指导文档

## 项目概述
根据PRD要求，开发一个知识库管理系统，包含文章列表、文章详情、文章创建/编辑功能。

## 页面结构与文件规划

### 项目框架选择
考虑到项目包含多个交互页面和表单操作，建议使用Vue框架开发。

### 目录结构
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── ArticleCard.vue
│   │   ├── ArticleForm.vue
│   │   └── Pagination.vue
│   ├── views/
│   │   ├── ArticleList.vue
│   │   ├── ArticleDetail.vue
│   │   └── ArticleCreate.vue
│   ├── router/
│   │   └── index.js
│   ├── api/
│   │   └── api.js
│   ├── App.vue
│   └── main.js
└── package.json
```

### 页面功能说明

#### 1. 文章列表页 (ArticleList.vue)
- **功能**: 展示所有文章的标题、摘要、创建时间
- **接口调用**: GET /api/v1/articles?page=1&limit=10
- **交互**: 点击文章标题跳转到详情页，支持分页

#### 2. 文章详情页 (ArticleDetail.vue)
- **功能**: 展示文章完整内容（Markdown格式渲染）
- **接口调用**: GET /api/v1/articles/:id
- **交互**: 支持返回列表页，编辑按钮跳转到编辑页

#### 3. 文章创建/编辑页 (ArticleCreate.vue)
- **功能**: 创建新文章或编辑现有文章
- **接口调用**: 
  - POST /api/v1/articles (创建)
  - PUT /api/v1/articles/:id (编辑)
- **表单字段**: title (string), content (markdown string)

## 路由配置
```javascript
// src/router/index.js
const routes = [
  { path: '/', component: ArticleList },
  { path: '/articles/:id', component: ArticleDetail },
  { path: '/create', component: ArticleCreate },
  { path: '/edit/:id', component: ArticleCreate }
]
```

## API 调用规范
- 基础URL: `/api/v1`
- 使用 axios 进行HTTP请求
- 请求头包含: `Content-Type: application/json`
- 认证: JWT token 在 Authorization header 中

## 构建输出
- 开发环境: `npm run serve`
- 生产构建: `npm run build` (输出到 frontend/dist/ 目录)
# 前后端对接文档

## 基础约定

### API 基础路径
- 开发环境: `http://localhost:3000/api/v1`
- 生产环境: `/api/v1` (同域)

### 跨域配置
后端需配置CORS:
```javascript
app.use(cors({
  origin: ['http://localhost:8080'], // 开发环境
  credentials: true
}));
```

### 数据格式
- **请求格式**: `application/json`
- **响应格式**: 
```json
{
  "success": true,
  "data": {},
  "message": ""
}
```
- **错误格式**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### Markdown 传输
- 前端发送原始Markdown字符串
- 后端存储原始Markdown
- 前端接收后使用 markdown-it 等库渲染

## 接口调用示例

### 获取文章列表
```javascript
// frontend/src/api/api.js
export const getArticles = (page = 1, limit = 10) => {
  return axios.get(`/api/v1/articles`, {
    params: { page, limit }
  });
};
```

### 创建文章
```javascript
export const createArticle = (articleData) => {
  return axios.post('/api/v1/articles', articleData);
};
```

## Mock 数据示例

### 文章列表响应
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": 1,
        "title": "Vue 3 入门指南",
        "content": "Vue 3 是 Vue.js 的最新版本...",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_items": 1
    }
  }
}
```

## 联调方式

### 开发环境
1. 后端启动: `cd backend && npm start` (端口3000)
2. 前端启动: `cd frontend && npm run serve` (端口8080)
3. 前端通过代理访问后端API

### 生产环境
1. 前端构建: `cd frontend && npm run build`
2. 后端配置静态文件服务指向 `frontend/dist/`
3. 启动后端服务，前端页面通过根路径访问

## 目录结构约定
- 前端项目: `frontend/` 目录
- 后端项目: `backend/` 目录
- 构建产物: `frontend/dist/` 目录
- 后端静态服务: 指向 `../frontend/dist`
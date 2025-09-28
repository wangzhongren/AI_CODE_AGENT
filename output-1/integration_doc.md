# 前后端对接文档

## 环境配置

### 开发环境
- **前端**: `http://localhost:8080` (Vue Dev Server)
- **后端**: `http://localhost:3000` (Express)
- **跨域处理**: 前端vue.config.js已配置代理，所有`/api`请求转发到后端

### 生产环境
- **统一域名**: 前后端部署在同一域名下
- **静态文件**: 后端直接提供`frontend/dist/`目录下的文件
- **API路径**: 保持`/api/v1`前缀

## 关键接口对接示例

### 1. 获取内容列表
```js
// 前端调用 (src/api/api.js)
export const fetchItems = (page = 1, limit = 10) => {
  return axios.get(`/api/v1/items`, { params: { page, limit } });
};

// 后端响应示例
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "title": "示例内容", "content": "..." }
    ],
    "pagination": { "page": 1, "limit": 10, "total": 1 }
  }
}
```

### 2. 提交评论
```js
// 前端调用
export const createComment = (commentData) => {
  return axios.post(`/api/v1/comments`, commentData);
};

// 后端验证
// - item_id: 必须存在且关联有效内容
// - author_name: 1-50字符
// - content: 1-500字符
```

### 3. 公开分享
```js
// 前端生成分享链接
const shareUrl = `${window.location.origin}/share/${token}`;

// 后端验证token有效性
// - 检查token是否存在
// - 检查是否过期（如有设置）
```

## Mock数据示例

### 内容列表
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "项目计划书",
        "content": "详细项目规划...",
        "created_at": "2023-08-01T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1
    }
  }
}
```

### 评论列表
```json
{
  "success": true,
  "data": {
    "comments": [
      {
        "id": 1,
        "author_name": "张三",
        "content": "很好的计划！",
        "created_at": "2023-08-02T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1
    }
  }
}
```

## 联调注意事项

1. **数据库初始化**: 后端启动时需确保SQLite数据库和表结构已创建
2. **CORS配置**: 开发环境后端需允许前端域名跨域
   ```js
   // 后端app.js
   app.use(cors({ origin: 'http://localhost:8080' }));
   ```
3. **错误处理**: 前端需处理后端返回的错误状态码（4xx/5xx）
4. **分享链接测试**: 确保分享页能独立访问且不依赖用户登录状态

## 安全测试要点

- [ ] 评论内容XSS防护（后端应转义或前端渲染时处理）
- [ ] 分享token不可预测性（使用crypto随机生成）
- [ ] 评论频率限制（防止刷评论）
- [ ] SQL注入防护（使用参数化查询）
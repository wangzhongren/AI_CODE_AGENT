# 后端开发指导文档

## 技术栈
- Node.js + Express
- MySQL 数据库
- JWT 认证

## 数据库设计

### 建表脚本
```sql
CREATE DATABASE knowledge_base;
USE knowledge_base;

CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## API 设计

### 基础配置
- API 前缀: `/api/v1`
- 端口: 3000
- 静态文件服务: `express.static(path.join(__dirname, '../frontend/dist'))`

### 接口详情

#### 1. 获取文章列表
- **路径**: GET /api/v1/articles
- **参数**: 
  - page (可选, 默认1)
  - limit (可选, 默认10)
- **响应**:
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": 1,
        "title": "文章标题",
        "content": "文章内容摘要...",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 50
    }
  }
}
```

#### 2. 获取文章详情
- **路径**: GET /api/v1/articles/:id
- **响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "完整文章标题",
    "content": "完整的Markdown内容",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 3. 创建文章
- **路径**: POST /api/v1/articles
- **请求体**:
```json
{
  "title": "新文章标题",
  "content": "Markdown格式的内容"
}
```
- **响应**: 同文章详情格式

#### 4. 更新文章
- **路径**: PUT /api/v1/articles/:id
- **请求体**: 同创建文章
- **响应**: 同文章详情格式

## 项目结构
```
backend/
├── app.js
├── routes/
│   └── articles.js
├── controllers/
│   └── articlesController.js
├── models/
│   └── Article.js
├── middleware/
│   └── auth.js
└── config/
    └── database.js
```

## 认证机制
- 使用 JWT token
- Authorization header 格式: `Bearer <token>`
- token 有效期: 24小时
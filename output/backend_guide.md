# 后端开发指导文档（Node.js + SQLite）

## 技术栈
- Web框架: Express.js
- 数据库: SQLite (使用sqlite3或better-sqlite3)
- 安全: Helmet, CORS, 输入验证

## 数据库设计

### 表结构

```sql
-- 内容表
CREATE TABLE items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 评论表
CREATE TABLE comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  author_name TEXT NOT NULL,
  content TEXT NOT NULL CHECK(length(content) <= 500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 分享令牌表
CREATE TABLE share_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL UNIQUE,
  token TEXT NOT NULL UNIQUE,
  expires_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
```

## API接口设计

### 基础约定
- **基础路径**: `/api/v1`
- **分页参数**: `page` (默认1), `limit` (默认10, 最大50)
- **响应格式**:
  ```json
  {
    "success": true,
    "data": { ... },
    "message": "操作成功"
  }
  ```

### 接口列表

1. **内容管理**
   - `GET /api/v1/items` - 获取内容列表（分页）
   - `GET /api/v1/items/:id` - 获取内容详情
   - `POST /api/v1/items` - 创建新内容

2. **评论功能**
   - `GET /api/v1/comments` - 获取评论列表（需item_id参数）
   - `POST /api/v1/comments` - 创建评论
     - 参数: `{ item_id, author_name, content }`

3. **分享功能**
   - `POST /api/v1/share` - 生成分享链接
     - 参数: `{ item_id }`
     - 返回: `{ token: "unique_token_string" }`
   - `GET /api/v1/shared/:token` - 通过token获取内容

## 安全边界实现

- **输入验证**:
  - 所有POST/PUT请求验证参数类型和长度
  - 评论内容限制500字符
- **分享安全**:
  - 每个内容仅生成一个有效token
  - token使用高强度随机字符串（32位以上）
  - 可选设置过期时间（默认7天）
- **防滥用**:
  - 评论接口添加基础频率限制（如10秒/次）

## 目录结构

```
backend/
├── app.js                 # 应用入口
├── routes/
│   ├── items.js           # 内容路由
│   ├── comments.js        # 评论路由
│   └── share.js           # 分享路由
├── controllers/           # 业务逻辑
├── models/                # 数据库操作
│   └── db.js              # SQLite连接
├── middleware/            # 中间件（验证、日志等）
└── public/                # 静态文件（生产环境指向frontend/dist）
```

## 静态文件服务

生产环境需托管Vue构建后的文件：
```js
// app.js
const path = require('path');
app.use(express.static(path.join(__dirname, '../frontend/dist')));
```

## 开发与部署

- 开发命令: `npm run dev` (使用nodemon)
- 生产构建: 确保先构建前端 `cd frontend && npm run build`
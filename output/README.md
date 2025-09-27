# 内容管理系统 - 后端

基于 Node.js + Express + SQLite 的内容管理系统后端，支持内容管理、评论功能和安全分享。

## 技术栈

- **Web框架**: Express.js
- **数据库**: SQLite (sqlite3)
- **安全**: Helmet, CORS, 输入验证, 频率限制
- **静态文件**: 自动服务 public 目录

## 功能特性

### 内容管理
- 创建、查看内容
- 分页列表获取

### 评论功能
- 为内容添加评论
- 评论内容限制500字符
- 频率限制（10秒/次）

### 分享功能
- 生成唯一分享令牌
- 令牌7天后自动过期
- 每个内容仅有一个有效分享链接

## 安全边界

- **输入验证**: 所有POST请求参数验证类型和长度
- **分享安全**: 高强度随机token (32位)，自动过期机制
- **防滥用**: 评论接口频率限制
- **数据完整性**: SQLite外键约束，级联删除

## API文档

完整的 OpenAPI 3.0 规范文档位于 `api_spec.json` 文件中。

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

## 目录结构

```
.
├── api_spec.json          # OpenAPI 接口文档
├── backend/
│   ├── app.js             # 应用入口
│   ├── routes/            # 路由定义
│   ├── controllers/       # 业务逻辑
│   ├── models/            # 数据库操作
│   │   └── db.js          # SQLite连接和表创建
│   ├── middleware/        # 中间件
│   │   ├── validation.js  # 输入验证
│   │   └── rateLimit.js   # 频率限制
│   └── data/              # SQLite数据库文件目录
├── public/                # 静态文件目录（前端构建产物）
├── package.json
└── README.md
```

## 快速开始

1. 安装依赖
   ```bash
   npm install
   ```

2. 开发模式启动
   ```bash
   npm run dev
   ```

3. 生产模式启动
   ```bash
   npm start
   ```

## 环境变量

- `PORT`: 服务器端口 (默认: 3000)

## 数据库

- 数据库文件位置: `backend/data/app.db`
- 自动创建表结构和外键约束
- 支持热重启，数据持久化

## 静态文件服务

后端自动提供 `public` 目录下的静态文件服务，前端构建产物应放置在此目录中。
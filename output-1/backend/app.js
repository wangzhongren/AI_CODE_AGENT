const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const path = require('path');

const app = express();

// 安全中间件
app.use(helmet());
app.use(cors());

// 解析JSON
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// 静态文件服务 - 指向 public 目录
app.use(express.static(path.join(__dirname, '../public')));

// API路由
app.use('/api/v1/items', require('./routes/items'));
app.use('/api/v1/comments', require('./routes/comments'));
app.use('/api/v1/share', require('./routes/share'));

// 健康检查
app.get('/health', (req, res) => {
  res.json({ success: true, message: 'Server is running' });
});

// 404处理
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'API endpoint not found'
  });
});

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    success: false,
    message: '服务器内部错误'
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
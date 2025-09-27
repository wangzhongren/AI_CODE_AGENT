const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// 确保数据库目录存在
const fs = require('fs');
const dbDir = path.join(__dirname, '../data');
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

const dbPath = path.join(dbDir, 'app.db');
const db = new sqlite3.Database(dbPath);

// 启用外键约束
db.run('PRAGMA foreign_keys = ON;');

// 创建表
db.serialize(() => {
  // 内容表
  db.run(`CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // 评论表
  db.run(`CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    author_name TEXT NOT NULL,
    content TEXT NOT NULL CHECK(length(content) <= 500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
  )`);

  // 分享令牌表
  db.run(`CREATE TABLE IF NOT EXISTS share_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL UNIQUE,
    token TEXT NOT NULL UNIQUE,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
  )`);
});

module.exports = db;
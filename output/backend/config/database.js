const mysql = require('mysql2/promise');

// Database configuration
const dbConfig = {
  host: process.env.DB_HOST || '106.14.112.246',
  user: process.env.DB_USER || 'root',
  port:9876,
  password: process.env.DB_PASSWORD || 'Th_mysql_123456',
  database: process.env.DB_NAME || 'knowledge_base',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

// Create connection pool
const pool = mysql.createPool(dbConfig);

module.exports = pool;
const db = require('../models/db');
const crypto = require('crypto');

const generateShareToken = (req, res) => {
  const { item_id } = req.body;
  
  // 验证内容是否存在
  const checkItemQuery = 'SELECT id FROM items WHERE id = ?';
  db.get(checkItemQuery, [item_id], (err, row) => {
    if (err) {
      console.error('Error checking item existence:', err);
      return res.status(500).json({
        success: false,
        message: '服务器内部错误'
      });
    }
    
    if (!row) {
      return res.status(404).json({
        success: false,
        message: '指定的内容不存在'
      });
    }
    
    // 生成高强度随机token (32位十六进制 = 128位)
    const token = crypto.randomBytes(16).toString('hex');
    
    // 设置7天后过期
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 7);
    
    // 插入或替换分享令牌（每个内容只能有一个有效token）
    const insertQuery = `
      INSERT OR REPLACE INTO share_tokens (item_id, token, expires_at) 
      VALUES (?, ?, ?)
    `;
    
    db.run(insertQuery, [item_id, token, expiresAt.toISOString()], function(err) {
      if (err) {
        console.error('Error creating share token:', err);
        return res.status(500).json({
          success: false,
          message: '服务器内部错误'
        });
      }
      
      res.json({
        success: true,
        data: { token },
        message: '生成分享链接成功'
      });
    });
  });
};

const getSharedItem = (req, res) => {
  const { token } = req.params;
  
  if (!token) {
    return res.status(400).json({
      success: false,
      message: '无效的分享令牌'
    });
  }
  
  // 查询有效的分享令牌（未过期）
  const query = `
    SELECT st.item_id, i.title, i.content, i.created_at, i.updated_at
    FROM share_tokens st
    JOIN items i ON st.item_id = i.id
    WHERE st.token = ? 
    AND (st.expires_at IS NULL OR st.expires_at > datetime('now'))
  `;
  
  db.get(query, [token], (err, row) => {
    if (err) {
      console.error('Error fetching shared item:', err);
      return res.status(500).json({
        success: false,
        message: '服务器内部错误'
      });
    }
    
    if (!row) {
      return res.status(404).json({
        success: false,
        message: '分享链接无效或已过期'
      });
    }
    
    res.json({
      success: true,
      data: row,
      message: '获取分享内容成功'
    });
  });
};

module.exports = {
  generateShareToken,
  getSharedItem
};
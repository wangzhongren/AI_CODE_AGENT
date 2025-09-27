const db = require('../models/db');

const getComments = (req, res) => {
  const { item_id } = req.query;
  
  if (!item_id || isNaN(item_id) || parseInt(item_id) <= 0) {
    return res.status(400).json({
      success: false,
      message: '需要提供有效的内容ID (item_id)'
    });
  }
  
  const query = `
    SELECT id, item_id, author_name, content, created_at 
    FROM comments 
    WHERE item_id = ?
    ORDER BY created_at DESC
  `;
  
  db.all(query, [item_id], (err, rows) => {
    if (err) {
      console.error('Error fetching comments:', err);
      return res.status(500).json({
        success: false,
        message: '服务器内部错误'
      });
    }
    
    res.json({
      success: true,
      data: rows,
      message: '获取评论列表成功'
    });
  });
};

const createComment = (req, res) => {
  const { item_id, author_name, content } = req.body;
  
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
    
    const insertQuery = `
      INSERT INTO comments (item_id, author_name, content) 
      VALUES (?, ?, ?)
    `;
    
    db.run(insertQuery, [item_id, author_name.trim(), content.trim()], function(err) {
      if (err) {
        console.error('Error creating comment:', err);
        return res.status(500).json({
          success: false,
          message: '服务器内部错误'
        });
      }
      
      const newComment = {
        id: this.lastID,
        item_id,
        author_name: author_name.trim(),
        content: content.trim(),
        created_at: new Date().toISOString()
      };
      
      res.status(201).json({
        success: true,
        data: newComment,
        message: '创建评论成功'
      });
    });
  });
};

module.exports = {
  getComments,
  createComment
};
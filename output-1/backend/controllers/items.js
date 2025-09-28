const db = require('../models/db');

const getItems = (req, res) => {
  const { page, limit } = req.pagination;
  const offset = (page - 1) * limit;
  
  const countQuery = 'SELECT COUNT(*) as total FROM items';
  const itemsQuery = `
    SELECT id, title, content, created_at, updated_at 
    FROM items 
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
  `;
  
  db.get(countQuery, (err, countRow) => {
    if (err) {
      console.error('Error counting items:', err);
      return res.status(500).json({
        success: false,
        message: '服务器内部错误'
      });
    }
    
    const total = countRow.total;
    const totalPages = Math.ceil(total / limit);
    
    db.all(itemsQuery, [limit, offset], (err, rows) => {
      if (err) {
        console.error('Error fetching items:', err);
        return res.status(500).json({
          success: false,
          message: '服务器内部错误'
        });
      }
      
      res.json({
        success: true,
        data: {
          items: rows,
          pagination: {
            page,
            limit,
            total,
            totalPages
          }
        },
        message: '获取内容列表成功'
      });
    });
  });
};

const getItemById = (req, res) => {
  const { id } = req.params;
  
  if (!id || isNaN(id) || parseInt(id) <= 0) {
    return res.status(400).json({
      success: false,
      message: '无效的内容ID'
    });
  }
  
  const query = `
    SELECT id, title, content, created_at, updated_at 
    FROM items 
    WHERE id = ?
  `;
  
  db.get(query, [id], (err, row) => {
    if (err) {
      console.error('Error fetching item:', err);
      return res.status(500).json({
        success: false,
        message: '服务器内部错误'
      });
    }
    
    if (!row) {
      return res.status(404).json({
        success: false,
        message: '内容不存在'
      });
    }
    
    res.json({
      success: true,
      data: row,
      message: '获取内容详情成功'
    });
  });
};

const createItem = (req, res) => {
  const { title, content } = req.body;
  
  const query = `
    INSERT INTO items (title, content) 
    VALUES (?, ?)
  `;
  
  db.run(query, [title.trim(), content.trim()], function(err) {
    if (err) {
      console.error('Error creating item:', err);
      return res.status(500).json({
        success: false,
        message: '服务器内部错误'
      });
    }
    
    const newItem = {
      id: this.lastID,
      title: title.trim(),
      content: content.trim(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    res.status(201).json({
      success: true,
      data: newItem,
      message: '创建内容成功'
    });
  });
};

module.exports = {
  getItems,
  getItemById,
  createItem
};
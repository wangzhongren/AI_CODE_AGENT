const pool = require('../config/database');

class Article {
  // Get all articles with pagination
  static async getAll(page = 1, limit = 10) {
    const offset = (page - 1) * limit;
    
    // Ensure we have proper integer values
    const limitVal = Number(limit);
    const offsetVal = Number(offset);
    
    if (isNaN(limitVal) || isNaN(offsetVal) || limitVal <= 0 || offsetVal < 0) {
      throw new Error('Invalid pagination parameters');
    }
    
    const [rows] = await pool.execute(
      'SELECT id, title, content, created_at FROM articles ORDER BY created_at DESC LIMIT ' + 
      pool.escape(limitVal) + ' OFFSET ' + pool.escape(offsetVal)
    );
    
    const [countResult] = await pool.execute('SELECT COUNT(*) as total FROM articles');
    const total = countResult[0].total;
    
    return {
      articles: rows,
      pagination: {
        current_page: Number(page),
        total_pages: Math.ceil(total / limitVal),
        total_items: total
      }
    };
  }

  // Get article by ID
  static async getById(id) {
    const articleId = Number(id);
    if (isNaN(articleId) || articleId <= 0) {
      return null;
    }
    
    const [rows] = await pool.execute(
      'SELECT id, title, content, created_at, updated_at FROM articles WHERE id = ?',
      [articleId]
    );
    return rows[0] || null;
  }

  // Create new article
  static async create(title, content) {
    const [result] = await pool.execute(
      'INSERT INTO articles (title, content) VALUES (?, ?)',
      [title, content]
    );
    return result.insertId;
  }

  // Update article by ID
  static async update(id, title, content) {
    const articleId = Number(id);
    if (isNaN(articleId) || articleId <= 0) {
      return false;
    }
    
    const [result] = await pool.execute(
      'UPDATE articles SET title = ?, content = ? WHERE id = ?',
      [title, content, articleId]
    );
    return result.affectedRows > 0;
  }

  // Delete article by ID
  static async delete(id) {
    const articleId = Number(id);
    if (isNaN(articleId) || articleId <= 0) {
      return false;
    }
    
    const [result] = await pool.execute(
      'DELETE FROM articles WHERE id = ?',
      [articleId]
    );
    return result.affectedRows > 0;
  }
}

module.exports = Article;
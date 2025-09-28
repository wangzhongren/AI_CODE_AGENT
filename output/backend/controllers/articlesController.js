const Article = require('../models/Article');

// Get articles list with pagination
const getArticles = async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    
    if (page < 1 || limit < 1) {
      return res.status(400).json({
        success: false,
        message: 'Page and limit must be positive integers'
      });
    }

    const result = await Article.getAll(page, limit);
    
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('Error fetching articles:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

// Get article by ID
const getArticleById = async (req, res) => {
  try {
    const { id } = req.params;
    const articleId = parseInt(id);
    
    if (isNaN(articleId) || articleId <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Invalid article ID'
      });
    }

    const article = await Article.getById(articleId);
    
    if (!article) {
      return res.status(404).json({
        success: false,
        message: 'Article not found'
      });
    }

    res.json({
      success: true,
      data: article
    });
  } catch (error) {
    console.error('Error fetching article:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

// Create new article
const createArticle = async (req, res) => {
  try {
    const { title, content } = req.body;
    
    if (!title || !content) {
      return res.status(400).json({
        success: false,
        message: 'Title and content are required'
      });
    }

    const articleId = await Article.create(title, content);
    const newArticle = await Article.getById(articleId);
    
    res.status(201).json({
      success: true,
      data: newArticle
    });
  } catch (error) {
    console.error('Error creating article:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

// Update existing article
const updateArticle = async (req, res) => {
  try {
    const { id } = req.params;
    const articleId = parseInt(id);
    const { title, content } = req.body;
    
    if (isNaN(articleId) || articleId <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Invalid article ID'
      });
    }
    
    if (!title || !content) {
      return res.status(400).json({
        success: false,
        message: 'Title and content are required'
      });
    }

    const exists = await Article.getById(articleId);
    if (!exists) {
      return res.status(404).json({
        success: false,
        message: 'Article not found'
      });
    }

    const updated = await Article.update(articleId, title, content);
    if (!updated) {
      return res.status(500).json({
        success: false,
        message: 'Failed to update article'
      });
    }

    const updatedArticle = await Article.getById(articleId);
    res.json({
      success: true,
      data: updatedArticle
    });
  } catch (error) {
    console.error('Error updating article:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

// Delete article by ID
const deleteArticle = async (req, res) => {
  try {
    const { id } = req.params;
    const articleId = parseInt(id);
    
    if (isNaN(articleId) || articleId <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Invalid article ID'
      });
    }

    const exists = await Article.getById(articleId);
    if (!exists) {
      return res.status(404).json({
        success: false,
        message: 'Article not found'
      });
    }

    const deleted = await Article.delete(articleId);
    if (!deleted) {
      return res.status(500).json({
        success: false,
        message: 'Failed to delete article'
      });
    }

    res.json({
      success: true,
      message: 'Article deleted successfully'
    });
  } catch (error) {
    console.error('Error deleting article:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

module.exports = {
  getArticles,
  getArticleById,
  createArticle,
  updateArticle,
  deleteArticle
};
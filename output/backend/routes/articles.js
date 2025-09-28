const express = require('express');
const router = express.Router();
const authenticateToken = require('../middleware/auth');
const {
  getArticles,
  getArticleById,
  createArticle,
  updateArticle,
  deleteArticle
} = require('../controllers/articlesController');

// Apply authentication middleware to all routes
router.use(authenticateToken);

// GET /api/v1/articles - Get articles list
router.get('/', getArticles);

// GET /api/v1/articles/:id - Get article by ID
router.get('/:id', getArticleById);

// POST /api/v1/articles - Create new article
router.post('/', createArticle);

// PUT /api/v1/articles/:id - Update existing article
router.put('/:id', updateArticle);

// DELETE /api/v1/articles/:id - Delete article
router.delete('/:id', deleteArticle);

module.exports = router;
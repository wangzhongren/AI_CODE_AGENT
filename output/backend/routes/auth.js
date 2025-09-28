const express = require('express');
const router = express.Router();
const { register, login, getCurrentUser } = require('../controllers/authController');
const authenticateToken = require('../middleware/auth');

// Public routes (no authentication required)
router.post('/register', register);
router.post('/login', login);

// Protected route (requires authentication)
router.get('/me', authenticateToken, getCurrentUser);

module.exports = router;
const express = require('express');
const router = express.Router();
const { getComments, createComment } = require('../controllers/comments');
const { validateCommentCreate } = require('../middleware/validation');
const { commentRateLimit } = require('../middleware/rateLimit');

router.get('/', getComments);
router.post('/', validateCommentCreate, commentRateLimit, createComment);

module.exports = router;
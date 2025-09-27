const express = require('express');
const router = express.Router();
const { generateShareToken, getSharedItem } = require('../controllers/share');
const { validateShareCreate } = require('../middleware/validation');

router.post('/', validateShareCreate, generateShareToken);
router.get('/:token', getSharedItem);

module.exports = router;
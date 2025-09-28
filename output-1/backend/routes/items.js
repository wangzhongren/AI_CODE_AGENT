const express = require('express');
const router = express.Router();
const { getItems, getItemById, createItem } = require('../controllers/items');
const { validateItemCreate, validatePagination } = require('../middleware/validation');

router.get('/', validatePagination, getItems);
router.get('/:id', getItemById);
router.post('/', validateItemCreate, createItem);

module.exports = router;
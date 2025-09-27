const validateItemCreate = (req, res, next) => {
  const { title, content } = req.body;
  
  if (!title || typeof title !== 'string' || title.trim().length === 0) {
    return res.status(400).json({
      success: false,
      message: '标题不能为空'
    });
  }
  
  if (!content || typeof content !== 'string' || content.trim().length === 0) {
    return res.status(400).json({
      success: false,
      message: '内容不能为空'
    });
  }
  
  if (title.length > 255) {
    return res.status(400).json({
      success: false,
      message: '标题长度不能超过255个字符'
    });
  }
  
  next();
};

const validateCommentCreate = (req, res, next) => {
  const { item_id, author_name, content } = req.body;
  
  if (!item_id || typeof item_id !== 'number' || item_id <= 0) {
    return res.status(400).json({
      success: false,
      message: '无效的内容ID'
    });
  }
  
  if (!author_name || typeof author_name !== 'string' || author_name.trim().length === 0) {
    return res.status(400).json({
      success: false,
      message: '作者名称不能为空'
    });
  }
  
  if (!content || typeof content !== 'string' || content.trim().length === 0) {
    return res.status(400).json({
      success: false,
      message: '评论内容不能为空'
    });
  }
  
  if (content.length > 500) {
    return res.status(400).json({
      success: false,
      message: '评论内容长度不能超过500个字符'
    });
  }
  
  if (author_name.length > 100) {
    return res.status(400).json({
      success: false,
      message: '作者名称长度不能超过100个字符'
    });
  }
  
  next();
};

const validateShareCreate = (req, res, next) => {
  const { item_id } = req.body;
  
  if (!item_id || typeof item_id !== 'number' || item_id <= 0) {
    return res.status(400).json({
      success: false,
      message: '无效的内容ID'
    });
  }
  
  next();
};

const validatePagination = (req, res, next) => {
  let { page = 1, limit = 10 } = req.query;
  
  page = parseInt(page);
  limit = parseInt(limit);
  
  if (isNaN(page) || page < 1) {
    page = 1;
  }
  
  if (isNaN(limit) || limit < 1 || limit > 50) {
    limit = 10;
  }
  
  req.pagination = { page, limit };
  next();
};

module.exports = {
  validateItemCreate,
  validateCommentCreate,
  validateShareCreate,
  validatePagination
};
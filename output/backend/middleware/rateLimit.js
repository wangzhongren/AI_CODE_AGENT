const rateLimitStore = new Map();

const commentRateLimit = (req, res, next) => {
  const ip = req.ip || req.connection.remoteAddress;
  const now = Date.now();
  const windowMs = 10000; // 10秒
  const maxRequests = 1;
  
  if (!rateLimitStore.has(ip)) {
    rateLimitStore.set(ip, { count: 0, resetTime: now + windowMs });
  }
  
  const ipData = rateLimitStore.get(ip);
  
  if (now > ipData.resetTime) {
    // 重置计数器
    ipData.count = 0;
    ipData.resetTime = now + windowMs;
  }
  
  if (ipData.count >= maxRequests) {
    return res.status(429).json({
      success: false,
      message: '请求过于频繁，请稍后再试'
    });
  }
  
  ipData.count++;
  rateLimitStore.set(ip, ipData);
  
  next();
};

// 定期清理过期的IP记录（可选）
setInterval(() => {
  const now = Date.now();
  for (const [ip, data] of rateLimitStore.entries()) {
    if (now > data.resetTime + 60000) { // 1分钟后清理
      rateLimitStore.delete(ip);
    }
  }
}, 60000);

module.exports = { commentRateLimit };
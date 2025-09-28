const API_BASE = '/api/v1'

export const api = {
  // 获取内容列表
  getItems(page = 1, limit = 10) {
    return fetch(`${API_BASE}/items?page=${page}&limit=${limit}`)
      .then(res => res.json())
  },

  // 获取内容详情
  getItemById(id) {
    return fetch(`${API_BASE}/items/${id}`)
      .then(res => res.json())
  },

  // 获取评论列表
  getComments(itemId, page = 1, limit = 10) {
    return fetch(`${API_BASE}/comments?item_id=${itemId}&page=${page}&limit=${limit}`)
      .then(res => res.json())
  },

  // 提交评论
  postComment({ item_id, author_name, content }) {
    return fetch(`${API_BASE}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id, author_name, content })
    }).then(res => res.json())
  },

  // 通过分享 token 获取内容
  getItemByShareToken(token) {
    return fetch(`${API_BASE}/shared/${token}`)
      .then(res => res.json())
  }
}
<template>
  <div class="article-detail" v-if="article">
    <div class="detail-header">
      <h1>{{ article.title }}</h1>
      <div class="detail-actions">
        <button @click="goBack" class="btn-secondary">返回列表</button>
        <router-link :to="`/edit/${article.id}`" class="btn-primary">
          编辑
        </router-link>
        <button @click="handleDelete" class="btn-danger" :disabled="deleting">
          {{ deleting ? '删除中...' : '删除' }}
        </button>
      </div>
    </div>
    <div class="detail-meta">
      创建于 {{ formatDate(article.created_at) }}
      <span v-if="article.updated_at !== article.created_at">
        • 更新于 {{ formatDate(article.updated_at) }}
      </span>
    </div>
    <div class="content" v-html="renderedContent"></div>
  </div>
  <div v-else-if="loading" class="loading">加载中...</div>
  <div v-else-if="error" class="error">{{ error }}</div>
</template>

<script>
import { articleApi } from '@/api/api.js'
import { marked } from 'marked'

export default {
  name: 'ArticleDetail',
  props: ['id'],
  data() {
    return {
      article: null,
      loading: false,
      error: null,
      deleting: false
    }
  },
  computed: {
    renderedContent() {
      if (!this.article) return ''
      return marked(this.article.content)
    }
  },
  created() {
    this.fetchArticle()
  },
  methods: {
    async fetchArticle() {
      this.loading = true
      this.error = null
      try {
        const response = await articleApi.getArticle(this.id)
        if (response.data.success) {
          this.article = response.data.data
        } else {
          throw new Error('获取文章失败')
        }
      } catch (err) {
        console.error('获取文章详情出错:', err)
        this.error = '无法加载文章内容'
      } finally {
        this.loading = false
      }
    },
    goBack() {
      this.$router.go(-1)
    },
    async handleDelete() {
      if (!confirm('确定要删除这篇文章吗？此操作不可恢复。')) {
        return
      }
      
      this.deleting = true
      try {
        const response = await articleApi.deleteArticle(this.id)
        if (response.data.success) {
          // 删除成功，返回文章列表
          this.$router.push('/')
        } else {
          throw new Error('删除失败')
        }
      } catch (err) {
        console.error('删除文章出错:', err)
        alert('删除失败，请稍后重试')
      } finally {
        this.deleting = false
      }
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.article-detail {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.detail-header h1 {
  margin: 0;
  font-size: 24px;
  color: #2c3e50;
  max-width: 70%;
}

.detail-actions {
  display: flex;
  gap: 10px;
}

.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.btn-secondary {
  background-color: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background-color: #d5dbdb;
}

.btn-danger {
  background-color: #e74c3c;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c0392b;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.detail-meta {
  font-size: 13px;
  color: #888;
  margin-bottom: 20px;
}

.content {
  line-height: 1.6;
  color: #333;
}

.content h1,
.content h2,
.content h3 {
  margin-top: 24px;
  margin-bottom: 16px;
  color: #2c3e50;
}

.content p {
  margin: 12px 0;
}

.content ul,
.content ol {
  padding-left: 20px;
  margin: 12px 0;
}

.content code {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.content pre {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.content blockquote {
  border-left: 4px solid #3498db;
  padding-left: 16px;
  margin: 16px 0;
  color: #555;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #e74c3c;
}
</style>
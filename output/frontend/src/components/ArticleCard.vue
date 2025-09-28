<template>
  <article class="article-card">
    <h2 class="article-title">
      <router-link :to="`/articles/${article.id}`">
        {{ article.title }}
      </router-link>
    </h2>
    <p class="article-summary">
      {{ getSummary(article.content) }}
    </p>
    <div class="article-meta">
      创建于 {{ formatDate(article.created_at) }}
    </div>
  </article>
</template>

<script>
export default {
  name: 'ArticleCard',
  props: {
    article: {
      type: Object,
      required: true
    }
  },
  methods: {
    getSummary(content) {
      // 简单截取前100字符作为摘要，移除Markdown符号
      const plainText = content.replace(/[#*_`~\[\]()>]/g, ' ')
      return plainText.substring(0, 100) + (plainText.length > 100 ? '...' : '')
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.article-card {
  padding: 20px;
  margin-bottom: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s;
}

.article-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.article-title {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
}

.article-title a {
  color: inherit;
  text-decoration: none;
}

.article-title a:hover {
  color: #3498db;
}

.article-summary {
  margin: 0 0 12px 0;
  color: #555;
  line-height: 1.5;
}

.article-meta {
  font-size: 13px;
  color: #888;
}
</style>
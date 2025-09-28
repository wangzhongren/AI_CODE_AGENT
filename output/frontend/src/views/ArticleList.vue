<template>
  <div class="article-list">
    <h2>文章列表</h2>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <ArticleCard
        v-for="article in articles"
        :key="article.id"
        :article="article"
      />
      <Pagination
        v-if="pagination.total_pages > 1"
        :current-page="pagination.current_page"
        :total-pages="pagination.total_pages"
        @change-page="handlePageChange"
      />
    </div>
  </div>
</template>

<script>
import { articleApi } from '@/api/api.js'
import ArticleCard from '@/components/ArticleCard.vue'
import Pagination from '@/components/Pagination.vue'

export default {
  name: 'ArticleList',
  components: {
    ArticleCard,
    Pagination
  },
  data() {
    return {
      articles: [],
      pagination: {
        current_page: 1,
        total_pages: 1,
        total_items: 0
      },
      loading: false,
      error: null
    }
  },
  created() {
    this.fetchArticles()
  },
  methods: {
    async fetchArticles(page = 1) {
      this.loading = true
      this.error = null
      try {
        const response = await articleApi.getArticles(page, 10)
        if (response.data.success) {
          this.articles = response.data.data.articles
          this.pagination = response.data.data.pagination
        } else {
          throw new Error('获取文章列表失败')
        }
      } catch (err) {
        console.error('获取文章列表出错:', err)
        this.error = '无法加载文章列表，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    handlePageChange(page) {
      this.fetchArticles(page)
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}
</script>

<style scoped>
.article-list h2 {
  margin-bottom: 24px;
  font-size: 20px;
  color: #2c3e50;
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
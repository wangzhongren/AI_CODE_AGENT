<template>
  <div class="share-container">
    <div class="back-link" @click="$router.push('/')">
      ← 返回首页
    </div>

    <article v-if="item" class="share-content">
      <header class="share-header">
        <h1>{{ item.title }}</h1>
        <div class="meta">
          <span>发布时间：{{ formatDate(item.created_at) }}</span>
        </div>
        <p class="share-tip">此为公开分享内容，仅展示，不支持评论</p>
      </header>

      <div class="content-body" v-html="item.content"></div>
    </article>

    <div v-else-if="loading" class="loading">加载中...</div>
    <div v-else class="error">分享链接无效或已过期</div>
  </div>
</template>

<script>
import { api } from '@/api/api'

export default {
  name: 'ShareView',
  data() {
    return {
      item: null,
      loading: true
    }
  },
  async mounted() {
    await this.loadSharedItem()
  },
  methods: {
    async loadSharedItem() {
      this.loading = true
      try {
        const response = await api.getItemByShareToken(this.$route.params.token)
        if (response.success) {
          this.item = response.data
        } else {
          console.error('获取分享内容失败:', response.message)
        }
      } catch (error) {
        console.error('加载分享内容出错:', error)
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.share-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.back-link {
  color: #4a6cf7;
  cursor: pointer;
  margin-bottom: 24px;
  display: inline-block;
  font-size: 14px;
}

.back-link:hover {
  text-decoration: underline;
}

.share-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 32px;
}

.share-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 16px;
  line-height: 1.3;
}

.meta {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 16px;
}

.share-tip {
  background: #f0f9ff;
  color: #0c4a6e;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 24px;
  border: 1px solid #bae6fd;
}

.content-body {
  line-height: 1.7;
  color: #374151;
  font-size: 16px;
}

.content-body :deep(p) {
  margin-bottom: 16px;
}

.content-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 12px 0;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}
</style>
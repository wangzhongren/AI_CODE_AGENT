<template>
  <div class="detail-container">
    <div class="back-link" @click="$router.back()">
      ← 返回列表
    </div>

    <article v-if="item" class="detail-content">
      <header class="detail-header">
        <h1>{{ item.title }}</h1>
        <div class="meta">
          <span>发布时间：{{ formatDate(item.created_at) }}</span>
          <span v-if="item.updated_at !== item.created_at">更新时间：{{ formatDate(item.updated_at) }}</span>
        </div>
      </header>

      <div class="content-body" v-html="item.content"></div>

      <div class="action-bar">
        <ShareButton :item-id="item.id" />
      </div>
    </article>

    <div v-else-if="loading" class="loading">加载中...</div>
    <div v-else class="error">内容不存在</div>

    <CommentList :comments="comments" />
    <CommentForm 
      :item-id="Number($route.params.id)" 
      @comment-submitted="handleNewComment"
      @reset-list="loadComments"
    />
  </div>
</template>

<script>
import { api } from '@/api/api'
import ShareButton from '@/components/ShareButton.vue'
import CommentList from '@/components/CommentList.vue'
import CommentForm from '@/components/CommentForm.vue'

export default {
  name: 'Detail',
  components: {
    ShareButton,
    CommentList,
    CommentForm
  },
  data() {
    return {
      item: null,
      comments: [],
      loading: true
    }
  },
  async mounted() {
    await this.loadItem()
    await this.loadComments()
  },
  methods: {
    async loadItem() {
      this.loading = true
      try {
        const response = await api.getItemById(this.$route.params.id)
        if (response.success) {
          this.item = response.data
        } else {
          console.error('获取详情失败:', response.message)
        }
      } catch (error) {
        console.error('加载详情出错:', error)
      } finally {
        this.loading = false
      }
    },
    async loadComments() {
      try {
        const response = await api.getComments(this.$route.params.id)
        if (response.success) {
          this.comments = response.data
        } else {
          console.error('获取评论失败:', response.message)
        }
      } catch (error) {
        console.error('加载评论出错:', error)
      }
    },
    handleNewComment(comment) {
      this.comments.unshift(comment)
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.detail-container {
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

.detail-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
}

.detail-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 16px;
  line-height: 1.3;
}

.meta {
  display: flex;
  gap: 24px;
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 24px;
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

.action-bar {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}
</style>
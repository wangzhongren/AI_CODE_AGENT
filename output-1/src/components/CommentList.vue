<template>
  <div class="comment-list">
    <h3>评论 ({{ comments.length }})</h3>
    <div v-if="comments.length === 0" class="no-comments">
      暂无评论，快来抢沙发吧！
    </div>
    <div v-else class="comments">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-header">
          <span class="author">{{ comment.author_name }}</span>
          <span class="time">{{ formatDate(comment.created_at) }}</span>
        </div>
        <div class="comment-content">{{ comment.content }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CommentList',
  props: {
    comments: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  methods: {
    formatDate(dateString) {
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      const seconds = Math.floor(diff / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)
      const days = Math.floor(hours / 24)

      if (days > 0) return `${days}天前`
      if (hours > 0) return `${hours}小时前`
      if (minutes > 0) return `${minutes}分钟前`
      return '刚刚'
    }
  }
}
</script>

<style scoped>
.comment-list {
  margin-top: 24px;
}

h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1f2937;
}

.no-comments {
  text-align: center;
  color: #6b7280;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
}

.comments {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  background: #f9fafb;
  padding: 16px;
  border-radius: 10px;
  border-left: 3px solid #4a6cf7;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.author {
  font-weight: 600;
  color: #1f2937;
}

.time {
  color: #6b7280;
}

.comment-content {
  line-height: 1.5;
  color: #374151;
  white-space: pre-wrap;
}
</style>
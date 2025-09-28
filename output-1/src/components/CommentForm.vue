<template>
  <form class="comment-form" @submit.prevent="handleSubmit">
    <div class="form-group">
      <label for="author">昵称：</label>
      <input
        id="author"
        v-model="authorName"
        type="text"
        maxlength="100"
        required
        placeholder="请输入您的昵称"
      />
    </div>
    <div class="form-group">
      <label for="content">评论：</label>
      <textarea
        id="content"
        v-model="content"
        maxlength="500"
        required
        placeholder="写下您的想法（最多500字）"
      ></textarea>
      <div class="char-count">{{ content.length }}/500</div>
    </div>
    <button 
      type="submit" 
      :disabled="isSubmitting || !canSubmit"
      class="submit-btn"
    >
      {{ isSubmitting ? '提交中...' : '发表评论' }}
    </button>
  </form>
</template>

<script>
import { api } from '@/api/api'

export default {
  name: 'CommentForm',
  props: {
    itemId: { type: Number, required: true }
  },
  data() {
    return {
      authorName: '',
      content: '',
      isSubmitting: false,
      lastSubmitTime: 0
    }
  },
  computed: {
    canSubmit() {
      const now = Date.now()
      return (now - this.lastSubmitTime) > 3000 // 3秒防重
    }
  },
  methods: {
    async handleSubmit() {
      if (!this.canSubmit) return

      this.isSubmitting = true
      this.lastSubmitTime = Date.now()

      try {
        const result = await api.postComment({
          item_id: this.itemId,
          author_name: this.authorName.trim(),
          content: this.content.trim()
        })

        if (result.success) {
          this.$emit('comment-submitted', result.data)
          this.authorName = ''
          this.content = ''
          this.$emit('reset-list') // 通知父组件刷新评论
        } else {
          alert(result.message || '评论提交失败')
        }
      } catch (error) {
        console.error('提交评论出错:', error)
        alert('网络错误，请稍后重试')
      } finally {
        this.isSubmitting = false
      }
    }
  }
}
</script>

<style scoped>
.comment-form {
  background: #f9fafb;
  padding: 20px;
  border-radius: 12px;
  margin-top: 24px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #374151;
}

input,
textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 0 2px rgba(74, 108, 247, 0.2);
}

textarea {
  min-height: 100px;
  resize: vertical;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.submit-btn {
  background: #10b981;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #0da271;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
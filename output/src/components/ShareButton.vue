<template>
  <button 
    class="share-button"
    @click="handleShare"
    :disabled="loading"
  >
    {{ loading ? '生成中...' : '公开分享' }}
  </button>
</template>

<script>
import { api } from '@/api/api'

export default {
  name: 'ShareButton',
  props: {
    itemId: { type: Number, required: true }
  },
  data() {
    return {
      loading: false
    }
  },
  methods: {
    async handleShare() {
      this.loading = true
      try {
        const response = await fetch('/api/v1/share', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ item_id: this.itemId })
        })
        const data = await response.json()
        if (data.success && data.data?.token) {
          const shareUrl = `${window.location.origin}/share/${data.data.token}`
          navigator.clipboard.writeText(shareUrl)
            .then(() => alert('分享链接已复制到剪贴板！'))
            .catch(() => {
              prompt('复制以下链接：', shareUrl)
            })
        } else {
          alert('生成分享链接失败')
        }
      } catch (error) {
        console.error('分享失败:', error)
        alert('网络错误，请重试')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.share-button {
  background: #4a6cf7;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.share-button:hover:not(:disabled) {
  background: #3a5bf5;
}

.share-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
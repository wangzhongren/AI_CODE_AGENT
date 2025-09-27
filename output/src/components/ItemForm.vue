<template>
  <div class="item-form-overlay" @click.self="closeForm">
    <div class="item-form-container">
      <div class="form-header">
        <h2>新增灵感</h2>
        <button class="close-btn" @click="closeForm">&times;</button>
      </div>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="title">标题：</label>
          <input
            id="title"
            v-model="title"
            type="text"
            maxlength="255"
            required
            placeholder="请输入灵感标题"
          />
        </div>
        
        <div class="form-group">
          <label for="content">内容：</label>
          <textarea
            id="content"
            v-model="content"
            required
            placeholder="写下您的灵感..."
          ></textarea>
        </div>
        
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="closeForm">取消</button>
          <button 
            type="submit" 
            :disabled="isSubmitting || !canSubmit"
            class="submit-btn"
          >
            {{ isSubmitting ? '提交中...' : '保存灵感' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/api'

export default {
  name: 'ItemForm',
  emits: ['item-created', 'close'],
  data() {
    return {
      title: '',
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
    closeForm() {
      this.$emit('close')
    },
    async handleSubmit() {
      if (!this.canSubmit) return

      this.isSubmitting = true
      this.lastSubmitTime = Date.now()

      try {
        const response = await fetch('/api/v1/items', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            title: this.title.trim(), 
            content: this.content.trim() 
          })
        })
        const result = await response.json()

        if (result.success) {
          this.$emit('item-created', result.data)
          this.title = ''
          this.content = ''
          this.closeForm()
        } else {
          alert(result.message || '保存失败，请重试')
        }
      } catch (error) {
        console.error('提交灵感出错:', error)
        alert('网络错误，请稍后重试')
      } finally {
        this.isSubmitting = false
      }
    }
  }
}
</script>

<style scoped>
.item-form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.item-form-container {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: auto;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.form-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.form-group {
  padding: 0 24px;
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
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
  min-height: 200px;
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 24px;
}

.cancel-btn,
.submit-btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.cancel-btn {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.cancel-btn:hover {
  background: #e5e7eb;
}

.submit-btn {
  background: #4a6cf7;
  color: white;
  border: none;
}

.submit-btn:hover:not(:disabled) {
  background: #3a5bf5;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
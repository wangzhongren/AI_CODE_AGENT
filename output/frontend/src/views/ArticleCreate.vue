<template>
  <div class="article-form">
    <h2>{{ isEditing ? '编辑文章' : '新建文章' }}</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="title">标题</label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          required
          placeholder="请输入文章标题"
          class="form-input"
        />
      </div>
      <div class="form-group">
        <label for="content">内容 (Markdown)</label>
        <textarea
          id="content"
          v-model="form.content"
          required
          placeholder="使用 Markdown 编写内容..."
          class="form-textarea"
        ></textarea>
      </div>
      <div class="form-actions">
        <button type="button" @click="goBack" class="btn-secondary">
          取消
        </button>
        <button type="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : (isEditing ? '更新' : '创建') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { articleApi } from '@/api/api.js'

export default {
  name: 'ArticleCreate',
  props: ['id'],
  data() {
    return {
      form: {
        title: '',
        content: ''
      },
      submitting: false,
      isEditing: !!this.id
    }
  },
  async created() {
    if (this.isEditing) {
      await this.loadArticle()
    }
  },
  methods: {
    async loadArticle() {
      try {
        const response = await articleApi.getArticle(this.id)
        if (response.data.success) {
          this.form.title = response.data.data.title
          this.form.content = response.data.data.content
        }
      } catch (err) {
        console.error('加载文章失败:', err)
        alert('无法加载文章内容')
        this.goBack()
      }
    },
    async handleSubmit() {
      if (!this.form.title.trim() || !this.form.content.trim()) {
        alert('标题和内容不能为空')
        return
      }

      this.submitting = true
      try {
        let response
        if (this.isEditing) {
          response = await articleApi.updateArticle(this.id, this.form)
        } else {
          response = await articleApi.createArticle(this.form)
        }

        if (response.data.success) {
          const articleId = response.data.data.id
          // 使用 replace 而不是 push，避免返回时回到新建页面
          this.$router.replace(`/articles/${articleId}`)
        } else {
          throw new Error('操作失败')
        }
      } catch (err) {
        console.error('提交失败:', err)
        alert('提交失败，请稍后重试')
      } finally {
        this.submitting = false
      }
    },
    goBack() {
      this.$router.go(-1)
    }
  }
}
</script>

<style scoped>
.article-form {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.article-form h2 {
  margin-bottom: 24px;
  font-size: 20px;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #2c3e50;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-textarea {
  width: 100%;
  height: 300px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  resize: vertical;
}

.form-textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.btn-primary,
.btn-secondary {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background-color: #d5dbdb;
}
</style>
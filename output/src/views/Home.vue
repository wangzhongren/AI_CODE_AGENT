<template>
  <div class="home-container">
    <header class="page-header">
      <h1>内容中心</h1>
      <p>探索精彩内容，参与互动讨论</p>
      <button class="add-item-btn" @click="showForm = true">+ 新增灵感</button>
    </header>

    <main class="content-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-state">
        暂无内容，<button class="add-first-btn" @click="showForm = true">立即添加您的第一个灵感</button>
      </div>
      <div v-else class="items-grid">
        <div
          v-for="item in items"
          :key="item.id"
          class="item-card"
          @click="goToDetail(item.id)"
        >
          <h2 class="item-title">{{ item.title }}</h2>
          <p class="item-preview">{{ getPreview(item.content) }}</p>
          <div class="item-meta">
            <span>{{ formatDate(item.created_at) }}</span>
          </div>
        </div>
      </div>

      <div v-if="!loading && items.length > 0" class="pagination">
        <button
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
          class="page-btn"
        >
          上一页
        </button>
        <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
        <button
          :disabled="currentPage >= totalPages"
          @click="changePage(currentPage + 1)"
          class="page-btn"
        >
          下一页
        </button>
      </div>
    </main>

    <ItemForm 
      v-if="showForm"
      @item-created="handleNewItem"
      @close="showForm = false"
    />
  </div>
</template>

<script>
import { api } from '@/api/api'
import ItemForm from '@/components/ItemForm.vue'

export default {
  name: 'Home',
  components: {
    ItemForm
  },
  data() {
    return {
      items: [],
      loading: true,
      currentPage: 1,
      totalPages: 1,
      totalItems: 0,
      showForm: false
    }
  },
  async mounted() {
    await this.loadItems()
  },
  methods: {
    async loadItems(page = 1) {
      this.loading = true
      try {
        const response = await api.getItems(page, 10)
        if (response.success) {
          this.items = response.data.items
          this.currentPage = response.data.pagination.page
          this.totalPages = response.data.pagination.totalPages
          this.totalItems = response.data.pagination.total
        } else {
          console.error('获取列表失败:', response.message)
        }
      } catch (error) {
        console.error('加载内容列表出错:', error)
      } finally {
        this.loading = false
      }
    },
    goToDetail(id) {
      this.$router.push(`/item/${id}`)
    },
    getPreview(content) {
      const text = content.replace(/<[^>]*>/g, '')
      return text.length > 100 ? text.substring(0, 100) + '...' : text
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('zh-CN')
    },
    changePage(page) {
      if (page < 1 || page > this.totalPages) return
      this.loadItems(page)
    },
    handleNewItem(newItem) {
      // 将新项目添加到列表顶部
      this.items.unshift(newItem)
      // 如果当前是第一页且项目数量超过限制，移除最后一个
      if (this.currentPage === 1 && this.items.length > 10) {
        this.items.pop()
      }
    }
  }
}
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
}

.page-header p {
  color: #6b7280;
  font-size: 16px;
  margin-bottom: 20px;
}

.add-item-btn {
  background: #4a6cf7;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}

.add-item-btn:hover {
  background: #3a5bf5;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.add-first-btn {
  background: #4a6cf7;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.add-first-btn:hover {
  background: #3a5bf5;
}

.items-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.item-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.item-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #1f2937;
  line-height: 1.4;
}

.item-preview {
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 12px;
  font-size: 14px;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  color: #9ca3af;
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
}

.page-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #e5e7eb;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #4b5563;
  font-size: 14px;
}
</style>
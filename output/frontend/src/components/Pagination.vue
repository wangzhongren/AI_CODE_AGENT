<template>
  <div class="pagination">
    <button
      :disabled="currentPage === 1"
      @click="onPrev"
      class="pagination-btn"
    >
      上一页
    </button>
    <span class="page-info">
      第 {{ currentPage }} 页，共 {{ totalPages }} 页
    </span>
    <button
      :disabled="currentPage === totalPages"
      @click="onNext"
      class="pagination-btn"
    >
      下一页
    </button>
  </div>
</template>

<script>
export default {
  name: 'Pagination',
  props: {
    currentPage: {
      type: Number,
      required: true
    },
    totalPages: {
      type: Number,
      required: true
    }
  },
  emits: ['change-page'],
  methods: {
    onPrev() {
      if (this.currentPage > 1) {
        this.$emit('change-page', this.currentPage - 1)
      }
    },
    onNext() {
      if (this.currentPage < this.totalPages) {
        this.$emit('change-page', this.currentPage + 1)
      }
    }
  }
}
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 24px;
  gap: 16px;
}

.pagination-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #f5f5f5;
  border-color: #bbb;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}
</style>
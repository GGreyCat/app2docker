import { onMounted, onUnmounted } from 'vue'

// 全局模态框栈，用于管理多个模态框的层级
const modalStack = []

/**
 * 统一的模态框 ESC 键处理
 * 在 App.vue 中调用一次即可
 */
export function useModalEscape() {
  function handleEscape(event) {
    if (event.key !== 'Escape') return
    
    // 查找所有显示的模态框
    const modals = document.querySelectorAll('.modal.show, .modal.fade.show')
    
    if (modals.length === 0) return
    
    // 获取最上层的模态框（z-index 最高的）
    let topModal = null
    let maxZIndex = -1
    
    modals.forEach(modal => {
      const zIndex = parseInt(window.getComputedStyle(modal).zIndex) || 0
      if (zIndex > maxZIndex) {
        maxZIndex = zIndex
        topModal = modal
      }
    })
    
    if (!topModal) {
      // 如果没有找到，就关闭最后一个
      topModal = modals[modals.length - 1]
    }
    
    // 查找关闭按钮并触发点击
    const closeBtn = topModal.querySelector('.btn-close')
    if (closeBtn) {
      closeBtn.click()
    } else {
      // 如果没有关闭按钮，尝试触发 click.self 事件（点击背景关闭）
      const backdrop = document.querySelector('.modal-backdrop.show')
      if (backdrop) {
        backdrop.click()
      }
    }
  }
  
  onMounted(() => {
    window.addEventListener('keydown', handleEscape)
  })
  
  onUnmounted(() => {
    window.removeEventListener('keydown', handleEscape)
  })
}


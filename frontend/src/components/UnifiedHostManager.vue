<template>
  <div class="unified-host-manager">
    <!-- 子标签导航 -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button 
          type="button" 
          class="nav-link" 
          :class="{ active: activeSubTab === 'ssh' }" 
          @click="activeSubTab = 'ssh'"
        >
          <i class="fas fa-server me-1"></i> SSH主机
        </button>
      </li>
      <li class="nav-item">
        <button 
          type="button" 
          class="nav-link" 
          :class="{ active: activeSubTab === 'agent' }" 
          @click="activeSubTab = 'agent'"
        >
          <i class="fas fa-network-wired me-1"></i> Agent主机
        </button>
      </li>
    </ul>

    <!-- SSH主机管理 -->
    <HostManager v-if="activeSubTab === 'ssh'" />

    <!-- Agent主机管理 -->
    <AgentHostManager v-if="activeSubTab === 'agent'" />
  </div>
</template>

<script>
import HostManager from './HostManager.vue'
import AgentHostManager from './AgentHostManager.vue'
import { ref } from 'vue'

export default {
  name: 'UnifiedHostManager',
  components: {
    HostManager,
    AgentHostManager
  },
  setup() {
    const activeSubTab = ref('ssh')
    
    return {
      activeSubTab
    }
  }
}
</script>

<style scoped>
.unified-host-manager {
  padding: 0;
}

.nav-tabs {
  border-bottom: 2px solid #dee2e6;
}

.nav-tabs .nav-link {
  border: none;
  border-bottom: 2px solid transparent;
  color: #6c757d;
  padding: 0.5rem 1rem;
  transition: all 0.2s;
}

.nav-tabs .nav-link:hover {
  border-bottom-color: #0d6efd;
  color: #0d6efd;
}

.nav-tabs .nav-link.active {
  color: #0d6efd;
  border-bottom-color: #0d6efd;
  background-color: transparent;
  font-weight: 500;
}
</style>


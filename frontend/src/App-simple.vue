<template>
  <div class="p-5">
    <h1>🎉 Vue 3 + Vite 测试</h1>
    <p>如果你能看到这个，说明 Vue 正常工作！</p>
    <button @click="count++" class="btn btn-primary">
      点击次数: {{ count }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const count = ref(0)
</script>

<style>
@import 'bootstrap/dist/css/bootstrap.min.css';
</style>


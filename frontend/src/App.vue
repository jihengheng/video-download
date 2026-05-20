<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark">VRS</span>
        <div>
          <h1>视频研究工作台</h1>
          <p>公开视频解析、下载、字幕提取与结构化总结。</p>
        </div>
      </div>
      <nav class="topnav">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/workspace/tasks">任务工作台</RouterLink>
        <RouterLink to="/history">历史记录</RouterLink>
      </nav>
    </header>

    <main class="page">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

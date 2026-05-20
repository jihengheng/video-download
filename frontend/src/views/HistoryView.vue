<template>
  <section class="stack">
    <div class="section-heading">
      <div>
        <div class="eyebrow">历史记录</div>
        <h2>查看已完成的研究结果、导出内容与后续处理记录。</h2>
      </div>
    </div>

    <div class="history-list">
      <el-card v-for="task in completedTasks" :key="task.id" shadow="hover">
        <div class="history-card">
          <div>
            <h3>{{ task.video_title }}</h3>
            <p>{{ task.source_platform }} · {{ task.selected_format_id }}</p>
          </div>
          <div class="history-actions">
            <TaskStatusBadge :status="task.status" />
            <el-button type="primary" plain @click="router.push(`/results/${task.id}`)">查看结果</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import TaskStatusBadge from "../components/TaskStatusBadge.vue";
import { useTaskStore } from "../stores/tasks";

const router = useRouter();
const tasks = useTaskStore();

const completedTasks = computed(() => tasks.tasks.filter((task) => task.status === "completed"));

onMounted(async () => {
  await tasks.fetchTasks();
});
</script>

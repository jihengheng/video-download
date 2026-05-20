<template>
  <section class="stack">
    <div class="section-heading">
      <div>
        <div class="eyebrow">任务工作台</div>
        <h2>查看每一条任务的进度，并快速回到已完成的研究结果。</h2>
      </div>
      <el-button type="primary" @click="router.push('/')">解析新链接</el-button>
    </div>

    <el-table :data="tasks.tasks" empty-text="暂时还没有任务">
      <el-table-column prop="video_title" label="视频标题" min-width="220" />
      <el-table-column prop="source_platform" label="平台" width="140" />
      <el-table-column label="状态" width="160">
        <template #default="{ row }">
          <TaskStatusBadge :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column label="进度" width="180">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" :show-text="false" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button text @click="router.push(`/workspace/tasks/${row.id}`)">查看</el-button>
          <el-button v-if="row.status === 'completed'" text @click="router.push(`/results/${row.id}`)">结果</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import TaskStatusBadge from "../components/TaskStatusBadge.vue";
import { useTaskStore } from "../stores/tasks";

const router = useRouter();
const tasks = useTaskStore();

onMounted(async () => {
  await tasks.fetchTasks();
});
</script>

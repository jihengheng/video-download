<template>
  <section class="stack" v-if="task">
    <div class="section-heading">
      <div>
        <div class="eyebrow">任务详情</div>
        <h2>{{ task.video_title }}</h2>
      </div>
      <TaskStatusBadge :status="task.status" />
    </div>

    <el-card shadow="never">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="平台">{{ task.source_platform }}</el-descriptions-item>
        <el-descriptions-item label="格式">{{ task.selected_format_id }}</el-descriptions-item>
        <el-descriptions-item label="摘要">{{ task.need_summary ? "开启" : "关闭" }}</el-descriptions-item>
        <el-descriptions-item label="进度">{{ task.progress }}%</el-descriptions-item>
      </el-descriptions>

      <div class="task-actions">
        <el-button v-if="task.status === 'failed' && task.can_retry" @click="handleRetry">重试</el-button>
        <el-button v-if="task.status === 'completed'" type="primary" @click="router.push(`/results/${task.id}`)">查看结果</el-button>
        <el-button danger plain @click="handleDelete">删除</el-button>
      </div>

      <div v-if="downloadArtifacts.length" class="stack">
        <h3>下载文件</h3>
        <div class="task-actions">
          <el-button
            v-for="artifact in downloadArtifacts"
            :key="artifact.storage_key"
            plain
            tag="a"
            :href="artifact.download_url"
            target="_blank"
          >
            {{ artifactLabel(artifact.artifact_type) }}
          </el-button>
        </div>
      </div>
    </el-card>

    <el-alert
      v-if="task.error_message"
      title="任务错误"
      type="error"
      :description="task.error_message"
      show-icon
      :closable="false"
    />
  </section>

  <el-empty v-else description="未找到对应任务" />
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getErrorMessage } from "../api/client";
import TaskStatusBadge from "../components/TaskStatusBadge.vue";
import { useTaskStore } from "../stores/tasks";

const route = useRoute();
const router = useRouter();
const tasks = useTaskStore();
const task = computed(() => tasks.currentTask);
const downloadArtifacts = computed(() => (task.value?.artifacts ?? []).filter((artifact) => artifact.download_url));

onMounted(async () => {
  const accessToken = typeof route.query.token === "string" ? route.query.token : null;
  await tasks.fetchTask(Number(route.params.id), accessToken);
});

async function handleRetry() {
  try {
    const accessToken = typeof route.query.token === "string" ? route.query.token : null;
    await tasks.retry(Number(route.params.id), accessToken);
    ElMessage.success("任务已重新发起");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "重试失败"));
  }
}

async function handleDelete() {
  try {
    const accessToken = typeof route.query.token === "string" ? route.query.token : null;
    await tasks.remove(Number(route.params.id), accessToken);
    ElMessage.success("任务已删除");
    await router.push("/workspace/tasks");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "删除失败"));
  }
}

function artifactLabel(artifactType: string) {
  return {
    video: "下载视频",
    notes: "下载笔记",
    manifest: "下载清单",
  }[artifactType] ?? `下载 ${artifactType}`;
}
</script>

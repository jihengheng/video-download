<template>
  <section class="stack" v-if="result">
    <div class="section-heading">
      <div>
        <div class="eyebrow">任务结果</div>
        <h2>{{ result.title_suggestion || "结构化研究笔记" }}</h2>
      </div>
      <el-button text @click="router.push(`/workspace/tasks/${route.params.id}`)">返回任务</el-button>
    </div>

    <el-card shadow="never">
      <h3>摘要</h3>
      <p>{{ result.summary }}</p>
      <div class="tag-row">
        <el-tag v-for="tag in result.tags" :key="tag" effect="plain">{{ tag }}</el-tag>
      </div>
    </el-card>

    <div class="result-grid">
      <el-card shadow="never">
        <h3>关键要点</h3>
        <ul class="bullet-list">
          <li v-for="point in result.key_points" :key="point">{{ point }}</li>
        </ul>
      </el-card>

      <el-card shadow="never">
        <h3>时间线</h3>
        <div v-for="entry in result.timeline" :key="`${entry.time}-${entry.label}`" class="timeline-entry">
          <strong>{{ entry.time }} · {{ entry.label }}</strong>
          <p>{{ entry.description }}</p>
        </div>
      </el-card>
    </div>

    <el-card shadow="never">
      <h3>字幕全文</h3>
      <p class="transcript-body">{{ result.transcript }}</p>
    </el-card>

    <el-card v-if="downloadArtifacts.length" shadow="never">
      <div class="section-heading">
        <div>
          <h3>导出与下载</h3>
          <p class="inspect-help">你可以直接下载视频、研究笔记或任务清单。</p>
        </div>
      </div>
      <div class="task-actions">
        <el-button
          v-for="artifact in downloadArtifacts"
          :key="artifact.storage_key"
          type="primary"
          plain
          tag="a"
          :href="artifact.download_url"
          target="_blank"
        >
          {{ artifactLabel(artifact.artifact_type) }}
        </el-button>
      </div>
    </el-card>
  </section>

  <el-empty v-else description="结果暂未就绪" />
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useTaskStore } from "../stores/tasks";

const route = useRoute();
const router = useRouter();
const tasks = useTaskStore();
const result = computed(() => tasks.currentResult);
const downloadArtifacts = computed(() => (result.value?.artifacts ?? []).filter((artifact) => artifact.download_url));

onMounted(async () => {
  const accessToken = typeof route.query.token === "string" ? route.query.token : null;
  await tasks.fetchResult(Number(route.params.id), accessToken);
});

function artifactLabel(artifactType: string) {
  return {
    video: "下载视频",
    notes: "下载笔记",
    manifest: "下载清单",
  }[artifactType] ?? `下载 ${artifactType}`;
}
</script>

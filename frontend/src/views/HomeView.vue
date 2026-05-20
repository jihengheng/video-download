<template>
  <section class="hero-grid">
    <div class="hero-panel">
      <div class="eyebrow">公开视频研究</div>
      <h2>输入公开视频链接，快速生成结构化摘要与研究笔记。</h2>
      <p class="lede">
        提交公开链接后，你可以先预览可下载格式，再发起任务，最终在同一个工作台里查看字幕、要点与可导出的笔记。
      </p>

      <el-form @submit.prevent="handleInspect">
        <el-form-item label="视频链接">
          <el-input v-model="url" size="large" placeholder="https://www.youtube.com/watch?v=..." />
        </el-form-item>
        <div class="hero-actions">
          <el-button type="primary" size="large" :loading="tasks.loading" @click="handleInspect">
            解析链接
          </el-button>
          <el-tag type="warning" effect="plain">仅支持公开链接</el-tag>
          <el-tag effect="plain">免费试用，按日限额</el-tag>
        </div>
      </el-form>

      <div class="notice-grid">
        <article>
          <h3>1. 先解析</h3>
          <p>在消耗额度前，先查看平台、时长以及可下载格式。</p>
        </article>
        <article>
          <h3>2. 再处理</h3>
          <p>把下载、字幕提取和摘要生成放进同一条异步任务中执行。</p>
        </article>
        <article>
          <h3>3. 最后查看</h3>
          <p>在结果页阅读摘要、时间线和可导出的研究笔记。</p>
        </article>
      </div>
    </div>

    <aside class="side-column">
      <QuotaCard :quota="session.quota" />
      <AuthPanel v-if="!session.isAuthenticated" />
      <el-card v-else shadow="hover">
        <h3>已登录工作台</h3>
        <p>你的任务、重试记录和导出结果都可以在工作台与历史页中查看。</p>
        <el-button text @click="session.signOut">退出登录</el-button>
      </el-card>
      <el-alert
        title="请仍然遵守版权与平台规则"
        type="warning"
        show-icon
        :closable="false"
        description="本产品面向公开链接研究与笔记整理场景，请勿用于私有内容或未获授权的内容。"
      />
    </aside>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { getErrorMessage } from "../api/client";
import AuthPanel from "../components/AuthPanel.vue";
import QuotaCard from "../components/QuotaCard.vue";
import { useSessionStore } from "../stores/session";
import { useTaskStore } from "../stores/tasks";

const router = useRouter();
const session = useSessionStore();
const tasks = useTaskStore();
const url = ref("");

onMounted(async () => {
  try {
    await session.refreshQuota();
  } catch {
    // Keep the page interactive even when the API is not yet reachable.
  }
});

async function handleInspect() {
  if (!url.value) {
    ElMessage.warning("请输入公开视频链接");
    return;
  }
  try {
    await tasks.inspect(url.value);
    await router.push({ name: "inspect", query: { url: url.value } });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "解析失败，请检查链接后重试"));
  }
}
</script>

<template>
  <section class="stack">
    <div class="section-heading">
      <div>
        <div class="eyebrow">解析结果</div>
        <h2>选择下载格式，并决定是否生成摘要笔记。</h2>
      </div>
      <el-button text @click="router.push('/')">返回首页</el-button>
    </div>

    <el-card v-if="inspected" shadow="never">
      <div class="inspect-grid inspect-grid--result">
        <div class="inspect-main">
          <div class="inspect-media">
            <img
              v-if="inspected.thumbnail_url"
              :src="inspected.thumbnail_url"
              :alt="`${inspected.title} 的封面`"
              class="inspect-cover"
            />
            <div v-else class="inspect-cover inspect-cover--placeholder">暂无封面</div>
          </div>

          <div class="inspect-overview">
            <h3 class="inspect-title">{{ inspected.title }}</h3>
            <div class="inspect-meta-grid">
              <div class="inspect-meta-card">
                <span class="inspect-meta-label">来源平台</span>
                <strong>{{ inspected.source_platform }}</strong>
              </div>
              <div class="inspect-meta-card">
                <span class="inspect-meta-label">视频时长</span>
                <strong>{{ durationLabel }}</strong>
              </div>
              <div class="inspect-meta-card">
                <span class="inspect-meta-label">预计处理耗时</span>
                <strong>{{ inspected.estimated_processing_minutes }} 分钟</strong>
              </div>
              <div class="inspect-meta-card">
                <span class="inspect-meta-label">总结能力</span>
                <strong>{{ inspected.supports_summary ? "可生成摘要" : "仅支持下载" }}</strong>
              </div>
            </div>
          </div>
        </div>

        <div class="inspect-sidebar inspect-sidebar--result">
          <div class="summary-toggle-row">
            <div>
              <strong>生成摘要</strong>
              <p class="inspect-help">
                {{ inspected.supports_summary ? "检测到可用字幕，可生成结构化总结。" : "当前视频未检测到可用字幕，暂时只能下载。" }}
              </p>
            </div>
            <el-switch v-model="needSummary" active-text="开启" :disabled="!inspected.supports_summary" />
          </div>
          <el-alert
            :title="inspected.supports_summary ? '摘要会基于字幕内容生成结构化总结。' : '这条视频当前无法直接生成摘要。'"
            :type="inspected.supports_summary ? 'info' : 'warning'"
            :closable="false"
          />
        </div>
      </div>

      <div class="stack">
        <div class="formats-heading">
          <div>
            <h3>可下载格式</h3>
            <p class="inspect-help">默认展示可直接观看的视频格式。仅音频格式已收进高级选项，避免误点。</p>
          </div>
          <el-tag effect="plain">{{ inspected.formats.length }} 个可用格式</el-tag>
        </div>

        <el-radio-group v-model="selectedFormat" class="sr-only" aria-label="选择下载格式">
          <el-radio
            v-for="format in inspected.formats"
            :key="`radio-${format.format_id}`"
            :value="format.format_id"
          >
            {{ format.format_id }}
          </el-radio>
        </el-radio-group>

        <div class="stack">
          <div class="formats-subheading">
            <strong>常用下载格式</strong>
            <span class="inspect-help">优先显示带画面的视频格式。</span>
          </div>

          <div class="format-list">
            <button
              v-for="format in primaryFormats"
              :key="format.format_id"
              type="button"
              class="format-card format-card--button"
              :class="{ 'is-selected': selectedFormat === format.format_id }"
              @click="selectedFormat = format.format_id"
            >
              <div class="format-card__header">
                <strong>{{ format.format_id }}</strong>
                <div class="tag-row">
                  <el-tag size="small" effect="plain">{{ format.ext }}</el-tag>
                  <el-tag v-if="format.has_video && format.has_audio" size="small" type="success" effect="plain">音视频</el-tag>
                  <el-tag v-else-if="format.has_video" size="small" type="warning" effect="plain">仅视频</el-tag>
                </div>
              </div>
              <p class="format-card__summary">
                {{ format.resolution }} · {{ format.filesize_mb ?? "--" }} MB
              </p>
              <span class="format-card__note">{{ format.note || "标准格式" }}</span>
            </button>
          </div>
        </div>

        <el-collapse v-if="audioOnlyFormats.length" class="advanced-collapse">
          <el-collapse-item name="audio-only">
            <template #title>
              <div class="advanced-title">
                <strong>高级选项</strong>
                <span>仅音频格式，适合提取声音或做播客式收听</span>
              </div>
            </template>

            <div class="format-list">
              <button
                v-for="format in audioOnlyFormats"
                :key="format.format_id"
                type="button"
                class="format-card format-card--button"
                :class="{ 'is-selected': selectedFormat === format.format_id }"
                @click="selectedFormat = format.format_id"
              >
                <div class="format-card__header">
                  <strong>{{ format.format_id }}</strong>
                  <div class="tag-row">
                    <el-tag size="small" effect="plain">{{ format.ext }}</el-tag>
                    <el-tag size="small" type="info" effect="plain">仅音频</el-tag>
                  </div>
                </div>
                <p class="format-card__summary">
                  {{ format.resolution }} · {{ format.filesize_mb ?? "--" }} MB
                </p>
                <span class="format-card__note">{{ format.note || "音频流" }}</span>
              </button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <div class="hero-actions">
        <el-button type="primary" :loading="tasks.loading" @click="handlePrimaryAction">
          {{ inspected.supports_summary ? "创建任务" : "直接下载" }}
        </el-button>
        <el-button
          v-if="inspected.supports_summary"
          plain
          :loading="tasks.loading"
          @click="downloadDirectly"
        >
          仅下载，不做总结
        </el-button>
        <el-button plain @click="router.push('/workspace/tasks')">打开工作台</el-button>
      </div>
    </el-card>

    <el-empty v-else description="还没有解析数据，请先回首页输入链接。" />
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getErrorMessage } from "../api/client";
import { useTaskStore } from "../stores/tasks";

const route = useRoute();
const router = useRouter();
const tasks = useTaskStore();
const needSummary = ref(true);
const selectedFormat = ref("");

const inspected = computed(() => tasks.inspected);
const allFormats = computed(() => inspected.value?.formats ?? []);
const durationLabel = computed(() => formatDuration(inspected.value?.duration_seconds));
const primaryFormats = computed(() => {
  const videoFormats = allFormats.value.filter((format) => format.has_video);
  return videoFormats.length ? videoFormats : allFormats.value;
});
const audioOnlyFormats = computed(() => {
  const hasExplicitVideoFormats = allFormats.value.some((format) => format.has_video);
  return hasExplicitVideoFormats ? allFormats.value.filter((format) => format.has_video === false) : [];
});

onMounted(async () => {
  const url = route.query.url;
  if (typeof url === "string" && !tasks.inspected) {
    await tasks.inspect(url);
  }
  needSummary.value = Boolean(tasks.inspected?.supports_summary);
  const preferredFormat = pickPreferredFormat(tasks.inspected?.formats ?? []);
  if (preferredFormat) {
    selectedFormat.value = preferredFormat.format_id;
  }
});

async function submitTask() {
  const url = route.query.url;
  if (typeof url !== "string" || !selectedFormat.value) {
    ElMessage.error("缺少解析结果或未选择格式");
    return;
  }
  try {
    const task = await tasks.create({ url, format_id: selectedFormat.value, need_summary: needSummary.value });
    ElMessage.success("任务已创建");
    await router.push({ path: `/workspace/tasks/${task.id}`, query: { token: task.public_token } });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "任务创建失败"));
  }
}

async function handlePrimaryAction() {
  if (!inspected.value) {
    ElMessage.error("缺少解析结果");
    return;
  }

  if (inspected.value.supports_summary) {
    await submitTask();
    return;
  }

  await downloadDirectly();
}

async function downloadDirectly() {
  const url = route.query.url;
  if (typeof url !== "string" || !selectedFormat.value) {
    ElMessage.error("缺少解析结果或未选择格式");
    return;
  }

  try {
    const response = await tasks.directDownload({ url, format_id: selectedFormat.value });
    const contentTypeHeader = response.headers["content-type"];
    const contentType = typeof contentTypeHeader === "string" ? contentTypeHeader : "application/octet-stream";
    const blob = new Blob([response.data], { type: contentType });
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const disposition = response.headers["content-disposition"] as string | undefined;
    const filenameMatch = disposition?.match(/filename="?([^"]+)"?/i);
    link.href = objectUrl;
    link.download = filenameMatch?.[1] || `${inspected.value?.title || "video"}.mp4`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(objectUrl);
    ElMessage.success("下载已开始");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "下载失败，请稍后重试"));
  }
}

function formatDuration(durationSeconds?: number | null) {
  if (!durationSeconds) {
    return "--";
  }

  const hours = Math.floor(durationSeconds / 3600);
  const minutes = Math.floor((durationSeconds % 3600) / 60);
  const seconds = durationSeconds % 60;

  if (hours > 0) {
    return `${hours}小时 ${minutes}分 ${seconds}秒`;
  }
  return `${minutes}分 ${seconds}秒`;
}

function pickPreferredFormat(formats: Array<{ format_id: string; has_video?: boolean; has_audio?: boolean }>) {
  return (
    formats.find((format) => format.has_video && format.has_audio) ??
    formats.find((format) => format.has_video) ??
    formats[0]
  );
}
</script>

<template>
  <el-tag :type="tagType" effect="dark">{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ status: string }>();

const label = computed(() => {
  const mapping: Record<string, string> = {
    pending: "等待中",
    parsing: "解析中",
    downloading: "下载中",
    transcribing: "字幕处理中",
    summarizing: "总结中",
    completed: "已完成",
    failed: "失败",
    deleted: "已删除",
  };
  return mapping[props.status] ?? props.status.replaceAll("_", " ");
});
const tagType = computed(() => {
  if (props.status === "completed") return "success";
  if (props.status === "failed") return "danger";
  if (props.status === "deleted") return "info";
  return "warning";
});
</script>

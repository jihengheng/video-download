<template>
  <el-card class="quota-card" shadow="hover">
    <div class="quota-card__header">
      <span>今日额度</span>
      <strong>剩余 {{ quota?.remaining_count ?? "--" }} 次</strong>
    </div>
    <el-progress
      :percentage="usagePercentage"
      :show-text="false"
      :stroke-width="10"
      color="#d97706"
    />
    <p class="quota-card__meta">
      今日已使用 {{ quota?.used_count ?? 0 }} / {{ quota?.limit_count ?? 0 }} 次任务额度。
    </p>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  quota?: { used_count: number; limit_count: number; remaining_count: number } | null;
}>();

const usagePercentage = computed(() => {
  if (!props.quota || props.quota.limit_count === 0) return 0;
  return Math.round((props.quota.used_count / props.quota.limit_count) * 100);
});
</script>

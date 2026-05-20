import { defineStore } from "pinia";
import { ref } from "vue";

import {
  createTask,
  directDownloadVideo,
  deleteTask,
  deleteTaskWithAccess,
  getResult,
  getResultWithAccess,
  getTask,
  getTaskWithAccess,
  getTasks,
  inspectVideo,
  retryTask,
  retryTaskWithAccess,
} from "../api/tasks";
import type { InspectResponse, SummaryResult, TaskItem } from "../types/api";

export const useTaskStore = defineStore("tasks", () => {
  const inspected = ref<InspectResponse | null>(null);
  const tasks = ref<TaskItem[]>([]);
  const currentTask = ref<TaskItem | null>(null);
  const currentResult = ref<SummaryResult | null>(null);
  const loading = ref(false);

  async function inspect(url: string) {
    loading.value = true;
    try {
      inspected.value = await inspectVideo(url);
      return inspected.value;
    } finally {
      loading.value = false;
    }
  }

  async function create(payload: { url: string; format_id: string; need_summary: boolean }) {
    loading.value = true;
    try {
      currentTask.value = await createTask(payload);
      return currentTask.value;
    } finally {
      loading.value = false;
    }
  }

  async function directDownload(payload: { url: string; format_id: string }) {
    loading.value = true;
    try {
      return await directDownloadVideo(payload);
    } finally {
      loading.value = false;
    }
  }

  async function fetchTasks() {
    const response = await getTasks();
    tasks.value = response.items;
  }

  async function fetchTask(taskId: number, accessToken?: string | null) {
    currentTask.value = accessToken ? await getTaskWithAccess(taskId, accessToken) : await getTask(taskId);
  }

  async function fetchResult(taskId: number, accessToken?: string | null) {
    currentResult.value = accessToken ? await getResultWithAccess(taskId, accessToken) : await getResult(taskId);
  }

  async function retry(taskId: number, accessToken?: string | null) {
    if (accessToken) {
      await retryTaskWithAccess(taskId, accessToken);
      await fetchTask(taskId, accessToken);
      return;
    }
    await retryTask(taskId);
    await fetchTask(taskId);
  }

  async function remove(taskId: number, accessToken?: string | null) {
    if (accessToken) {
      await deleteTaskWithAccess(taskId, accessToken);
    } else {
      await deleteTask(taskId);
    }
    tasks.value = tasks.value.filter((task) => task.id !== taskId);
  }

  return {
    inspected,
    tasks,
    currentTask,
    currentResult,
    loading,
    inspect,
    create,
    directDownload,
    fetchTasks,
    fetchTask,
    fetchResult,
    retry,
    remove,
  };
});

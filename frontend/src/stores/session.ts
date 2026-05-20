import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { attachToken } from "../api/client";
import { getQuota, login, register } from "../api/tasks";

export const useSessionStore = defineStore("session", () => {
  const token = ref<string | null>(localStorage.getItem("vrs-token"));
  const quota = ref<{ remaining_count: number; limit_count: number; used_count: number } | null>(null);
  const loading = ref(false);

  attachToken(token.value);

  const isAuthenticated = computed(() => Boolean(token.value));

  async function signUp(email: string, password: string) {
    loading.value = true;
    try {
      const response = await register(email, password);
      setToken(response.access_token);
      await refreshQuota();
    } finally {
      loading.value = false;
    }
  }

  async function signIn(email: string, password: string) {
    loading.value = true;
    try {
      const response = await login(email, password);
      setToken(response.access_token);
      await refreshQuota();
    } finally {
      loading.value = false;
    }
  }

  async function refreshQuota() {
    quota.value = await getQuota();
  }

  function setToken(nextToken: string | null) {
    token.value = nextToken;
    attachToken(nextToken);
    if (nextToken) {
      localStorage.setItem("vrs-token", nextToken);
    } else {
      localStorage.removeItem("vrs-token");
    }
  }

  function signOut() {
    setToken(null);
    quota.value = null;
  }

  return {
    token,
    quota,
    loading,
    isAuthenticated,
    signIn,
    signOut,
    signUp,
    refreshQuota,
  };
});

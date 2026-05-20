<template>
  <el-card class="auth-panel" shadow="hover">
    <template #header>
      <div class="auth-panel__header">
        <h3>登录后可查看历史并重试任务</h3>
        <el-switch v-model="isRegister" active-text="注册" inactive-text="登录" />
      </div>
    </template>

    <el-form @submit.prevent="submit">
      <el-form-item label="邮箱">
        <el-input v-model="email" placeholder="researcher@example.com" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="password" type="password" show-password placeholder="至少 8 位字符" />
      </el-form-item>
      <el-button type="primary" :loading="session.loading" @click="submit">
        {{ isRegister ? "创建账号" : "立即登录" }}
      </el-button>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { ref } from "vue";

import { getErrorMessage } from "../api/client";
import { useSessionStore } from "../stores/session";

const session = useSessionStore();
const isRegister = ref(false);
const email = ref("");
const password = ref("");

async function submit() {
  try {
    if (isRegister.value) {
      await session.signUp(email.value, password.value);
      ElMessage.success("账号创建成功");
    } else {
      await session.signIn(email.value, password.value);
      ElMessage.success("登录成功");
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "认证失败，请检查邮箱和密码"));
  }
}
</script>

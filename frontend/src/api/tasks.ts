import { apiClient } from "./client";
import type { InspectResponse, QuotaResponse, SummaryResult, TaskItem, TaskListResponse } from "../types/api";

export async function inspectVideo(url: string): Promise<InspectResponse> {
  const { data } = await apiClient.post<InspectResponse>("/video/inspect", { url });
  return data;
}

export async function directDownloadVideo(payload: { url: string; format_id: string }) {
  const response = await apiClient.post("/video/download", payload, {
    responseType: "blob",
    timeout: 0,
  });
  return response;
}

export async function createTask(payload: { url: string; format_id: string; need_summary: boolean }): Promise<TaskItem> {
  const { data } = await apiClient.post<TaskItem>("/tasks", payload);
  return data;
}

export async function getTasks(): Promise<TaskListResponse> {
  const { data } = await apiClient.get<TaskListResponse>("/tasks");
  return data;
}

export async function getTask(taskId: number): Promise<TaskItem> {
  const { data } = await apiClient.get<TaskItem>(`/tasks/${taskId}`);
  return data;
}

export async function getTaskWithAccess(taskId: number, accessToken?: string | null): Promise<TaskItem> {
  const { data } = await apiClient.get<TaskItem>(`/tasks/${taskId}`, { params: { access_token: accessToken ?? undefined } });
  return data;
}

export async function retryTask(taskId: number): Promise<void> {
  await apiClient.post(`/tasks/${taskId}/retry`);
}

export async function retryTaskWithAccess(taskId: number, accessToken?: string | null): Promise<void> {
  await apiClient.post(`/tasks/${taskId}/retry`, null, { params: { access_token: accessToken ?? undefined } });
}

export async function deleteTask(taskId: number): Promise<void> {
  await apiClient.delete(`/tasks/${taskId}`);
}

export async function deleteTaskWithAccess(taskId: number, accessToken?: string | null): Promise<void> {
  await apiClient.delete(`/tasks/${taskId}`, { params: { access_token: accessToken ?? undefined } });
}

export async function getResult(taskId: number): Promise<SummaryResult> {
  const { data } = await apiClient.get<SummaryResult>(`/tasks/${taskId}/result`);
  return data;
}

export async function getResultWithAccess(taskId: number, accessToken?: string | null): Promise<SummaryResult> {
  const { data } = await apiClient.get<SummaryResult>(`/tasks/${taskId}/result`, {
    params: { access_token: accessToken ?? undefined },
  });
  return data;
}

export async function getQuota(): Promise<QuotaResponse> {
  const { data } = await apiClient.get<QuotaResponse>("/auth/quota");
  return data;
}

export async function register(email: string, password: string): Promise<{ access_token: string }> {
  const { data } = await apiClient.post<{ access_token: string }>("/auth/register", { email, password });
  return data;
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const { data } = await apiClient.post<{ access_token: string }>("/auth/login", { email, password });
  return data;
}

import { vi } from "vitest";

vi.mock("../../api/tasks", () => ({
  getQuota: vi.fn().mockResolvedValue({
    quota_date: "2026-05-17",
    limit_count: 3,
    used_count: 0,
    remaining_count: 3,
  }),
  login: vi.fn(),
  register: vi.fn(),
  inspectVideo: vi.fn(),
  createTask: vi.fn(),
  getTasks: vi.fn(),
  getTask: vi.fn(),
  getTaskWithAccess: vi.fn(),
  retryTask: vi.fn(),
  retryTaskWithAccess: vi.fn(),
  deleteTask: vi.fn(),
  deleteTaskWithAccess: vi.fn(),
  getResult: vi.fn(),
  getResultWithAccess: vi.fn(),
}));

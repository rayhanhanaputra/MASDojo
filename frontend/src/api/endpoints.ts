// Typed endpoint helpers, one per backend route used by the UI.

import { authedFetch, request, uploadForm } from "./client";
import type {
  ApiKeyStatus,
  HintResponse,
  Provider,
  InstanceConfig,
  LabSessionAdminView,
  ProfileStats,
  Role,
  RosterEntry,
  SkillMap,
  SystemCheckItem,
  Submission,
  TaskCreate,
  TaskDetail,
  TaskManageView,
  TaskSummary,
  TaskUpdate,
  TokenResponse,
  UserAdminView,
  UserPublic,
} from "./types";

export const api = {
  // public front-end config (deployment mode)
  config: () => request<{ solo_mode: boolean }>("/config", { auth: false }),

  // auth
  register: (email: string, display_name: string, password: string) =>
    request<UserPublic>("/auth/register", {
      method: "POST",
      auth: false,
      body: { email, display_name, password },
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    }),
  me: () => request<UserPublic>("/auth/me"),

  // tasks + pathway
  listTasks: () => request<TaskSummary[]>("/tasks"),
  getTask: (id: string) => request<TaskDetail>(`/tasks/${id}`),
  skillMap: () => request<SkillMap>("/pathway/skill-map"),
  revealHint: (id: string, tier: number) =>
    request<HintResponse>(`/tasks/${id}/hints/${tier}`, { method: "POST" }),

  // all-in-one target APK
  targetApkStatus: () =>
    request<{ available: boolean; filename: string; size: number }>(
      "/download/target-apk/status",
    ),

  // challenge files
  listArtifacts: (taskId: string) =>
    request<{ path: string; size: number }[]>(`/tasks/${taskId}/artifacts`),
  getArtifactText: async (taskId: string, filePath: string) => {
    const enc = filePath.split("/").map(encodeURIComponent).join("/");
    return (await authedFetch(`/tasks/${taskId}/artifacts/${enc}`)).text();
  },

  // submissions
  submit: (taskId: string, payload: Record<string, unknown>) =>
    request<Submission>(`/submissions/${taskId}`, { method: "POST", body: { payload } }),
  getSubmission: (id: number) => request<Submission>(`/submissions/${id}`),
  listSubmissions: (taskId?: string) =>
    request<Submission[]>(`/submissions${taskId ? `?task_id=${taskId}` : ""}`),

  // settings (BYOK)
  getAiKey: () => request<ApiKeyStatus>("/settings/ai-key"),
  setAiKey: (
    provider: Provider,
    api_key: string,
    base_url?: string,
    model?: string,
  ) =>
    request<ApiKeyStatus>("/settings/ai-key", {
      method: "PUT",
      body: { provider, api_key, base_url: base_url || null, model: model || null },
    }),
  deleteAiKey: () => request<void>("/settings/ai-key", { method: "DELETE" }),

  // mentor
  mentorHint: (task_id: string, attempt: string, error: string) =>
    request<HintResponse>("/mentor/hint", { method: "POST", body: { task_id, attempt, error } }),
  mentorExplain: (task_id: string, snippet: string) =>
    request<{ explanation: string }>("/mentor/explain", {
      method: "POST",
      body: { task_id, snippet },
    }),
  mentorReview: (task_id: string) =>
    request<{ review: string }>("/mentor/review", { method: "POST", body: { task_id } }),
  // AI-as-adversary: AI proposes a solution, graded for real by the emulator.
  mentorAttempt: (task_id: string) =>
    request<{ submission_id: number; field: string; candidate: string; note: string }>(
      "/mentor/attempt",
      { method: "POST", body: { task_id } },
    ),

  streamToken: (submissionId: number) =>
    request<{ token: string }>(`/submissions/${submissionId}/stream-token`),

  // stats
  stats: () => request<ProfileStats>("/stats"),
  userStats: (userId: number) => request<ProfileStats>(`/stats/users/${userId}`),
  roster: () => request<RosterEntry[]>("/stats/roster"),

  // interactive lab playground
  labStartSession: (task_id: string) =>
    request<{
      id: number;
      task_id: string;
      status: string;
      device_serial: string | null;
      expires_at: string;
      stream_url: string | null;
    }>("/lab/sessions", { method: "POST", body: { task_id } }),
  labEndSession: () => request<void>("/lab/sessions/current", { method: "DELETE" }),

  // admin: system health + instance settings (mode, registration, lab, AI)
  adminSystemCheck: () => request<SystemCheckItem[]>("/admin/system"),
  adminLabSessions: () => request<LabSessionAdminView[]>("/admin/lab/sessions"),
  adminGetSettings: () => request<InstanceConfig>("/admin/settings"),
  adminUpdateSettings: (patch: {
    registration_open?: boolean;
    lab_enabled?: boolean;
    lab_allow_device_hosted?: boolean;
    lab_emulator_image?: string;
    lab_emulator_adb_port?: number;
    lab_emulator_serial?: string;
    lab_emulator_boot_timeout_sec?: number;
    lab_session_ttl_min?: number;
    lab_mem_limit?: string;
    lab_cpu_limit?: string;
    lab_pids_limit?: number;
    lab_stream_url?: string;
    grading_job_timeout_sec?: number;
    mentor_rate_limit_per_hour?: number;
  }) => request<InstanceConfig>("/admin/settings", { method: "PATCH", body: patch }),
  adminSwitchToHosted: (email: string, display_name: string, password: string) =>
    request<InstanceConfig>("/admin/settings/switch-to-hosted", {
      method: "POST",
      body: { email, display_name, password },
    }),
  adminSwitchToSolo: () =>
    request<InstanceConfig>("/admin/settings/switch-to-solo", { method: "POST" }),
  adminSetFallback: (
    provider: "anthropic" | "openai",
    api_key: string,
    base_url?: string,
    model?: string,
  ) =>
    request<InstanceConfig>("/admin/settings/ai-fallback", {
      method: "PUT",
      body: { provider, api_key, base_url: base_url || null, model: model || null },
    }),
  adminClearFallback: () =>
    request<InstanceConfig>("/admin/settings/ai-fallback", { method: "DELETE" }),

  // admin (manage users) — requires admin role
  adminListUsers: () => request<UserAdminView[]>("/admin/users"),
  adminSetRole: (userId: number, role: Role) =>
    request<UserAdminView>(`/admin/users/${userId}/role`, { method: "PATCH", body: { role } }),
  adminSetActive: (userId: number, is_active: boolean) =>
    request<UserAdminView>(`/admin/users/${userId}/active`, {
      method: "PATCH",
      body: { is_active },
    }),
  adminDeleteUser: (userId: number) =>
    request<void>(`/admin/users/${userId}`, { method: "DELETE" }),

  // instructor (manage tasks) — requires instructor role
  instructorListTasks: () => request<TaskManageView[]>("/instructor/tasks"),
  instructorUpdateTask: (taskId: string, patch: TaskUpdate) =>
    request<TaskManageView>(`/instructor/tasks/${taskId}`, { method: "PATCH", body: patch }),
  instructorCreateTask: (body: TaskCreate) =>
    request<TaskManageView>("/instructor/tasks", { method: "POST", body }),
  instructorDeleteTask: (taskId: string) =>
    request<void>(`/instructor/tasks/${taskId}`, { method: "DELETE" }),
  instructorUploadApk: (taskId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return uploadForm<TaskManageView>(`/instructor/tasks/${taskId}/apk`, form);
  },
};

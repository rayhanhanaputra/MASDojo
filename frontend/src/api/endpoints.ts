// Typed endpoint helpers, one per backend route used by the UI.

import { authedFetch, request } from "./client";
import type {
  ApiKeyStatus,
  HintResponse,
  Provider,
  ProfileStats,
  SkillMap,
  Submission,
  TaskDetail,
  TaskSummary,
  TokenResponse,
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
  setAiKey: (provider: Provider, api_key: string) =>
    request<ApiKeyStatus>("/settings/ai-key", { method: "PUT", body: { provider, api_key } }),
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

  // proof-of-pwn
  getCertificate: (submissionId: number) =>
    request<{ token: string; payload: Record<string, unknown> }>(
      `/submissions/${submissionId}/certificate`,
    ),
  verifyCertificate: (token: string) =>
    request<{ valid: boolean; payload: Record<string, unknown> | null }>("/verify", {
      method: "POST",
      auth: false,
      body: { token },
    }),

  streamToken: (submissionId: number) =>
    request<{ token: string }>(`/submissions/${submissionId}/stream-token`),

  // stats
  stats: () => request<ProfileStats>("/stats"),
};

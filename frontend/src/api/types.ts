// Shapes mirror the backend Pydantic models.

export type Role = "learner" | "instructor" | "admin";

export interface UserPublic {
  id: number;
  email: string;
  display_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface SystemCheckItem {
  component: string;
  status: "ok" | "warn" | "down" | "disabled";
  detail: string;
  hint: string;
}

export interface LabSessionAdminView {
  id: number;
  user_id: number;
  user_email: string;
  task_id: string;
  device_serial: string | null;
  expires_at: string;
}

export interface RosterEntry {
  id: number;
  email: string;
  display_name: string;
  role: Role;
  tasks_passed: number;
  tasks_total: number;
  total_score: number;
}

export interface InstanceConfig {
  solo_mode: boolean;
  registration_open: boolean;
  lab_enabled: boolean;
  lab_allow_device_hosted: boolean;
  ai_fallback_configured: boolean;
  ai_fallback_provider: "anthropic" | "openai" | null;
  ai_fallback_masked: string | null;
  ai_fallback_base_url: string | null;
  ai_fallback_model: string | null;
}

export interface UserAdminView {
  id: number;
  email: string;
  display_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface TaskManageView {
  id: string;
  title: string;
  module: string;
  order_index: number;
  domain: string;
  difficulty: number;
  time_estimate_min: number;
  objective: string;
  success_type: SuccessType;
  grader_status: string;
  is_reference: boolean;
  is_published: boolean;
  instructor_edited: boolean;
  source: string;
  submission_schema: Record<string, unknown>;
  expected_value: string;
  hints: Record<string, string>;
  has_target_apk: boolean;
  artifact_count: number;
}

export interface TaskUpdate {
  title?: string;
  module?: string;
  order_index?: number;
  difficulty?: number;
  time_estimate_min?: number;
  objective?: string;
  is_published?: boolean;
  hints?: { h1?: string; h2?: string; h3?: string; solution?: string };
  expected_value?: string;
  success_type?: string;
  submission_schema?: Record<string, unknown>;
}

export interface TaskCreate {
  id: string;
  title: string;
  module: string;
  domain: string;
  success_type: "flag" | "static_assert";
  objective?: string;
  difficulty?: number;
  time_estimate_min?: number;
  masvs?: string[];
  order_index?: number;
  submission_schema?: Record<string, unknown>;
  expected_value: string;
  hints?: { h1?: string; h2?: string; h3?: string; solution?: string };
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type SuccessType = "flag" | "static_assert" | "frida_assert" | "network_assert";
export type NodeState = "locked" | "available" | "passed";

export interface TaskSummary {
  id: string;
  title: string;
  module: string;
  order_index: number;
  domain: string;
  masvs: string[];
  difficulty: number;
  prereqs: string[];
  success_type: SuccessType;
  time_estimate_min: number;
  is_reference: boolean;
  grader_status: "implemented" | "todo";
}

export interface TaskDetail extends TaskSummary {
  mastg_refs: string[];
  objective: string;
  submission_schema: Record<string, unknown>;
  hint_count: number;
}

export interface SkillNode {
  id: string;
  title: string;
  module: string;
  domain: string;
  difficulty: number;
  prereqs: string[];
  success_type: SuccessType;
  masvs: string[];
  is_reference: boolean;
  state: NodeState;
  best_score: number;
  attempts: number;
}

export interface SkillMap {
  nodes: SkillNode[];
  recommended_task_id: string | null;
}

export interface CheckResult {
  name: string;
  passed: boolean;
  detail: string;
}

// A structured artifact backing the verdict (log, trace, timeline, note).
export interface EvidenceItem {
  label: string;
  kind: string;
  content: string;
}

export type SubmissionStatus = "queued" | "running" | "passed" | "failed" | "error";

export interface Submission {
  id: number;
  task_id: string;
  success_type: SuccessType;
  status: SubmissionStatus;
  evidence: string;
  checks: CheckResult[];
  evidence_bundle: EvidenceItem[];
  score: number;
  ai_generated?: boolean;
  error: string | null;
  job_id: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface HintResponse {
  tier: number;
  content: string;
  source: "ai" | "static";
  is_solution: boolean;
}

export type Provider = "anthropic" | "openai";

export interface ApiKeyStatus {
  configured: boolean;
  provider: Provider | null;
  masked_key: string | null;
  base_url: string | null;
  model: string | null;
  last_validated_at: string | null;
}

export interface DomainMastery {
  domain: string;
  tasks_total: number;
  tasks_passed: number;
  avg_score: number;
  highest_difficulty_cleared: number;
}

export interface ModuleProgress {
  module: string;
  tasks_total: number;
  tasks_passed: number;
}

export interface TaskStat {
  task_id: string;
  title: string;
  module: string;
  domain: string;
  difficulty: number;
  success_type: string;
  status: "passed" | "attempted" | "not_started";
  best_score: number;
  attempts: number;
  hint_tier_used: number;
  time_to_solve_sec: number | null;
  last_activity: string | null;
  passed_at: string | null;
}

export interface ProfileStats {
  display_name: string;
  tasks_passed: number;
  tasks_total: number;
  total_score: number;
  total_attempts: number;
  total_hints_used: number;
  tasks_attempted: number;
  completion_pct: number;
  pass_rate: number;
  avg_attempts_per_pass: number;
  highest_difficulty_cleared: number;
  avg_time_to_solve_min: number;
  masvs_covered: string[];
  first_active: string | null;
  last_active: string | null;
  domains: DomainMastery[];
  modules: ModuleProgress[];
  tasks: TaskStat[];
}

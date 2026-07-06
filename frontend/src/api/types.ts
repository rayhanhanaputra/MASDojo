// Shapes mirror the backend Pydantic models.

export interface UserPublic {
  id: number;
  email: string;
  display_name: string;
  created_at: string;
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

// A structured proof artifact backing the verdict (log, trace, timeline, note).
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
  last_validated_at: string | null;
}

export interface DomainMastery {
  domain: string;
  tasks_total: number;
  tasks_passed: number;
  avg_score: number;
  highest_difficulty_cleared: number;
}

export interface ProfileStats {
  display_name: string;
  tasks_passed: number;
  tasks_total: number;
  total_score: number;
  total_attempts: number;
  total_hints_used: number;
  domains: DomainMastery[];
}

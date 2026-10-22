export type RunStatus = 'pending' | 'planning' | 'running' | 'waiting_approval' | 'completed' | 'failed' | 'cancelled';

export type TaskStatus = 'pending' | 'ready' | 'running' | 'waiting_approval' | 'completed' | 'failed' | 'needs_review';

export type AgentRole = 'planner' | 'researcher' | 'developer' | 'analyst' | 'writer' | 'reviewer';

export interface Project {
  project_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface Run {
  run_id: string;
  project_id: string;
  goal: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  execution_time_seconds?: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  pending_approvals: number;
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface Task {
  task_id: string;
  run_id: string;
  title: string;
  role: AgentRole;
  goal: string;
  status: TaskStatus;
  depends_on: string[];
  acceptance_criteria: string[];
  requires_approval: boolean;
  assigned_model?: string;
  routing_reason?: string;
  router_confidence?: number;
  attempts: number;
  max_attempts: number;
  result_summary?: string;
  output_data?: any;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  execution_time_seconds?: number;
  created_at: string;
  updated_at: string;
}

export interface ModelInfo {
  model_id: string;
  name: string;
  provider: string;
  family: string;
  capabilities: string[];
  context_window: number;
  avg_latency_ms: number;
  cost_per_1k_tokens: number;
  is_local: boolean;
  is_available: boolean;
}

export interface ApprovalRequest {
  approval_id: string;
  run_id: string;
  task_id: string;
  action_type: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'approved' | 'rejected';
  payload: Record<string, any>;
  created_at: string;
  decided_at?: string;
  decided_by?: string;
  decision_reason?: string;
}

export interface Artifact {
  artifact_id: string;
  run_id: string;
  task_id: string;
  title: string;
  artifact_type: string;
  file_path?: string;
  content_snippet?: string;
  size_bytes: number;
  created_at: string;
  metadata: Record<string, any>;
}

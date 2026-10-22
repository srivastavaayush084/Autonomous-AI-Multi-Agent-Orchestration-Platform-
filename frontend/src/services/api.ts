import type { Project, Run, Task, ModelInfo, ApprovalRequest, Artifact } from '../types';

const BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    }
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error ${res.status}: ${errorText}`);
  }
  return res.json();
}

export const api = {
  // System Health
  async getHealth(): Promise<{ status: string; version: string; database: string; strategy: string }> {
    const res = await fetch(`${BASE_URL}/health`);
    return res.json();
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    return fetchJSON<Project[]>('/projects/');
  },

  async createProject(name: string, description: string): Promise<Project> {
    return fetchJSON<Project>('/projects/', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    });
  },

  async deleteProject(projectId: string): Promise<{ status: string; project_id: string }> {
    return fetchJSON<{ status: string; project_id: string }>(`/projects/${projectId}`, {
      method: 'DELETE'
    });
  },

  // Runs
  async getRuns(projectId?: string): Promise<Run[]> {
    const q = projectId ? `?project_id=${projectId}` : '';
    return fetchJSON<Run[]>(`/runs/${q}`);
  },

  async getRun(runId: string): Promise<Run> {
    return fetchJSON<Run>(`/runs/${runId}`);
  },

  async createRun(projectId: string, goal: string): Promise<Run> {
    return fetchJSON<Run>('/runs/', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, goal })
    });
  },

  async resumeRun(runId: string): Promise<Run> {
    return fetchJSON<Run>(`/runs/${runId}/resume`, {
      method: 'POST'
    });
  },

  async getRunTasks(runId: string): Promise<Task[]> {
    return fetchJSON<Task[]>(`/runs/${runId}/tasks`);
  },

  // Models
  async getModels(): Promise<ModelInfo[]> {
    return fetchJSON<ModelInfo[]>('/models/');
  },

  async getModelStatus(): Promise<any> {
    return fetchJSON<any>('/models/status');
  },

  // Approvals
  async getApprovals(runId?: string): Promise<ApprovalRequest[]> {
    const q = runId ? `?run_id=${runId}` : '';
    return fetchJSON<ApprovalRequest[]>(`/approvals/${q}`);
  },

  async decideApproval(approvalId: string, decision: 'approved' | 'rejected', reason: string): Promise<ApprovalRequest> {
    return fetchJSON<ApprovalRequest>(`/approvals/${approvalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason })
    });
  },

  // Artifacts
  async getArtifacts(runId?: string): Promise<Artifact[]> {
    const q = runId ? `?run_id=${runId}` : '';
    return fetchJSON<Artifact[]>(`/artifacts/${q}`);
  },

  // RAG & Project Memory
  async ingestDocument(doc: {
    project_id: string;
    title: string;
    content: string;
    document_type?: string;
    allowed_roles?: string[];
    visibility?: string;
  }): Promise<any> {
    return fetchJSON<any>('/rag/ingest', {
      method: 'POST',
      body: JSON.stringify(doc)
    });
  },

  async queryMemory(params: {
    project_id: string;
    query: string;
    role?: string;
    top_k?: number;
    min_similarity?: number;
  }): Promise<any> {
    return fetchJSON<any>('/rag/query', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async getProjectDocuments(projectId: string): Promise<any[]> {
    return fetchJSON<any[]>(`/rag/documents/${projectId}`);
  },

  async deleteDocument(projectId: string, documentId: string): Promise<any> {
    return fetchJSON<any>(`/rag/documents/${projectId}/${documentId}`, {
      method: 'DELETE'
    });
  }
};

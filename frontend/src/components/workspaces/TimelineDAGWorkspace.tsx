import React from 'react';
import { GitBranch, RefreshCw, X } from 'lucide-react';
import type { Run, Task } from '../../types';
import { TaskDAGViewer } from '../TaskDAGViewer';

interface TimelineDAGWorkspaceProps {
  runs: Run[];
  activeRun: Run | null;
  tasks: Task[];
  onSelectRun: (runId: string) => void;
  onRefresh: () => void;
  onCancelRun: (runId: string) => void;
  onViewArtifacts: (taskId: string) => void;
}

export const TimelineDAGWorkspace: React.FC<TimelineDAGWorkspaceProps> = ({
  runs,
  activeRun,
  tasks,
  onSelectRun,
  onRefresh,
  onCancelRun,
  onViewArtifacts,
}) => {
  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <GitBranch size={24} color="#c084fc" />
            Agent Execution Timeline & DAG Orchestrator
          </div>
          <div className="workspace-subtitle">
            Dynamic dependency graph with state checkpoints, model assignments, execution durations, and retry semantics.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {activeRun && (activeRun.status === 'running' || activeRun.status === 'planning') && (
            <button
              className="btn-reject"
              onClick={() => onCancelRun(activeRun.run_id)}
            >
              <X size={14} style={{ display: 'inline', marginRight: 4 }} /> Cancel Run
            </button>
          )}
          <button
            className="btn-new-chat"
            onClick={onRefresh}
            style={{ padding: '8px 16px' }}
          >
            <RefreshCw size={14} /> Refresh DAG
          </button>
        </div>
      </div>

      {/* Run Selector & Active Run Stats */}
      {runs.length > 0 && (
        <div className="workspace-panel" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Inspect Task Run:
            </span>
            <select
              className="form-select"
              value={activeRun?.run_id || ''}
              onChange={e => onSelectRun(e.target.value)}
              style={{ minWidth: '280px' }}
            >
              {runs.map(r => (
                <option key={r.run_id} value={r.run_id}>
                  [{r.status.toUpperCase()}] {r.goal.slice(0, 50)} ({r.run_id.slice(0, 8)})
                </option>
              ))}
            </select>
          </div>

          {activeRun && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span className={`badge badge-${activeRun.status}`}>{activeRun.status}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Total Tasks: <strong>{activeRun.total_tasks}</strong>
              </span>
              <span style={{ fontSize: '0.8rem', color: '#34d399' }}>
                Completed: <strong>{activeRun.completed_tasks}</strong>
              </span>
              {activeRun.execution_time_seconds && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Duration: <strong>{activeRun.execution_time_seconds.toFixed(1)}s</strong>
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* DAG Visualization */}
      <div className="workspace-panel" style={{ padding: '24px' }}>
        <TaskDAGViewer tasks={tasks} onViewArtifacts={onViewArtifacts} />
      </div>
    </div>
  );
};

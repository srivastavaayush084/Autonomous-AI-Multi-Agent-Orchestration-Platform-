import React, { useState } from 'react';
import type { Task } from '../types';
import { CheckCircle2, Clock, AlertTriangle, ArrowRight, ShieldAlert, Cpu, Eye, CheckSquare, Play } from 'lucide-react';
import { api } from '../services/api';

interface TaskDAGViewerProps {
  tasks: Task[];
  onViewArtifacts: (taskId: string) => void;
}

export const TaskDAGViewer: React.FC<TaskDAGViewerProps> = ({ tasks, onViewArtifacts }) => {
  const [expandedTask, setExpandedTask] = useState<string | null>(null);

  if (tasks.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center' }}>
        <Cpu size={48} color="#6366f1" style={{ opacity: 0.6, marginBottom: '16px' }} />
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>No Tasks in Orchestration Graph</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>
          Select or launch a run to inspect autonomous task decomposition, dependency resolution, and agent execution.
        </p>
      </div>
    );
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'planner': return { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.3)' };
      case 'researcher': return { bg: 'rgba(6, 182, 212, 0.15)', text: '#22d3ee', border: 'rgba(6, 182, 212, 0.3)' };
      case 'developer': return { bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8', border: 'rgba(99, 102, 241, 0.3)' };
      case 'reviewer': return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: 'rgba(16, 185, 129, 0.3)' };
      default: return { bg: 'rgba(148, 163, 184, 0.15)', text: '#94a3b8', border: 'rgba(148, 163, 184, 0.3)' };
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 size={16} color="#34d399" />;
      case 'running': return <Clock size={16} color="#38bdf8" className="animate-spin" />;
      case 'waiting_approval': return <ShieldAlert size={16} color="#fbbf24" />;
      case 'failed': return <AlertTriangle size={16} color="#fb7185" />;
      default: return <Clock size={16} color="#94a3b8" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Task Execution DAG & Agent Pipeline</h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Sequential and parallel dependency graph orchestrated with state checkpoints
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-completed">{tasks.filter(t => t.status === 'completed').length} Done</span>
          <span className="badge badge-running">{tasks.filter(t => t.status === 'running').length} Active</span>
          <span className="badge badge-waiting_approval">{tasks.filter(t => t.status === 'waiting_approval').length} Gated</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {tasks.map((task, index) => {
          const roleStyle = getRoleColor(task.role);
          const isExpanded = expandedTask === task.task_id;

          return (
            <div
              key={task.task_id}
              className={`glass-panel ${task.status === 'running' ? 'glass-panel-glow' : ''}`}
              style={{
                padding: '18px 22px',
                borderLeft: `4px solid ${
                  task.status === 'completed' ? '#10b981' :
                  task.status === 'running' ? '#06b6d4' :
                  task.status === 'waiting_approval' ? '#f59e0b' :
                  task.status === 'failed' ? '#f43f5e' : 'rgba(255,255,255,0.2)'
                }`
              }}
            >
              {/* Header Row */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.06)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    color: 'var(--text-secondary)'
                  }}>
                    {index + 1}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                        {task.title}
                      </h4>
                      <span style={{
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: roleStyle.bg,
                        color: roleStyle.text,
                        border: `1px solid ${roleStyle.border}`,
                        fontWeight: 700,
                        textTransform: 'uppercase'
                      }}>
                        {task.role}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} className="font-mono">
                      ID: {task.task_id}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  {/* Model Routing Badge */}
                  {task.assigned_model && (
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-end',
                      background: 'rgba(0,0,0,0.3)',
                      padding: '4px 10px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-subtle)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Cpu size={12} color="#818cf8" />
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#c7d2fe' }} className="font-mono">
                          {task.assigned_model.split('/')[1] || task.assigned_model}
                        </span>
                      </div>
                      {task.router_confidence && (
                        <span style={{ fontSize: '0.65rem', color: '#10b981', fontWeight: 600 }}>
                          ML Match {(task.router_confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  )}

                  {/* Status Badge */}
                  <div className={`badge badge-${task.status}`}>
                    {getStatusIcon(task.status)}
                    <span>{task.status.replace('_', ' ')}</span>
                  </div>

                  {task.status === 'ready' && (
                    <button
                      className="btn-primary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        background: 'linear-gradient(135deg, #10b981, #059669)',
                        border: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                      onClick={async (e) => {
                        e.stopPropagation();
                        await api.resumeRun(task.run_id);
                      }}
                    >
                      <Play size={12} />
                      <span>Execute</span>
                    </button>
                  )}

                  <button
                    className="btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                    onClick={() => setExpandedTask(isExpanded ? null : task.task_id)}
                  >
                    {isExpanded ? 'Collapse' : 'Details'}
                  </button>
                </div>
              </div>

              {/* Goal Description */}
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '12px', lineHeight: '1.5' }}>
                {task.goal}
              </p>

              {/* Dependency indicator */}
              {task.depends_on.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
                  <ArrowRight size={14} color="#64748b" />
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Prerequisites:</span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {task.depends_on.map(dep => (
                      <span
                        key={dep}
                        className="font-mono"
                        style={{ fontSize: '0.7rem', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px', color: '#94a3b8' }}
                      >
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Expanded Inspection Pane */}
              {isExpanded && (
                <div style={{
                  marginTop: '16px',
                  paddingTop: '16px',
                  borderTop: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}>
                  {/* Routing Rationale */}
                  {task.routing_reason && (
                    <div style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.25)', padding: '10px 14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', marginBottom: '2px' }}>
                        ROUTING DECISION RATIONALE:
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {task.routing_reason}
                      </p>
                    </div>
                  )}

                  {/* Acceptance Criteria Checklist */}
                  {task.acceptance_criteria && task.acceptance_criteria.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px' }}>
                        VERIFIABLE ACCEPTANCE CRITERIA:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {task.acceptance_criteria.map((crit, i) => (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: '#e2e8f0' }}>
                            <CheckSquare size={14} color="#10b981" />
                            <span>{crit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Output Data / Artifact */}
                  {task.output_data && (
                    <div style={{ marginTop: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                          AGENT DELIVERABLE PAYLOAD:
                        </span>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                          onClick={() => onViewArtifacts(task.task_id)}
                        >
                          <Eye size={12} />
                          <span>View Full Artifact</span>
                        </button>
                      </div>
                      <pre className="font-mono" style={{
                        background: '#040711',
                        border: '1px solid rgba(255,255,255,0.06)',
                        borderRadius: '8px',
                        padding: '12px',
                        fontSize: '0.78rem',
                        color: '#38bdf8',
                        overflowX: 'auto',
                        maxHeight: '180px'
                      }}>
                        {JSON.stringify(task.output_data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

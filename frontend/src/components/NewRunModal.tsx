import React, { useState } from 'react';
import type { Project } from '../types';
import { Play, X, Sparkles, FolderPlus } from 'lucide-react';

interface NewRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  projects: Project[];
  onSubmit: (projectId: string, goal: string) => Promise<void>;
  onCreateProject: (name: string, description: string) => Promise<Project>;
}

export const NewRunModal: React.FC<NewRunModalProps> = ({
  isOpen,
  onClose,
  projects,
  onSubmit,
  onCreateProject
}) => {
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.project_id || '');
  const [goal, setGoal] = useState<string>('');
  const [isCreatingNewProj, setIsCreatingNewProj] = useState<boolean>(false);
  const [newProjName, setNewProjName] = useState<string>('');
  const [newProjDesc, setNewProjDesc] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setSubmitting(true);
    try {
      let targetProjectId = selectedProjectId;
      if (isCreatingNewProj && newProjName.trim()) {
        const created = await onCreateProject(newProjName.trim(), newProjDesc.trim());
        targetProjectId = created.project_id;
      } else if (!targetProjectId && projects.length > 0) {
        targetProjectId = projects[0].project_id;
      }

      await onSubmit(targetProjectId, goal.trim());
      setGoal('');
      onClose();
    } catch (err) {
      alert(`Error launching run: ${err}`);
    } finally {
      setSubmitting(false);
    }
  };

  const presetGoals = [
    "Design and generate a secure microservices architecture with Redis cache and MongoDB Atlas schemas.",
    "Perform automated security audit, dependency risk assessment, and verification test suite generation.",
    "Formulate an enterprise multi-agent workflow for financial risk telemetry and predictive model routing."
  ];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(4, 7, 17, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '640px', padding: '28px', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Sparkles size={22} color="#6366f1" />
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }} className="text-gradient">
            Launch Autonomous Agent Run
          </h2>
        </div>
        <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Specify your high-level goal. The Planner Agent will decompose it into a verifiable task DAG and route specialist workers.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Project Selection / Creation Toggle */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#e2e8f0' }}>Target Project</label>
              <button
                type="button"
                onClick={() => setIsCreatingNewProj(!isCreatingNewProj)}
                style={{ fontSize: '0.78rem', color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <FolderPlus size={14} />
                <span>{isCreatingNewProj ? 'Select Existing' : '+ New Project'}</span>
              </button>
            </div>

            {isCreatingNewProj ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Project Name (e.g. Trendtide Distributed Engine)"
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  style={{
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    color: '#f8fafc',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                  required
                />
                <input
                  type="text"
                  placeholder="Brief description"
                  value={newProjDesc}
                  onChange={(e) => setNewProjDesc(e.target.value)}
                  style={{
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '8px 14px',
                    color: '#f8fafc',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
              </div>
            ) : (
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                style={{
                  width: '100%',
                  background: 'rgba(0,0,0,0.3)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  color: '#f8fafc',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              >
                {projects.map((p) => (
                  <option key={p.project_id} value={p.project_id} style={{ background: '#090d16' }}>
                    {p.name} ({p.project_id})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Goal Input */}
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
              Autonomous Goal Specification
            </label>
            <textarea
              rows={4}
              placeholder="e.g. Conduct a comprehensive security audit of our microservice API, formulate a mitigation architecture, and generate test scripts."
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(0,0,0,0.35)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '12px 14px',
                color: '#f8fafc',
                fontSize: '0.9rem',
                lineHeight: '1.5',
                outline: 'none',
                resize: 'vertical'
              }}
              required
            />
          </div>

          {/* Quick Presets */}
          <div>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              RECOMMENDED PRESET GOALS:
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {presetGoals.map((p, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => setGoal(p)}
                  style={{
                    textAlign: 'left',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-subtle)',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    color: 'var(--text-secondary)',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = '#38bdf8')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
                >
                  "{p}"
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              <Play size={16} />
              <span>{submitting ? 'Decomposing Goal...' : 'Start Orchestration'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

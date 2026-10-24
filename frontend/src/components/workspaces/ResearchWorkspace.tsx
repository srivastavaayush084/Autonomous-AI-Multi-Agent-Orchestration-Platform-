import React, { useState } from 'react';
import { FileText, Zap, Download, CheckCircle, X } from 'lucide-react';
import type { Run, Task, Artifact } from '../../types';

interface ResearchWorkspaceProps {
  projectId: string;
  onLaunchTask: (goal: string) => Promise<void>;
  activeRun: Run | null;
  activeTasks: Task[];
  activeArtifacts: Artifact[];
  isProcessing: boolean;
  onCancelRun: (runId: string) => void;
}

export const ResearchWorkspace: React.FC<ResearchWorkspaceProps> = ({
  projectId: _projectId,
  onLaunchTask,
  activeRun,
  activeTasks,
  activeArtifacts,
  isProcessing,
  onCancelRun,
}) => {
  const [topic, setTopic] = useState('');
  const [academicFocus, setAcademicFocus] = useState('comprehensive');
  const [includeCitations, setIncludeCitations] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || isProcessing) return;

    const prompt = `Create a rigorous ${academicFocus} research paper on "${topic.trim()}" with formal methodology, problem statement, technical analysis, and valid citations. Provide complete DOCX and PDF deliverables.`;
    onLaunchTask(prompt);
  };

  const docxArtifact = activeArtifacts.find(a => a.artifact_type === 'docx' || a.title.toLowerCase().endsWith('.docx'));
  const pdfArtifact = activeArtifacts.find(a => a.artifact_type === 'pdf' || a.title.toLowerCase().endsWith('.pdf'));

  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <FileText size={24} color="#818cf8" />
            Autonomous Research & Report Generator
          </div>
          <div className="workspace-subtitle">
            Multi-agent academic research engine: literature synthesis, evidence verification, and publication-ready DOCX & PDF generation.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '24px' }}>
        {/* Left: Configuration Form */}
        <div className="workspace-panel">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Research Topic or Hypothesis</label>
              <textarea
                className="form-textarea"
                placeholder="e.g., AI-based zero-day attack detection using graph neural networks and behavioral heuristics..."
                value={topic}
                onChange={e => setTopic(e.target.value)}
                disabled={isProcessing}
                style={{ height: '120px' }}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Academic Depth & Scope</label>
              <select
                className="form-select"
                value={academicFocus}
                onChange={e => setAcademicFocus(e.target.value)}
                disabled={isProcessing}
              >
                <option value="comprehensive">Comprehensive Research Paper (Standard)</option>
                <option value="deep-dive">Technical Deep Dive & Architecture Review</option>
                <option value="comparative">Comparative State-of-the-Art Analysis</option>
                <option value="executive">Executive Intelligence & Strategic Report</option>
              </select>
            </div>

            <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
              <input
                type="checkbox"
                id="citations"
                checked={includeCitations}
                onChange={e => setIncludeCitations(e.target.checked)}
                disabled={isProcessing}
              />
              <label htmlFor="citations" style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                Require verified sources & DOI citations
              </label>
            </div>

            <button
              type="submit"
              className="btn-send"
              disabled={isProcessing || !topic.trim()}
              style={{ width: '100%', marginTop: '10px', height: '42px', justifyContent: 'center' }}
            >
              <Zap size={16} />
              {isProcessing ? 'Agent Fleet Researching…' : 'Generate Full Research Paper'}
            </button>
          </form>

          {isProcessing && activeRun && (
            <div style={{ marginTop: '16px', textAlign: 'center' }}>
              <button
                className="btn-reject"
                onClick={() => onCancelRun(activeRun.run_id)}
                style={{ width: '100%' }}
              >
                <X size={14} style={{ display: 'inline', marginRight: 4 }} />
                Cancel Research Run
              </button>
            </div>
          )}
        </div>

        {/* Right: Real-time Execution & Deliverables */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Active Status Banner */}
          {activeRun && (
            <div className="workspace-panel" style={{ borderLeft: '4px solid var(--accent-indigo)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                  Active Task Status
                </span>
                <span className={`badge badge-${activeRun.status}`}>{activeRun.status}</span>
              </div>
              <div style={{ fontSize: '0.92rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                {activeRun.goal}
              </div>

              {/* Task Steps */}
              {activeTasks.length > 0 && (
                <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {activeTasks.map(t => (
                    <div
                      key={t.task_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        background: 'rgba(0,0,0,0.2)',
                        borderRadius: '6px',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>{t.title}</span>
                      <span className={`badge badge-${t.status}`}>{t.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Generated Deliverables */}
          {activeArtifacts.length > 0 && (
            <div className="workspace-panel" style={{ border: '1px solid rgba(16, 185, 129, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: 700, marginBottom: '12px' }}>
                <CheckCircle size={18} />
                Publication Artifacts Ready
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {pdfArtifact && (
                  <a
                    href={`/api/v1/artifacts/${pdfArtifact.artifact_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-download btn-download-pdf"
                    style={{ textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download PDF Paper (Verified)
                  </a>
                )}
                {docxArtifact && (
                  <a
                    href={`/api/v1/artifacts/${docxArtifact.artifact_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-download btn-download-docx"
                    style={{ textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download Word DOCX (Verified)
                  </a>
                )}
              </div>

              {/* Text Preview */}
              <div style={{ marginTop: '16px' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px', textTransform: 'uppercase' }}>
                  Artifact Content Preview:
                </div>
                <div style={{
                  maxHeight: '260px',
                  overflowY: 'auto',
                  padding: '12px',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  lineHeight: '1.6',
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-wrap',
                }}>
                  {activeArtifacts[0].full_content || activeArtifacts[0].content_snippet || 'No text preview available'}
                </div>
              </div>
            </div>
          )}

          {!activeRun && activeArtifacts.length === 0 && (
            <div className="workspace-panel" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <FileText size={42} style={{ opacity: 0.4, margin: '0 auto 12px' }} />
              <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Ready for Research Generation</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                Enter your research topic on the left to generate fully referenced academic papers.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

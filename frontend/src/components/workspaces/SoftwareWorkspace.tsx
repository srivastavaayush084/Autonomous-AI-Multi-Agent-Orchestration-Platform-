import React, { useState } from 'react';
import { Code2, Zap, Download, Package, X } from 'lucide-react';
import type { Run, Task, Artifact } from '../../types';

interface SoftwareWorkspaceProps {
  projectId: string;
  onLaunchTask: (goal: string) => Promise<void>;
  activeRun: Run | null;
  activeTasks: Task[];
  activeArtifacts: Artifact[];
  isProcessing: boolean;
  onCancelRun: (runId: string) => void;
}

export const SoftwareWorkspace: React.FC<SoftwareWorkspaceProps> = ({
  projectId: _projectId,
  onLaunchTask,
  activeRun,
  activeTasks,
  activeArtifacts,
  isProcessing,
  onCancelRun,
}) => {
  const [appName, setAppName] = useState('modern-dashboard-app');
  const [techStack, setTechStack] = useState('react-vite');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || isProcessing) return;

    const prompt = `Build a complete ${techStack === 'react-vite' ? 'React + Vite' : techStack === 'vanilla' ? 'HTML5/CSS3/JavaScript' : 'Python backend'} project named "${appName}". Requirements: ${description.trim()}. Include full directory tree, package manifest, configuration, test scripts, and README. Packaged into a downloadable ZIP archive.`;
    onLaunchTask(prompt);
  };

  const zipArtifact = activeArtifacts.find(a => a.artifact_type === 'zip' || a.title.toLowerCase().includes('zip'));

  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <Code2 size={24} color="#06b6d4" />
            Website & Software Builder Studio
          </div>
          <div className="workspace-subtitle">
            Autonomous multi-agent development pipeline: generates complete source trees, dependencies, manifests, verified builds, and packaged ZIP archives.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '24px' }}>
        {/* Left: Configuration Form */}
        <div className="workspace-panel">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Project / Application Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., ai-portfolio-suite"
                value={appName}
                onChange={e => setAppName(e.target.value)}
                disabled={isProcessing}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Technology Stack</label>
              <select
                className="form-select"
                value={techStack}
                onChange={e => setTechStack(e.target.value)}
                disabled={isProcessing}
              >
                <option value="react-vite">React 18 + Vite + TypeScript (Modern Single Page App)</option>
                <option value="vanilla">Vanilla HTML5 + Modern CSS + ES6 JavaScript</option>
                <option value="python">Python FastAPI Backend + CLI Suite</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Specification & Features</label>
              <textarea
                className="form-textarea"
                placeholder="e.g., A developer portfolio with hero banner, interactive project cards, skills grid, contact form, dark mode toggle, and smooth animations..."
                value={description}
                onChange={e => setDescription(e.target.value)}
                disabled={isProcessing}
                style={{ height: '140px' }}
                required
              />
            </div>

            <button
              type="submit"
              className="btn-send"
              disabled={isProcessing || !description.trim()}
              style={{ width: '100%', marginTop: '10px', height: '42px', justifyContent: 'center' }}
            >
              <Zap size={16} />
              {isProcessing ? 'Generating & Packaging Project…' : 'Build & Package Complete App'}
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
                Cancel Build Run
              </button>
            </div>
          )}
        </div>

        {/* Right: Real-time Execution & ZIP Deliverable */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {activeRun && (
            <div className="workspace-panel" style={{ borderLeft: '4px solid var(--accent-cyan)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                  Autonomous Builder Status
                </span>
                <span className={`badge badge-${activeRun.status}`}>{activeRun.status}</span>
              </div>
              <div style={{ fontSize: '0.92rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                {activeRun.goal}
              </div>

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

          {/* Generated ZIP Artifact */}
          {zipArtifact && (
            <div className="workspace-panel" style={{ border: '1px solid rgba(6, 182, 212, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#22d3ee', fontWeight: 700 }}>
                  <Package size={20} />
                  Complete Application ZIP Built
                </div>
                <a
                  href={`/api/v1/artifacts/${zipArtifact.artifact_id}/download`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-download btn-download-zip"
                  style={{ textDecoration: 'none' }}
                >
                  <Download size={14} /> Download {zipArtifact.title}
                </a>
              </div>

              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Package verified. Contains complete package.json, source files, styling, and README instructions.
              </div>

              <div style={{
                background: 'var(--bg-code)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '12px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
                color: 'var(--text-code)',
              }}>
                <div># How to run locally:</div>
                <div style={{ color: '#fff', marginTop: '4px' }}>1. Unzip the downloaded file</div>
                <div style={{ color: '#fff' }}>2. cd {appName}</div>
                <div style={{ color: '#38bdf8' }}>3. npm install && npm run dev</div>
              </div>
            </div>
          )}

          {!activeRun && !zipArtifact && (
            <div className="workspace-panel" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <Code2 size={42} style={{ opacity: 0.4, margin: '0 auto 12px' }} />
              <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Ready for Software Generation</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                Configure your software specifications on the left to generate complete, runnable source projects.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

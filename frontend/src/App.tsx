import React, { useState, useEffect } from 'react';
import type { Project, Run, Task, ModelInfo, ApprovalRequest, Artifact } from './types';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { TaskDAGViewer } from './components/TaskDAGViewer';
import { NewRunModal } from './components/NewRunModal';
import { ApprovalsDrawer } from './components/ApprovalsDrawer';
import { ArtifactsModal } from './components/ArtifactsModal';
import { ModelRegistryPanel } from './components/ModelRegistryPanel';
import { Folder, Layers, Clock, Play } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; database: string; strategy: string } | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);

  // Modal / Drawer UI states
  const [isNewRunOpen, setIsNewRunOpen] = useState<boolean>(false);
  const [isApprovalsOpen, setIsApprovalsOpen] = useState<boolean>(false);
  const [isArtifactsOpen, setIsArtifactsOpen] = useState<boolean>(false);
  const [filterArtifactTaskId, setFilterArtifactTaskId] = useState<string | null>(null);

  // Initial Data Fetch
  const loadInitialData = async () => {
    try {
      const [h, projs, mods, appr] = await Promise.all([
        api.getHealth().catch(() => ({ status: 'online', version: '1.0.0', database: 'connected', strategy: 'ml_hybrid' })),
        api.getProjects().catch(() => []),
        api.getModels().catch(() => []),
        api.getApprovals().catch(() => [])
      ]);
      setHealth(h);
      setProjects(projs);
      setModels(mods);
      setApprovals(appr);

      if (projs.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projs[0].project_id);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Poll for runs and tasks
  useEffect(() => {
    const fetchRunsAndTasks = async () => {
      try {
        const fetchedRuns = await api.getRuns(selectedProjectId || undefined);
        setRuns(fetchedRuns);

        if (!selectedRunId && fetchedRuns.length > 0) {
          setSelectedRunId(fetchedRuns[0].run_id);
        }

        if (selectedRunId) {
          const fetchedTasks = await api.getRunTasks(selectedRunId);
          setTasks(fetchedTasks);
        }

        const [fetchedApprovals, fetchedArtifacts] = await Promise.all([
          api.getApprovals(selectedRunId || undefined),
          api.getArtifacts(selectedRunId || undefined)
        ]);
        setApprovals(fetchedApprovals);
        setArtifacts(fetchedArtifacts);
      } catch (err) {
        // Silently catch polling issues
      }
    };

    fetchRunsAndTasks();
    const timer = setInterval(fetchRunsAndTasks, 2500);
    return () => clearInterval(timer);
  }, [selectedProjectId, selectedRunId]);

  const activeRun = runs.find(r => r.run_id === selectedRunId);

  const handleLaunchRun = async (projectId: string, goal: string) => {
    const createdRun = await api.createRun(projectId, goal);
    setSelectedProjectId(projectId);
    setSelectedRunId(createdRun.run_id);
    const updatedRuns = await api.getRuns(projectId);
    setRuns(updatedRuns);
  };

  const handleCreateProject = async (name: string, description: string) => {
    const proj = await api.createProject(name, description);
    setProjects([proj, ...projects]);
    setSelectedProjectId(proj.project_id);
    return proj;
  };

  const handleDecideApproval = async (approvalId: string, decision: 'approved' | 'rejected', reason: string) => {
    await api.decideApproval(approvalId, decision, reason);
    if (selectedRunId) {
      const [fetchedTasks, fetchedApprovals] = await Promise.all([
        api.getRunTasks(selectedRunId),
        api.getApprovals(selectedRunId)
      ]);
      setTasks(fetchedTasks);
      setApprovals(fetchedApprovals);
    }
  };

  const handleOpenArtifacts = (taskId?: string) => {
    setFilterArtifactTaskId(taskId || null);
    setIsArtifactsOpen(true);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <Navbar
        systemHealth={health}
        pendingApprovalsCount={approvals.filter(a => a.status === 'pending').length}
        onOpenNewRun={() => setIsNewRunOpen(true)}
        onOpenApprovals={() => setIsApprovalsOpen(true)}
      />

      {/* Main Workspace Layout */}
      <div style={{ display: 'flex', flex: 1, padding: '0 24px 24px 24px', gap: '20px' }}>
        {/* Left Sidebar: Projects & Runs */}
        <aside style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Projects Panel */}
          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Folder size={16} color="#818cf8" />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Projects</h3>
              </div>
              <span className="badge badge-pending">{projects.length}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {projects.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', padding: '10px 0' }}>
                  No projects created yet. Click "+ New" below to create one.
                </div>
              ) : (
                projects.map(p => (
                  <button
                    key={p.project_id}
                    onClick={() => {
                      setSelectedProjectId(p.project_id);
                      setSelectedRunId('');
                    }}
                    style={{
                      textAlign: 'left',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      background: selectedProjectId === p.project_id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${selectedProjectId === p.project_id ? 'rgba(99, 102, 241, 0.4)' : 'transparent'}`,
                      color: selectedProjectId === p.project_id ? '#f8fafc' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{p.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }} className="font-mono">
                      {p.project_id}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Runs History Panel */}
          <div className="glass-panel" style={{ padding: '18px', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={16} color="#06b6d4" />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700 }}>Runs History</h3>
              </div>
              <button
                className="btn-secondary"
                style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                onClick={() => setIsNewRunOpen(true)}
              >
                + New
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto' }}>
              {runs.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', padding: '10px 0' }}>
                  No runs executed yet. Click "+ New" to begin.
                </div>
              ) : (
                runs.map(r => (
                  <button
                    key={r.run_id}
                    onClick={() => setSelectedRunId(r.run_id)}
                    style={{
                      textAlign: 'left',
                      padding: '12px',
                      borderRadius: '8px',
                      background: selectedRunId === r.run_id ? 'rgba(6, 182, 212, 0.18)' : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${selectedRunId === r.run_id ? 'rgba(6, 182, 212, 0.4)' : 'transparent'}`,
                      color: selectedRunId === r.run_id ? '#f8fafc' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.run_id}</span>
                      <span className={`badge badge-${r.status}`} style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                        {r.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f1f5f9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.goal}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      <span>{r.completed_tasks}/{r.total_tasks} Tasks Done</span>
                      {r.execution_time_seconds && <span>{r.execution_time_seconds.toFixed(1)}s</span>}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </aside>

        {/* Center Main Stage */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Active Run Header Banner */}
          {activeRun && (
            <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="font-mono" style={{ fontSize: '0.78rem', color: '#38bdf8' }}>{activeRun.run_id}</span>
                  <div className={`badge badge-${activeRun.status}`}>
                    <span>{activeRun.status.toUpperCase()}</span>
                  </div>
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '6px', color: '#f8fafc' }}>
                  {activeRun.goal}
                </h2>
                <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  <span>Created: {new Date(activeRun.created_at).toLocaleTimeString()}</span>
                  {activeRun.execution_time_seconds && (
                    <span>Duration: <strong style={{ color: '#34d399' }}>{activeRun.execution_time_seconds.toFixed(2)}s</strong></span>
                  )}
                  <span>Completed: {activeRun.completed_tasks} of {activeRun.total_tasks} tasks</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                {activeRun && activeRun.status !== 'completed' && activeRun.status !== 'failed' && (
                  <button
                    className="btn-primary"
                    style={{ background: 'linear-gradient(135deg, #06b6d4, #6366f1)', border: 'none' }}
                    onClick={async () => {
                      await api.resumeRun(activeRun.run_id);
                      const [fetchedTasks, fetchedRuns] = await Promise.all([
                        api.getRunTasks(activeRun.run_id),
                        api.getRuns(selectedProjectId || undefined)
                      ]);
                      setTasks(fetchedTasks);
                      setRuns(fetchedRuns);
                    }}
                  >
                    <Play size={16} />
                    <span>Resume Execution</span>
                  </button>
                )}
                <button className="btn-secondary" onClick={() => handleOpenArtifacts()}>
                  <Layers size={16} />
                  <span>View Deliverables ({artifacts.length})</span>
                </button>
              </div>
            </div>
          )}

          {/* Interactive DAG Task Graph */}
          <TaskDAGViewer tasks={tasks} onViewArtifacts={(tId) => handleOpenArtifacts(tId)} />

          {/* Model Registry & Hybrid Fleet */}
          <ModelRegistryPanel models={models} />
        </main>
      </div>

      {/* Modals & Drawers */}
      <NewRunModal
        isOpen={isNewRunOpen}
        onClose={() => setIsNewRunOpen(false)}
        projects={projects}
        onSubmit={handleLaunchRun}
        onCreateProject={handleCreateProject}
      />

      <ApprovalsDrawer
        isOpen={isApprovalsOpen}
        onClose={() => setIsApprovalsOpen(false)}
        approvals={approvals}
        onDecide={handleDecideApproval}
      />

      <ArtifactsModal
        isOpen={isArtifactsOpen}
        onClose={() => setIsArtifactsOpen(false)}
        artifacts={artifacts}
        filterTaskId={filterArtifactTaskId}
      />
    </div>
  );
};

export default App;

import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { Project, Run, Task, ApprovalRequest, Artifact } from './types';
import { api } from './services/api';
import {
  Send, Plus, Layers, CheckCircle, XCircle, Clock, Bot,
  User, Copy, Check, Download, FileText, Code2, Zap,
  AlertTriangle, RotateCcw, ChevronRight
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ChatSession {
  id: string;           // run_id
  projectId: string;
  title: string;
  status: Run['status'];
  createdAt: string;
}

type MessageType = 'user' | 'agent' | 'system';

interface ChatMessage {
  id: string;
  type: MessageType;
  content: string;
  timestamp: string;
  runId?: string;
  tasks?: Task[];
  artifacts?: Artifact[];
  approvals?: ApprovalRequest[];
  isComplete?: boolean;
  isTyping?: boolean;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  researcher: 'Researcher',
  developer: 'Developer',
  writer: 'Writer',
  analyst: 'Analyst',
  reviewer: 'Reviewer',
  planner: 'Planner',
};

const SUGGESTIONS = [
  { emoji: '📄', title: 'Research Paper', desc: 'Write a detailed research paper on quantum computing', prompt: 'Write a comprehensive research paper on the latest advances in quantum computing, including key algorithms, hardware developments, and future prospects.' },
  { emoji: '🌐', title: 'Build a Website', desc: 'Create a complete landing page with HTML/CSS/JS', prompt: 'Build a complete responsive landing page for a SaaS product. Include HTML, CSS, and JavaScript files with hero section, features, pricing, and contact form.' },
  { emoji: '📊', title: 'Market Analysis', desc: 'Analyze a market and produce a detailed report', prompt: 'Conduct a comprehensive market analysis for the electric vehicle industry. Include market size, key players, growth trends, SWOT analysis, and investment opportunities.' },
  { emoji: '🤖', title: 'Python Script', desc: 'Generate a complete Python automation script', prompt: 'Write a complete Python script that scrapes job listings from a website, filters them by keywords, and exports results to a CSV file with proper error handling.' },
];

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function detectContentType(content: string): 'code' | 'text' {
  const codePatterns = [/^```/, /def\s+\w+\(/, /function\s+\w+/, /<!DOCTYPE/, /<html/i, /import\s+\w+/, /class\s+\w+/];
  return codePatterns.some(p => p.test(content.trim())) ? 'code' : 'text';
}

function stripCodeFences(content: string): string {
  return content.replace(/^```[\w]*\n?/m, '').replace(/```$/m, '').trim();
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const StepIcon: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, React.ReactNode> = {
    completed: '✓',
    running: '↻',
    failed: '✗',
    waiting_approval: '⏳',
    pending: '○',
    ready: '○',
  };
  return (
    <span className={`step-icon ${status}`} title={status}>
      {map[status] ?? '○'}
    </span>
  );
};

const AgentProgress: React.FC<{ tasks: Task[] }> = ({ tasks }) => {
  if (!tasks.length) return null;
  return (
    <div className="agent-progress fade-in">
      <div className="agent-progress-header">
        <Zap size={13} />
        Agent Pipeline — {tasks.filter(t => t.status === 'completed').length}/{tasks.length} complete
      </div>
      {tasks.map(task => (
        <div key={task.task_id} className={`agent-step ${task.status}`}>
          <StepIcon status={task.status} />
          <span className="step-label">{task.title}</span>
          <span className={`step-role role-${task.role}`}>{ROLE_LABELS[task.role] ?? task.role}</span>
          {task.execution_time_seconds && (
            <span className="step-time">{task.execution_time_seconds.toFixed(1)}s</span>
          )}
        </div>
      ))}
    </div>
  );
};

interface OutputCardProps {
  artifacts: Artifact[];
}

const OutputCard: React.FC<OutputCardProps> = ({ artifacts }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!artifacts.length) return null;

  const current = artifacts[activeTab];
  const content = (current as any).full_content || current.content_snippet || '';
  const contentType = detectContentType(content);
  const displayContent = contentType === 'code' ? stripCodeFences(content) : content;

  const handleCopy = () => {
    navigator.clipboard.writeText(displayContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAs = (ext: string, mimeType: string) => {
    const cleanTitle = current.title.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
    const blob = new Blob([displayContent], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${cleanTitle}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const pdfArtifact = artifacts.find(a => a.artifact_type === 'pdf' || a.title.toLowerCase().endsWith('.pdf'));
  const docxArtifact = artifacts.find(a => a.artifact_type === 'docx' || a.title.toLowerCase().endsWith('.docx'));
  const zipArtifact = artifacts.find(a => a.artifact_type === 'zip' || a.title.toLowerCase().includes('zip'));

  const downloadPDF = () => {
    if (pdfArtifact) {
      window.location.href = `/api/v1/artifacts/${pdfArtifact.artifact_id}/download`;
      return;
    }
    // Fallback print-to-PDF via new window
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`<!DOCTYPE html>
<html>
<head>
  <title>${current.title}</title>
  <style>
    body { font-family: Georgia, serif; max-width: 800px; margin: 40px auto; line-height: 1.8; color: #1a1a1a; font-size: 13pt; }
    h1 { font-size: 22pt; border-bottom: 2px solid #333; padding-bottom: 10px; }
    pre { background: #f5f5f5; padding: 16px; border-radius: 8px; font-size: 11pt; overflow-x: auto; }
    code { font-family: 'Courier New', monospace; }
  </style>
</head>
<body>
<h1>${current.title}</h1>
<pre>${displayContent.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
<script>window.onload = function(){ window.print(); }<\/script>
</body>
</html>`);
    win.document.close();
  };

  const downloadDOCX = () => {
    if (docxArtifact) {
      window.location.href = `/api/v1/artifacts/${docxArtifact.artifact_id}/download`;
    }
  };

  const downloadZip = () => {
    if (zipArtifact) {
      window.location.href = `/api/v1/artifacts/${zipArtifact.artifact_id}/download`;
      return;
    }
    const bundle = artifacts.map(a => {
      const c = (a as any).full_content || a.content_snippet || '';
      return `=== ${a.title} ===\n\n${c}\n\n`;
    }).join('\n' + '='.repeat(60) + '\n\n');
    const blob = new Blob([bundle], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'all_deliverables.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="output-card fade-in">
      <div className="output-card-header">
        <div className="output-card-title">
          <CheckCircle size={15} />
          Deliverables Ready — {artifacts.length} artifact{artifacts.length > 1 ? 's' : ''}
        </div>
        <div className="output-card-actions">
          <button className="btn-copy" onClick={handleCopy}>
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button className="btn-download btn-download-txt" onClick={() => downloadAs('txt', 'text/plain')}>
            <Download size={12} /> TXT
          </button>
          <button className="btn-download btn-download-md" onClick={() => downloadAs('md', 'text/markdown')}>
            <FileText size={12} /> MD
          </button>
          {docxArtifact && (
            <button className="btn-download btn-download-docx" onClick={downloadDOCX}>
              <FileText size={12} /> DOCX
            </button>
          )}
          <button className="btn-download btn-download-pdf" onClick={downloadPDF}>
            <FileText size={12} /> PDF
          </button>
          {zipArtifact && (
            <button className="btn-download btn-download-zip" onClick={downloadZip}>
              <Download size={12} /> ZIP
            </button>
          )}
          {contentType === 'code' && !zipArtifact && (
            <button className="btn-download btn-download-zip" onClick={() => downloadAs('py', 'text/plain')}>
              <Code2 size={12} /> .PY
            </button>
          )}
          {artifacts.length > 1 && !zipArtifact && (
            <button className="btn-download btn-download-zip" onClick={downloadZip}>
              <Download size={12} /> ALL
            </button>
          )}
        </div>
      </div>

      {artifacts.length > 1 && (
        <div className="output-tab-bar">
          {artifacts.map((a, i) => (
            <button
              key={a.artifact_id}
              className={`output-tab ${i === activeTab ? 'active' : ''}`}
              onClick={() => setActiveTab(i)}
            >
              {a.artifact_type === 'code' ? <Code2 size={11} style={{ display: 'inline', marginRight: 4 }} /> : <FileText size={11} style={{ display: 'inline', marginRight: 4 }} />}
              {a.title.replace('Deliverable - ', '')}
            </button>
          ))}
        </div>
      )}

      <div className="output-content">
        {contentType === 'code' ? (
          <pre className="output-code">{displayContent}</pre>
        ) : (
          <div className="output-text">{displayContent}</div>
        )}
      </div>
    </div>
  );
};

// ─── Message Renderer ─────────────────────────────────────────────────────────

const MessageBubble: React.FC<{
  msg: ChatMessage;
  onApprove: (approvalId: string) => void;
  onReject: (approvalId: string) => void;
}> = ({ msg, onApprove, onReject }) => {
  if (msg.type === 'user') {
    return (
      <div className="message-row user fade-in">
        <div className="msg-avatar user"><User size={16} /></div>
        <div className="msg-content">
          <div className="msg-sender" style={{ textAlign: 'right' }}>You</div>
          <div className="msg-bubble user">{msg.content}</div>
        </div>
      </div>
    );
  }

  if (msg.type === 'system') {
    return (
      <div className="message-row fade-in" style={{ justifyContent: 'center', padding: '4px 24px' }}>
        <div className="msg-bubble system" style={{ textAlign: 'center', maxWidth: 500 }}>
          {msg.content}
        </div>
      </div>
    );
  }

  // Agent message
  return (
    <div className="message-row fade-in">
      <div className="msg-avatar agent"><Bot size={16} style={{ color: '#06b6d4' }} /></div>
      <div className="msg-content" style={{ flex: 1, maxWidth: 720 }}>
        <div className="msg-sender">AI Agent System</div>
        <div className="msg-bubble agent">
          {msg.isTyping ? (
            <div className="typing-indicator">
              <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
            </div>
          ) : (
            <>
              <div style={{ fontSize: '0.88rem', lineHeight: 1.65, color: 'var(--text-secondary)' }}>
                {msg.content}
              </div>

              {/* Pending approval banners */}
              {msg.approvals?.filter(a => a.status === 'pending').map(approval => (
                <div key={approval.approval_id} className="approval-banner" style={{ marginTop: 12 }}>
                  <div className="approval-info">
                    <AlertTriangle size={16} />
                    <span><strong>Approval Required:</strong> {approval.description}</span>
                  </div>
                  <div className="approval-actions">
                    <button className="btn-approve" onClick={() => onApprove(approval.approval_id)}>
                      ✓ Approve
                    </button>
                    <button className="btn-reject" onClick={() => onReject(approval.approval_id)}>
                      ✗ Reject
                    </button>
                  </div>
                </div>
              ))}

              {/* Task pipeline */}
              {msg.tasks && msg.tasks.length > 0 && (
                <AgentProgress tasks={msg.tasks} />
              )}

              {/* Final deliverables */}
              {msg.isComplete && msg.artifacts && msg.artifacts.length > 0 && (
                <OutputCard artifacts={msg.artifacts} />
              )}
            </>
          )}
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4, marginLeft: 2 }}>
          {formatTime(msg.timestamp)}
          {msg.runId && <span style={{ marginLeft: 8, fontFamily: 'var(--font-mono)' }}>{msg.runId}</span>}
        </div>
      </div>
    </div>
  );
};

// ─── Main App ─────────────────────────────────────────────────────────────────

export const App: React.FC = () => {
  const [defaultProject, setDefaultProject] = useState<Project | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Bootstrap: ensure a default project exists
  useEffect(() => {
    const init = async () => {
      try {
        const projects = await api.getProjects();
        let proj = projects.find(p => p.name === 'Default Workspace') || projects[0];
        if (!proj) {
          proj = await api.createProject('Default Workspace', 'Auto-created default workspace');
        }
        setDefaultProject(proj);

        // Load existing runs as sessions
        const runs = await api.getRuns(proj.project_id);
        const loadedSessions: ChatSession[] = runs.map(r => ({
          id: r.run_id,
          projectId: r.project_id,
          title: r.goal.slice(0, 60) + (r.goal.length > 60 ? '…' : ''),
          status: r.status,
          createdAt: r.created_at,
        }));
        setSessions(loadedSessions);
      } catch (err) {
        console.error('Init error:', err);
      }
    };
    init();
  }, []);

  // Poll the active session for live updates
  const startPolling = useCallback((runId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const [run, tasks, artifacts, approvals] = await Promise.all([
          api.getRun(runId),
          api.getRunTasks(runId),
          api.getArtifacts(runId),
          api.getApprovals(runId),
        ]);

        const isTerminal = run.status === 'completed' || run.status === 'failed';

        setMessages(prev => {
          const idx = prev.findIndex(m => m.runId === runId && m.type === 'agent');
          if (idx === -1) return prev;

          const updated = [...prev];
          const msg = { ...updated[idx] };

          msg.tasks = tasks;
          msg.approvals = approvals;
          msg.isComplete = isTerminal;

          if (isTerminal) {
            msg.artifacts = artifacts;
            if (run.status === 'completed') {
              msg.content = `✅ Task completed successfully in ${run.execution_time_seconds?.toFixed(1) ?? '?'}s. Here are your deliverables:`;
            } else {
              msg.content = `❌ Something went wrong: ${run.error_message || 'Unknown error'}. You can try again.`;
            }
            msg.isTyping = false;
          } else {
            const completedCount = tasks.filter(t => t.status === 'completed').length;
            const runningTask = tasks.find(t => t.status === 'running');
            if (run.status === 'waiting_approval') {
              msg.content = `⏳ Awaiting your approval to continue. Please review and decide:`;
              msg.isTyping = false;
            } else if (runningTask) {
              msg.content = `🔄 Working on it… Currently running **${runningTask.title}** (${completedCount}/${tasks.length} steps done)`;
              msg.isTyping = false;
            }
          }

          updated[idx] = msg;
          return updated;
        });

        // Update session status
        setSessions(prev => prev.map(s => s.id === runId ? { ...s, status: run.status } : s));

        if (isTerminal && pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setIsSending(false);
        }
      } catch {
        // silently ignore transient errors
      }
    }, 2000);
  }, []);

  const handleSend = async (text?: string) => {
    const goal = (text ?? inputText).trim();
    if (!goal || isSending || !defaultProject) return;

    setInputText('');
    setIsSending(true);

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: goal,
      timestamp: new Date().toISOString(),
    };

    const agentMsg: ChatMessage = {
      id: `agent-${Date.now()}`,
      type: 'agent',
      content: '🚀 Starting your request… Breaking it down into subtasks.',
      timestamp: new Date().toISOString(),
      isTyping: true,
      tasks: [],
      artifacts: [],
      approvals: [],
      isComplete: false,
    };

    setMessages(prev => [...prev, userMsg, agentMsg]);

    try {
      const run = await api.createRun(defaultProject.project_id, goal);

      // Attach runId to the agent message
      setMessages(prev =>
        prev.map(m => m.id === agentMsg.id
          ? { ...m, runId: run.run_id, isTyping: false, content: '🔄 Planning your request…' }
          : m
        )
      );

      // Add to sessions list
      const newSession: ChatSession = {
        id: run.run_id,
        projectId: run.project_id,
        title: goal.slice(0, 60) + (goal.length > 60 ? '…' : ''),
        status: run.status,
        createdAt: run.created_at,
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(run.run_id);

      startPolling(run.run_id);
    } catch (err: any) {
      setMessages(prev =>
        prev.map(m => m.id === agentMsg.id
          ? { ...m, isTyping: false, content: `❌ Failed to start: ${err.message}` }
          : m
        )
      );
      setIsSending(false);
    }
  };

  const handleApprove = async (approvalId: string) => {
    await api.decideApproval(approvalId, 'approved', 'Approved by user');
    // Resume polling will handle the rest
  };

  const handleReject = async (approvalId: string) => {
    await api.decideApproval(approvalId, 'rejected', 'Rejected by user');
  };

  const handleLoadSession = async (session: ChatSession) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    setActiveSessionId(session.id);

    try {
      const [run, tasks, artifacts, approvals] = await Promise.all([
        api.getRun(session.id),
        api.getRunTasks(session.id),
        api.getArtifacts(session.id),
        api.getApprovals(session.id),
      ]);

      const isTerminal = run.status === 'completed' || run.status === 'failed';

      let agentContent = '';
      if (run.status === 'completed') {
        agentContent = `✅ Completed in ${run.execution_time_seconds?.toFixed(1) ?? '?'}s. Here are your deliverables:`;
      } else if (run.status === 'failed') {
        agentContent = `❌ Failed: ${run.error_message || 'Unknown error'}`;
      } else {
        agentContent = '🔄 Still working…';
      }

      const restoredMessages: ChatMessage[] = [
        {
          id: `user-${session.id}`,
          type: 'user',
          content: run.goal,
          timestamp: run.created_at,
        },
        {
          id: `agent-${session.id}`,
          type: 'agent',
          content: agentContent,
          timestamp: run.started_at || run.created_at,
          runId: session.id,
          tasks,
          artifacts,
          approvals,
          isComplete: isTerminal,
          isTyping: false,
        },
      ];

      setMessages(restoredMessages);

      if (!isTerminal) {
        setIsSending(true);
        startPolling(session.id);
      }
    } catch (err) {
      console.error('Load session error:', err);
    }
  };

  const handleNewChat = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    setActiveSessionId(null);
    setMessages([]);
    setIsSending(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const statusDot = (status: Run['status']) => {
    const colors: Record<string, string> = {
      completed: '#34d399',
      failed: '#fb7185',
      running: '#38bdf8',
      planning: '#c084fc',
      waiting_approval: '#fbbf24',
      pending: '#64748b',
    };
    return (
      <span style={{
        width: 7, height: 7, borderRadius: '50%',
        background: colors[status] ?? '#64748b',
        display: 'inline-block', flexShrink: 0,
        boxShadow: status === 'running' ? `0 0 6px ${colors.running}` : 'none',
      }} />
    );
  };

  const showWelcome = messages.length === 0;

  return (
    <div className="app-shell">
      {/* ─── Sidebar ─────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">🤖</div>
            <span className="sidebar-logo-text">AgentOS</span>
          </div>
          <button className="btn-new-chat" onClick={handleNewChat}>
            <Plus size={14} /> New Task
          </button>
        </div>

        <div className="sidebar-section-title">Recent Tasks</div>

        <div className="sidebar-list">
          {sessions.length === 0 && (
            <div style={{ padding: '12px 12px', fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              No tasks yet. Type something to get started.
            </div>
          )}
          {sessions.map(session => (
            <div
              key={session.id}
              className={`sidebar-item ${activeSessionId === session.id ? 'active' : ''}`}
              onClick={() => handleLoadSession(session)}
            >
              <div className="sidebar-item-icon">
                {session.status === 'completed' ? '✓' :
                 session.status === 'failed' ? '✗' :
                 session.status === 'running' || session.status === 'planning' ? '↻' : '·'}
              </div>
              <div className="sidebar-item-info">
                <div className="sidebar-item-title">{session.title}</div>
                <div className="sidebar-item-meta">
                  {statusDot(session.status)}
                  <span style={{ textTransform: 'capitalize' }}>{session.status}</span>
                  <span>·</span>
                  <span>{formatTime(session.createdAt)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="status-pill">
            <div className="status-dot" />
            Backend connected
          </div>
        </div>
      </aside>

      {/* ─── Main Chat ───────────────────────────────────────── */}
      <main className="chat-main">
        {/* Topbar */}
        <div className="chat-topbar">
          <div className="chat-topbar-title">
            {activeSessionId
              ? sessions.find(s => s.id === activeSessionId)?.title ?? 'Task'
              : 'Autonomous AI Multi-Agent Platform'}
          </div>
          <div className="chat-topbar-actions">
            {activeSessionId && (
              <span className={`badge badge-${sessions.find(s => s.id === activeSessionId)?.status ?? 'pending'}`}>
                {sessions.find(s => s.id === activeSessionId)?.status ?? 'pending'}
              </span>
            )}
            <button
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 12px', borderRadius: 7,
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-secondary)',
                fontSize: '0.78rem', fontWeight: 500, cursor: 'pointer',
                fontFamily: 'var(--font-sans)'
              }}
              onClick={handleNewChat}
            >
              <Plus size={13} /> New
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-area">
          {showWelcome ? (
            <div className="welcome-screen">
              <div className="welcome-logo">🤖</div>
              <h1 className="welcome-title">What can I help you build?</h1>
              <p className="welcome-subtitle">
                Describe any task — research papers, websites, scripts, analysis reports — and a team of AI agents will complete it and deliver the full output.
              </p>
              <div className="suggestion-grid">
                {SUGGESTIONS.map((s, i) => (
                  <div key={i} className="suggestion-card" onClick={() => handleSend(s.prompt)}>
                    <div className="suggestion-emoji">{s.emoji}</div>
                    <div className="suggestion-title">{s.title}</div>
                    <div className="suggestion-desc">{s.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="input-box"
              placeholder="Describe your task… (e.g., 'Write a research paper on AI in healthcare' or 'Build a todo app in React')"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={isSending}
            />
            <button
              className="input-send-btn"
              onClick={() => handleSend()}
              disabled={!inputText.trim() || isSending || !defaultProject}
            >
              <Send size={16} />
            </button>
          </div>
          <div className="input-hint">
            Press Enter to send · Shift+Enter for new line · Agents will complete the full task and deliver downloadable output
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;

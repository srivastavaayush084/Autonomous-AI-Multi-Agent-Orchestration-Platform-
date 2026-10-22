import React, { useState } from 'react';
import type { Artifact } from '../types';
import { FileText, Code2, X, Layers, Copy, Check, Download } from 'lucide-react';

interface ArtifactsModalProps {
  isOpen: boolean;
  onClose: () => void;
  artifacts: Artifact[];
  filterTaskId?: string | null;
}

export const ArtifactsModal: React.FC<ArtifactsModalProps> = ({
  isOpen,
  onClose,
  artifacts,
  filterTaskId
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const displayList = filterTaskId 
    ? artifacts.filter(a => a.task_id === filterTaskId)
    : artifacts;

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownload = (content: string, title: string, type: string) => {
    const ext = type === 'code' ? 'py' : 'md';
    const cleanTitle = title.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
    const filename = `${cleanTitle}.${ext}`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(4, 7, 17, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 70,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '850px', maxHeight: '85vh', padding: '28px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Layers size={22} color="#06b6d4" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }} className="text-gradient">
              Generated Deliverables & Artifacts
            </h2>
            <span className="badge badge-completed" style={{ fontSize: '0.72rem' }}>
              {displayList.length} Items
            </span>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '6px' }}>
          {displayList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
              <FileText size={36} style={{ opacity: 0.4, marginBottom: '8px' }} />
              <p>No artifacts produced yet for this selection.</p>
              <p style={{ fontSize: '0.78rem', marginTop: '4px', color: 'var(--text-muted)' }}>
                Artifacts are automatically produced and cataloged as DAG tasks complete.
              </p>
            </div>
          ) : (
            displayList.map(a => {
              const contentToUse = a.content_snippet || '';
              const isCopied = copiedId === a.artifact_id;

              return (
                <div key={a.artifact_id} className="glass-panel" style={{ padding: '16px', background: 'rgba(0,0,0,0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {a.artifact_type === 'code' ? <Code2 size={16} color="#818cf8" /> : <FileText size={16} color="#06b6d4" />}
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>{a.title}</h4>
                      <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>[{a.artifact_id}]</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginRight: '6px' }}>
                        {(a.size_bytes / 1024).toFixed(1)} KB
                      </span>
                      
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => handleCopy(contentToUse, a.artifact_id)}
                      >
                        {isCopied ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                        <span>{isCopied ? 'Copied!' : 'Copy'}</span>
                      </button>

                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => handleDownload(contentToUse, a.title, a.artifact_type)}
                      >
                        <Download size={12} />
                        <span>Download</span>
                      </button>
                    </div>
                  </div>

                  {a.content_snippet && (
                    <pre className="font-mono" style={{
                      background: '#030712',
                      border: '1px solid var(--border-subtle)',
                      padding: '12px',
                      borderRadius: '8px',
                      fontSize: '0.78rem',
                      color: '#93c5fd',
                      overflowX: 'auto',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '260px'
                    }}>
                      {a.content_snippet}
                    </pre>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

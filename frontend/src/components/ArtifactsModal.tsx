import React from 'react';
import type { Artifact } from '../types';
import { FileText, Code2, X, Layers } from 'lucide-react';

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
  if (!isOpen) return null;

  const displayList = filterTaskId 
    ? artifacts.filter(a => a.task_id === filterTaskId)
    : artifacts;

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
      <div className="glass-panel" style={{ width: '100%', maxWidth: '800px', maxHeight: '85vh', padding: '28px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Layers size={22} color="#06b6d4" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }} className="text-gradient">
              Generated Deliverables & Artifacts
            </h2>
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
            </div>
          ) : (
            displayList.map(a => (
              <div key={a.artifact_id} className="glass-panel" style={{ padding: '16px', background: 'rgba(0,0,0,0.3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {a.artifact_type === 'code' ? <Code2 size={16} color="#818cf8" /> : <FileText size={16} color="#06b6d4" />}
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>{a.title}</h4>
                    <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>[{a.artifact_id}]</span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {(a.size_bytes / 1024).toFixed(1)} KB
                  </span>
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
                    maxHeight: '220px'
                  }}>
                    {a.content_snippet}
                  </pre>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { Download, FileText, Code2, Package, FileSpreadsheet, Search, Filter, RefreshCw, Eye, X } from 'lucide-react';
import type { Artifact } from '../../types';
import { api } from '../../services/api';

export const FilesDownloadsWorkspace: React.FC = () => {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);

  const fetchArtifacts = async () => {
    setLoading(true);
    try {
      const items = await api.getArtifacts();
      setArtifacts(items);
    } catch (err) {
      console.error('Failed to load artifacts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const getIcon = (type: string, title: string) => {
    const t = (type || '').toLowerCase();
    const tit = (title || '').toLowerCase();
    if (t === 'pdf' || tit.endsWith('.pdf')) return <FileText size={16} color="#fb7185" />;
    if (t === 'docx' || tit.endsWith('.docx')) return <FileText size={16} color="#38bdf8" />;
    if (t === 'zip' || tit.endsWith('.zip')) return <Package size={16} color="#fbbf24" />;
    if (t === 'csv' || tit.endsWith('.csv')) return <FileSpreadsheet size={16} color="#34d399" />;
    if (t === 'code' || tit.endsWith('.py') || tit.endsWith('.js')) return <Code2 size={16} color="#818cf8" />;
    return <FileText size={16} color="#94a3b8" />;
  };

  const filtered = artifacts.filter(a => {
    const matchesSearch = (a.title || '').toLowerCase().includes(search.toLowerCase()) ||
                          (a.run_id || '').toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;
    if (typeFilter === 'all') return true;
    const t = (a.artifact_type || '').toLowerCase();
    const tit = (a.title || '').toLowerCase();
    if (typeFilter === 'pdf') return t === 'pdf' || tit.endsWith('.pdf');
    if (typeFilter === 'docx') return t === 'docx' || tit.endsWith('.docx');
    if (typeFilter === 'zip') return t === 'zip' || tit.endsWith('.zip');
    if (typeFilter === 'csv') return t === 'csv' || tit.endsWith('.csv');
    if (typeFilter === 'code') return t === 'code' || tit.endsWith('.py') || tit.endsWith('.js');
    return true;
  });

  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <Download size={24} color="#38bdf8" />
            Generated Files & Verified Downloads
          </div>
          <div className="workspace-subtitle">
            Centralized registry of all physical deliverables generated across all workspaces. Direct 1-click download with on-disk validation.
          </div>
        </div>
        <button
          className="btn-new-chat"
          onClick={fetchArtifacts}
          disabled={loading}
          style={{ padding: '8px 16px' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Files
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="workspace-panel" style={{ padding: '14px 20px', display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
          <input
            type="text"
            className="form-input"
            placeholder="Search deliverables by name or run ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: '36px' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Filter size={16} color="var(--text-secondary)" />
          {['all', 'pdf', 'docx', 'zip', 'csv', 'code'].map(f => (
            <button
              key={f}
              onClick={() => setTypeFilter(f)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                background: typeFilter === f ? 'rgba(99, 102, 241, 0.25)' : 'rgba(0,0,0,0.25)',
                border: typeFilter === f ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
                color: typeFilter === f ? '#fff' : 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Files Table */}
      <div className="workspace-panel" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading deliverables registry…
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No deliverables found matching your criteria.
          </div>
        ) : (
          <table className="files-table">
            <thead>
              <tr>
                <th>Deliverable Name</th>
                <th>Type</th>
                <th>Run ID</th>
                <th>Size</th>
                <th>Created</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(a => (
                <tr key={a.artifact_id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      {getIcon(a.artifact_type, a.title)}
                      <span style={{ fontWeight: 600 }}>{a.title}</span>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-completed">{a.artifact_type || 'file'}</span>
                  </td>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {a.run_id?.slice(0, 14)}…
                    </span>
                  </td>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                      {a.size_bytes > 1024 * 1024
                        ? `${(a.size_bytes / (1024 * 1024)).toFixed(2)} MB`
                        : `${(a.size_bytes / 1024).toFixed(1)} KB`}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(a.created_at).toLocaleString()}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '8px' }}>
                      <button
                        className="btn-table-action"
                        onClick={() => setSelectedArtifact(a)}
                        title="Preview Content"
                      >
                        <Eye size={12} /> Preview
                      </button>
                      <a
                        href={`/api/v1/artifacts/${a.artifact_id}/download`}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-table-action"
                        style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.35)', color: '#34d399' }}
                      >
                        <Download size={12} /> Download
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Artifact Preview Drawer/Modal */}
      {selectedArtifact && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 80,
          padding: '24px',
        }}>
          <div className="workspace-panel" style={{ width: '100%', maxWidth: '800px', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {getIcon(selectedArtifact.artifact_type, selectedArtifact.title)}
                <span style={{ fontWeight: 700, fontSize: '1rem' }}>{selectedArtifact.title}</span>
              </div>
              <button
                onClick={() => setSelectedArtifact(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{
              flex: 1,
              overflowY: 'auto',
              background: 'rgba(0,0,0,0.3)',
              borderRadius: '6px',
              padding: '16px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82rem',
              lineHeight: 1.6,
              color: 'var(--text-primary)',
              whiteSpace: 'pre-wrap',
            }}>
              {selectedArtifact.full_content || selectedArtifact.content_snippet || 'No text content available'}
            </div>

            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <a
                href={`/api/v1/artifacts/${selectedArtifact.artifact_id}/download`}
                target="_blank"
                rel="noreferrer"
                className="btn-download btn-download-pdf"
                style={{ textDecoration: 'none' }}
              >
                <Download size={14} /> Download File
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

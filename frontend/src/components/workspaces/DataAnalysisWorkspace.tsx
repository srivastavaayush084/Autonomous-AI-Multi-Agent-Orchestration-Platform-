import React, { useState, useRef } from 'react';
import { BarChart3, Upload, FileSpreadsheet, Download, CheckCircle, Zap, X } from 'lucide-react';
import type { Run, Task, Artifact } from '../../types';
import { api } from '../../services/api';

interface DataAnalysisWorkspaceProps {
  projectId: string;
  onLaunchTask: (goal: string) => Promise<void>;
  activeRun: Run | null;
  activeTasks: Task[];
  activeArtifacts: Artifact[];
  isProcessing: boolean;
  onCancelRun: (runId: string) => void;
}

export const DataAnalysisWorkspace: React.FC<DataAnalysisWorkspaceProps> = ({
  projectId,
  onLaunchTask,
  activeRun,
  activeTasks,
  activeArtifacts,
  isProcessing,
  onCancelRun,
}) => {
  const [uploadedFile, setUploadedFile] = useState<{
    file_id: string;
    filename: string;
    file_path: string;
    preview: string;
    size_bytes: number;
  } | null>(null);
  const [analysisGoal, setAnalysisGoal] = useState('Analyze this dataset, calculate comprehensive summary statistics, detect outliers, identify correlations, and export summary CSV and reports.');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const res = await api.uploadFile(file, projectId);
      setUploadedFile(res);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload dataset');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartAnalysis = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadedFile || isProcessing) return;

    const prompt = `Perform data analysis on uploaded dataset at "${uploadedFile.file_path}" (${uploadedFile.filename}). Specific request: ${analysisGoal.trim()}. Compute descriptive statistics, column distributions, anomalies, correlations, and output summary_statistics.csv, Word DOCX, and PDF reports.`;
    onLaunchTask(prompt);
  };

  const csvArtifact = activeArtifacts.find(a => a.artifact_type === 'csv' || a.title.toLowerCase().endsWith('.csv'));
  const docxArtifact = activeArtifacts.find(a => a.artifact_type === 'docx' || a.title.toLowerCase().endsWith('.docx'));
  const pdfArtifact = activeArtifacts.find(a => a.artifact_type === 'pdf' || a.title.toLowerCase().endsWith('.pdf'));

  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <BarChart3 size={24} color="#10b981" />
            Autonomous Data Analysis & Statistics Engine
          </div>
          <div className="workspace-subtitle">
            Upload CSV or Excel datasets to compute quantitative distributions, IQR outliers, correlations, and export summary CSVs and analytical reports.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 440px) 1fr', gap: '24px' }}>
        {/* Left: Upload & Configuration Form */}
        <div className="workspace-panel">
          <div className="form-group">
            <label className="form-label">Upload Dataset (CSV / XLSX / JSON)</label>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".csv,.xlsx,.xls,.json,.tsv"
              onChange={handleFileChange}
              disabled={isUploading || isProcessing}
            />

            {!uploadedFile ? (
              <div
                className="file-dropzone"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={32} color="#10b981" />
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {isUploading ? 'Uploading & parsing dataset…' : 'Click to select or drop CSV / XLSX'}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Supports up to 50 MB with automatic column type inference
                </div>
              </div>
            ) : (
              <div className="uploaded-file-chip">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileSpreadsheet size={16} />
                  <span>{uploadedFile.filename}</span>
                  <span style={{ fontSize: '0.72rem', opacity: 0.8 }}>
                    ({(uploadedFile.size_bytes / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setUploadedFile(null)}
                  style={{ background: 'none', border: 'none', color: '#fb7185', cursor: 'pointer' }}
                >
                  <X size={14} />
                </button>
              </div>
            )}

            {uploadError && (
              <div style={{ color: '#fb7185', fontSize: '0.78rem', marginTop: '6px' }}>
                {uploadError}
              </div>
            )}
          </div>

          {/* Dataset Preview */}
          {uploadedFile && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
                Data Preview (First 500 chars):
              </div>
              <pre style={{
                padding: '10px',
                background: 'rgba(0,0,0,0.3)',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-code)',
                maxHeight: '120px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
              }}>
                {uploadedFile.preview}
              </pre>
            </div>
          )}

          <form onSubmit={handleStartAnalysis}>
            <div className="form-group">
              <label className="form-label">Analytical Focus & Instructions</label>
              <textarea
                className="form-textarea"
                value={analysisGoal}
                onChange={e => setAnalysisGoal(e.target.value)}
                disabled={isProcessing || !uploadedFile}
                style={{ height: '100px' }}
                required
              />
            </div>

            <button
              type="submit"
              className="btn-send"
              disabled={isProcessing || !uploadedFile}
              style={{ width: '100%', marginTop: '6px', height: '42px', justifyContent: 'center' }}
            >
              <Zap size={16} />
              {isProcessing ? 'Analyzing Dataset…' : 'Run Full Statistical Analysis'}
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
                Cancel Analysis Run
              </button>
            </div>
          )}
        </div>

        {/* Right: Results & Verified Downloads */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {activeRun && (
            <div className="workspace-panel" style={{ borderLeft: '4px solid var(--accent-emerald)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                  Analysis Execution Pipeline
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

          {/* Generated Artifacts */}
          {activeArtifacts.length > 0 && (
            <div className="workspace-panel" style={{ border: '1px solid rgba(16, 185, 129, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: 700, marginBottom: '14px' }}>
                <CheckCircle size={18} />
                Calculated Deliverables Available
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {csvArtifact && (
                  <a
                    href={`/api/v1/artifacts/${csvArtifact.artifact_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-download btn-download-txt"
                    style={{ textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download summary_statistics.csv
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
                    <Download size={14} /> Download Analysis DOCX
                  </a>
                )}
                {pdfArtifact && (
                  <a
                    href={`/api/v1/artifacts/${pdfArtifact.artifact_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-download btn-download-pdf"
                    style={{ textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download Analysis PDF
                  </a>
                )}
              </div>

              {/* Text Preview of Statistics Findings */}
              <div style={{ marginTop: '16px' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px', textTransform: 'uppercase' }}>
                  Quantitative Summary Preview:
                </div>
                <div style={{
                  maxHeight: '260px',
                  overflowY: 'auto',
                  padding: '12px',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '6px',
                  fontSize: '0.84rem',
                  lineHeight: '1.6',
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-wrap',
                }}>
                  {activeArtifacts[0].full_content || activeArtifacts[0].content_snippet || 'No output preview'}
                </div>
              </div>
            </div>
          )}

          {!activeRun && activeArtifacts.length === 0 && (
            <div className="workspace-panel" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <BarChart3 size={42} style={{ opacity: 0.4, margin: '0 auto 12px' }} />
              <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Ready for Data Ingestion</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                Upload any CSV or Excel file to compute statistical summaries, correlations, and downloadable charts.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

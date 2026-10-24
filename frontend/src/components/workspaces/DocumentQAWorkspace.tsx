import React, { useState, useRef } from 'react';
import { FileSearch, Upload, FileText, Image, Download, CheckCircle, Zap, X } from 'lucide-react';
import type { Run, Task, Artifact } from '../../types';
import { api } from '../../services/api';

interface DocumentQAWorkspaceProps {
  projectId: string;
  onLaunchTask: (goal: string) => Promise<void>;
  activeRun: Run | null;
  activeTasks: Task[];
  activeArtifacts: Artifact[];
  isProcessing: boolean;
  onCancelRun: (runId: string) => void;
}

export const DocumentQAWorkspace: React.FC<DocumentQAWorkspaceProps> = ({
  projectId,
  onLaunchTask,
  activeRun,
  activeTasks,
  activeArtifacts,
  isProcessing,
  onCancelRun,
}) => {
  const [uploadedDoc, setUploadedDoc] = useState<{
    file_id: string;
    filename: string;
    file_path: string;
    file_type: string;
    preview: string;
    size_bytes: number;
  } | null>(null);
  const [question, setQuestion] = useState('');
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
      setUploadedDoc(res);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartQA = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadedDoc || !question.trim() || isProcessing) return;

    const prompt = `Analyze uploaded document at "${uploadedDoc.file_path}" (${uploadedDoc.filename}, type: ${uploadedDoc.file_type}). Answer this question strictly grounded in the document content: ${question.trim()}. Highlight key quotes and identify any unsupported conclusions. Provide complete DOCX and PDF answer reports.`;
    onLaunchTask(prompt);
  };

  const docxArtifact = activeArtifacts.find(a => a.artifact_type === 'docx' || a.title.toLowerCase().endsWith('.docx'));
  const pdfArtifact = activeArtifacts.find(a => a.artifact_type === 'pdf' || a.title.toLowerCase().endsWith('.pdf'));

  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <FileSearch size={24} color="#a855f7" />
            Document & Image Understanding Studio
          </div>
          <div className="workspace-subtitle">
            Upload PDF, Word DOCX, text files, or images for text extraction, OCR, grounded question answering, and verified report downloads.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 440px) 1fr', gap: '24px' }}>
        {/* Left: Document Upload & Prompt */}
        <div className="workspace-panel">
          <div className="form-group">
            <label className="form-label">Upload File (PDF / DOCX / TXT / PNG / JPG)</label>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              disabled={isUploading || isProcessing}
            />

            {!uploadedDoc ? (
              <div
                className="file-dropzone"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={32} color="#a855f7" />
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {isUploading ? 'Extracting text and metadata…' : 'Click to select or drop document/image'}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Supports PDF text, Word formatting, and OCR on high-res images
                </div>
              </div>
            ) : (
              <div className="uploaded-file-chip">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {uploadedDoc.file_type === 'image' ? <Image size={16} /> : <FileText size={16} />}
                  <span>{uploadedDoc.filename}</span>
                  <span style={{ fontSize: '0.72rem', opacity: 0.8 }}>
                    ({(uploadedDoc.size_bytes / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setUploadedDoc(null)}
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

          {/* Extracted Text Preview */}
          {uploadedDoc && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
                Extracted Text Snippet:
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
                {uploadedDoc.preview || 'Text parsed successfully'}
              </pre>
            </div>
          )}

          <form onSubmit={handleStartQA}>
            <div className="form-group">
              <label className="form-label">Question / Extraction Query</label>
              <textarea
                className="form-textarea"
                placeholder="e.g., What are the core contractual obligations and liabilities outlined in section 4? Summarize key deadlines."
                value={question}
                onChange={e => setQuestion(e.target.value)}
                disabled={isProcessing || !uploadedDoc}
                style={{ height: '110px' }}
                required
              />
            </div>

            <button
              type="submit"
              className="btn-send"
              disabled={isProcessing || !uploadedDoc || !question.trim()}
              style={{ width: '100%', marginTop: '6px', height: '42px', justifyContent: 'center' }}
            >
              <Zap size={16} />
              {isProcessing ? 'Analyzing Document…' : 'Synthesize Grounded Answer'}
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
                Cancel Understanding Run
              </button>
            </div>
          )}
        </div>

        {/* Right: Results & Downloads */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {activeRun && (
            <div className="workspace-panel" style={{ borderLeft: '4px solid var(--accent-violet)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                  Document Understanding Pipeline
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

          {activeArtifacts.length > 0 && (
            <div className="workspace-panel" style={{ border: '1px solid rgba(168, 85, 247, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#c084fc', fontWeight: 700, marginBottom: '14px' }}>
                <CheckCircle size={18} />
                Grounded Deliverables Ready
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {docxArtifact && (
                  <a
                    href={`/api/v1/artifacts/${docxArtifact.artifact_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-download btn-download-docx"
                    style={{ textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download Answer DOCX
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
                    <Download size={14} /> Download Answer PDF
                  </a>
                )}
              </div>

              <div style={{ marginTop: '16px' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px', textTransform: 'uppercase' }}>
                  Grounded Synthesis:
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
              <FileSearch size={42} style={{ opacity: 0.4, margin: '0 auto 12px' }} />
              <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Ready for Document Grounding</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                Upload any PDF, Word document, text file, or image to ask questions grounded directly in the text.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

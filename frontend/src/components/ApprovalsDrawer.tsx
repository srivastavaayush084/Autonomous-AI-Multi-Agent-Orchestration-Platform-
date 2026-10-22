import React, { useState } from 'react';
import type { ApprovalRequest } from '../types';
import { ShieldAlert, Check, X, Clock } from 'lucide-react';

interface ApprovalsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  approvals: ApprovalRequest[];
  onDecide: (approvalId: string, decision: 'approved' | 'rejected', reason: string) => Promise<void>;
}

export const ApprovalsDrawer: React.FC<ApprovalsDrawerProps> = ({
  isOpen,
  onClose,
  approvals,
  onDecide
}) => {
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});
  const [processingId, setProcessingId] = useState<string | null>(null);

  if (!isOpen) return null;

  const pendingList = approvals.filter(a => a.status === 'pending');

  const handleDecision = async (approvalId: string, decision: 'approved' | 'rejected') => {
    setProcessingId(approvalId);
    try {
      await onDecide(approvalId, decision, rejectReason[approvalId] || '');
    } catch (e) {
      alert(`Decision error: ${e}`);
    } finally {
      setProcessingId(null);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return <span style={{ background: 'rgba(244, 63, 94, 0.2)', color: '#fb7185', border: '1px solid rgba(244, 63, 94, 0.4)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700 }}>HIGH RISK</span>;
      default:
        return <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.4)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700 }}>MEDIUM RISK</span>;
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(4, 7, 17, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-end',
      zIndex: 60
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '540px',
        height: '100vh',
        padding: '28px',
        overflowY: 'auto',
        borderRadius: 0,
        borderLeft: '1px solid var(--border-glow)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={22} color="#fbbf24" />
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Human-in-the-Loop Gateway</h2>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            Close
          </button>
        </div>

        <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Consequential, deployment, or destructive operations are quarantined here pending explicit operator verification.
        </p>

        {pendingList.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            <Check size={40} color="#10b981" style={{ opacity: 0.5, marginBottom: '12px' }} />
            <p style={{ fontSize: '0.9rem', color: '#e2e8f0', fontWeight: 600 }}>Zero Pending Approval Gates</p>
            <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>All running agent pipelines are operating within autonomous clearance parameters.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {pendingList.map(item => (
              <div key={item.approval_id} className="glass-panel" style={{ padding: '18px', borderLeft: '4px solid #f59e0b' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getRiskBadge(item.risk_level)}
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} className="font-mono">
                      {item.approval_id}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    <span>Awaiting Decision</span>
                  </span>
                </div>

                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                  {item.action_type.toUpperCase()}: {item.description}
                </h4>

                {item.payload && (
                  <div style={{ background: 'rgba(0,0,0,0.35)', padding: '10px', borderRadius: '6px', fontSize: '0.78rem', color: '#cbd5e1', marginBottom: '14px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>PAYLOAD CONTEXT:</div>
                    <pre className="font-mono" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(item.payload, null, 2)}
                    </pre>
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <input
                    type="text"
                    placeholder="Optional feedback / reasoning (required on rejection)"
                    value={rejectReason[item.approval_id] || ''}
                    onChange={(e) => setRejectReason({ ...rejectReason, [item.approval_id]: e.target.value })}
                    style={{
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      padding: '8px 12px',
                      fontSize: '0.8rem',
                      color: '#f8fafc',
                      outline: 'none'
                    }}
                  />

                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => handleDecision(item.approval_id, 'rejected')}
                      disabled={processingId === item.approval_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 14px',
                        borderRadius: '6px',
                        background: 'rgba(244, 63, 94, 0.15)',
                        border: '1px solid rgba(244, 63, 94, 0.35)',
                        color: '#fb7185',
                        fontWeight: 600,
                        fontSize: '0.82rem',
                        cursor: 'pointer'
                      }}
                    >
                      <X size={14} />
                      <span>Reject & Abort</span>
                    </button>

                    <button
                      onClick={() => handleDecision(item.approval_id, 'approved')}
                      disabled={processingId === item.approval_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        border: 'none',
                        color: '#ffffff',
                        fontWeight: 600,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        boxShadow: '0 2px 10px rgba(16, 185, 129, 0.3)'
                      }}
                    >
                      <Check size={14} />
                      <span>Authorize Execution</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

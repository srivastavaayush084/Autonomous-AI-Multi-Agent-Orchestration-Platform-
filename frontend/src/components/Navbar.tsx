import React from 'react';
import { Cpu, Database, ShieldAlert, Sparkles, Play } from 'lucide-react';

interface NavbarProps {
  systemHealth: { status: string; database: string; strategy: string } | null;
  pendingApprovalsCount: number;
  onOpenNewRun: () => void;
  onOpenApprovals: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  systemHealth,
  pendingApprovalsCount,
  onOpenNewRun,
  onOpenApprovals,
}) => {
  return (
    <header className="glass-panel" style={{ margin: '16px 24px', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 10 }}>
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)'
        }}>
          <Cpu size={24} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em' }} className="text-gradient">
              Trendtide Orchestrator
            </h1>
            <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: '6px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontWeight: 700, border: '1px solid rgba(99, 102, 241, 0.4)' }}>
              v1.0 ML-CORE
            </span>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Autonomous Multi-Agent Orchestration & Model Routing Platform
          </p>
        </div>
      </div>

      {/* Live System Diagnostics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '8px', background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: systemHealth?.status === 'online' ? '#10b981' : '#f43f5e', boxShadow: systemHealth?.status === 'online' ? '0 0 8px #10b981' : 'none' }} />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            API: <span style={{ color: '#f8fafc' }}>{systemHealth?.status || 'Connecting...'}</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '8px', background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-subtle)' }}>
          <Database size={14} color="#06b6d4" />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            DB: <span style={{ color: '#06b6d4' }}>{systemHealth?.database?.includes('connected') ? 'Atlas Connected' : 'Dual-Mode Active'}</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '8px', background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-subtle)' }}>
          <Sparkles size={14} color="#a855f7" />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Router: <span style={{ color: '#c084fc' }}>ML Hybrid (RandomForest)</span>
          </span>
        </div>

        {/* Human-in-the-loop Pending Approval Button */}
        {pendingApprovalsCount > 0 && (
          <button
            onClick={onOpenApprovals}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.2)',
              border: '1px solid rgba(245, 158, 11, 0.5)',
              color: '#fbbf24',
              fontWeight: 700,
              fontSize: '0.8rem',
              cursor: 'pointer',
              animation: 'pulse-border 1.5s infinite'
            }}
          >
            <ShieldAlert size={16} />
            <span>{pendingApprovalsCount} Gate{pendingApprovalsCount > 1 ? 's' : ''} Require Approval</span>
          </button>
        )}

        {/* Action Button */}
        <button className="btn-primary" onClick={onOpenNewRun}>
          <Play size={16} />
          <span>Launch Autonomous Run</span>
        </button>
      </div>
    </header>
  );
};

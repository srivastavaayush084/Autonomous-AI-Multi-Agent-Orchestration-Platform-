import React from 'react';
import type { ModelInfo } from '../types';
import { Cpu, Zap, Cloud, HardDrive, CheckCircle2 } from 'lucide-react';

interface ModelRegistryPanelProps {
  models: ModelInfo[];
}

export const ModelRegistryPanel: React.FC<ModelRegistryPanelProps> = ({ models }) => {
  return (
    <div className="glass-panel" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={18} color="#818cf8" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Model Registry & Hybrid Inference Fleet</h3>
        </div>
        <span style={{ fontSize: '0.72rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
          <CheckCircle2 size={12} />
          <span>Multi-Provider Mesh Active</span>
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {models.map(m => (
          <div
            key={m.model_id}
            style={{
              background: 'rgba(0,0,0,0.25)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#f8fafc' }}>{m.name}</span>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.68rem',
                fontWeight: 600,
                padding: '2px 6px',
                borderRadius: '4px',
                background: m.is_local ? 'rgba(6, 182, 212, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                color: m.is_local ? '#22d3ee' : '#a5b4fc'
              }}>
                {m.is_local ? <HardDrive size={10} /> : <Cloud size={10} />}
                {m.is_local ? 'Local Ollama' : 'Cloud API'}
              </span>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {m.capabilities.map(cap => (
                <span
                  key={cap}
                  style={{
                    fontSize: '0.65rem',
                    background: 'rgba(255,255,255,0.05)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    color: 'var(--text-secondary)'
                  }}
                >
                  {cap}
                </span>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              <span>Context: {(m.context_window / 1024).toFixed(0)}k</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Zap size={10} color="#fbbf24" />
                {m.avg_latency_ms}ms
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

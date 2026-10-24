import React, { useState, useEffect } from 'react';
import { Settings, ShieldCheck, RefreshCw } from 'lucide-react';
import type { ModelInfo } from '../../types';
import { ModelRegistryPanel } from '../ModelRegistryPanel';
import { api } from '../../services/api';

interface SettingsWorkspaceProps {
  models: ModelInfo[];
  onRefreshModels: () => void;
}

export const SettingsWorkspace: React.FC<SettingsWorkspaceProps> = ({
  models,
  onRefreshModels,
}) => {
  const [health, setHealth] = useState<any>(null);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [checking, setChecking] = useState(false);

  const checkConnectivity = async () => {
    setChecking(true);
    try {
      const [h, s] = await Promise.all([
        api.getHealth(),
        api.getModelStatus(),
      ]);
      setHealth(h);
      setModelStatus(s);
      onRefreshModels();
    } catch (err) {
      console.error('Settings health error:', err);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkConnectivity();
  }, []);

  return (
    <div className="workspace-view-container fade-in">
      <div className="workspace-header">
        <div>
          <div className="workspace-title">
            <Settings size={24} color="#f59e0b" />
            Settings & Model Routing Configuration
          </div>
          <div className="workspace-subtitle">
            Configure local inference endpoints, inspect Ollama connectivity, model token budgets, and provider fallbacks.
          </div>
        </div>
        <button
          className="btn-new-chat"
          onClick={checkConnectivity}
          disabled={checking}
          style={{ padding: '8px 16px' }}
        >
          <RefreshCw size={14} className={checking ? 'animate-spin' : ''} />
          Ping Fleet & Models
        </button>
      </div>

      {/* Connectivity & Health Summary */}
      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-box-label">Backend Engine API</div>
          <div className="stat-box-value" style={{ color: health?.status === 'online' ? '#34d399' : '#fb7185' }}>
            {health?.status === 'online' ? '● Online (v1.0)' : 'Offline'}
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Database Mode</div>
          <div className="stat-box-value" style={{ color: '#06b6d4', fontSize: '0.95rem' }}>
            {health?.database || 'Dual-Mode Active'}
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Local Ollama Status</div>
          <div className="stat-box-value" style={{ color: '#38bdf8', fontSize: '0.95rem' }}>
            {modelStatus?.ollama_connected ? 'Connected (CPU Engine)' : 'Local Ollama Ready'}
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Primary Local Model</div>
          <div className="stat-box-value" style={{ color: '#c084fc', fontSize: '0.95rem' }}>
            llama3.2:1b (Installed)
          </div>
        </div>
      </div>

      {/* Model Fleet Panel */}
      <ModelRegistryPanel models={models} />

      {/* Local-First Architecture Information */}
      <div className="workspace-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <ShieldCheck size={20} color="#10b981" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Autonomous Local-First Guarantee</h3>
        </div>
        <p style={{ fontSize: '0.84rem', lineHeight: '1.65', color: 'var(--text-secondary)' }}>
          This multi-agent platform is fully functional without requiring external paid API keys. All core workflows
          (Research, Web Building, Data Analytics with pandas, Document Extraction with pypdf, and Direct Chat)
          execute using your local Ollama runtime and Python scientific packages. External cloud providers can optionally
          be configured for enhanced throughput when internet access is available.
        </p>
      </div>
    </div>
  );
};

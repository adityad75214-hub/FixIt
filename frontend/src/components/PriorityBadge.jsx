import React from 'react';
import { AlertCircle, ArrowUp, ArrowRight, ArrowDown } from 'lucide-react';

const PRIORITY_CONFIG = {
  critical: { label: 'Critical', bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5', icon: AlertCircle },
  high: { label: 'High', bg: '#FFEDD5', text: '#9A3412', border: '#FDBA74', icon: ArrowUp },
  medium: { label: 'Medium', bg: '#FEF3C7', text: '#92400E', border: '#FDE68A', icon: ArrowRight },
  low: { label: 'Low', bg: '#D1FAE5', text: '#065F46', border: '#A7F3D0', icon: ArrowDown },
};

export default function PriorityBadge({ priority }) {
  const normalized = (priority || 'medium').toLowerCase();
  const config = PRIORITY_CONFIG[normalized] || PRIORITY_CONFIG.medium;
  const Icon = config.icon;

  return (
    <span
      className={`priority-badge priority-${normalized}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.3rem',
        padding: '0.2rem 0.55rem',
        borderRadius: '6px',
        fontSize: '0.75rem',
        fontWeight: '600',
        backgroundColor: config.bg,
        color: config.text,
        border: `1px solid ${config.border}`,
        whiteSpace: 'nowrap'
      }}
    >
      <Icon size={12} strokeWidth={2.5} />
      {config.label}
    </span>
  );
}

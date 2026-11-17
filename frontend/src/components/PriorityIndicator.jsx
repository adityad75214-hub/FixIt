import React from 'react';

export default function PriorityIndicator({ priority, showLabel = true }) {
  const p = (priority || 'medium').toLowerCase();

  const configs = {
    critical: { label: 'Critical', color: 'var(--priority-critical)', bg: 'rgba(220, 38, 38, 0.12)' },
    high: { label: 'High', color: 'var(--priority-high)', bg: 'rgba(217, 119, 6, 0.12)' },
    medium: { label: 'Medium', color: 'var(--priority-medium)', bg: 'rgba(245, 158, 11, 0.12)' },
    low: { label: 'Low', color: 'var(--priority-low)', bg: 'rgba(22, 163, 74, 0.12)' },
  };

  const current = configs[p] || configs.medium;

  return (
    <span
      data-testid="priority-indicator"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.2rem 0.55rem',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: '600',
        color: current.color,
        backgroundColor: current.bg,
        border: `1px solid ${current.color}33`,
        whiteSpace: 'nowrap'
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: current.color
        }}
      />
      {showLabel && <span>{current.label}</span>}
    </span>
  );
}

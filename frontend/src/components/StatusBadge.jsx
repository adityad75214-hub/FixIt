import React from 'react';

const STATUS_CONFIG = {
  open: { label: 'Open', bg: '#DBEAFE', text: '#1E40AF', dot: '#3B82F6' },
  assigned: { label: 'Assigned', bg: '#EDE9FE', text: '#5B21B6', dot: '#8B5CF6' },
  in_progress: { label: 'In Progress', bg: '#FEF3C7', text: '#92400E', dot: '#F59E0B' },
  on_hold: { label: 'On Hold', bg: '#FCE7F3', text: '#9D174D', dot: '#EC4899' },
  resolved: { label: 'Resolved', bg: '#D1FAE5', text: '#065F46', dot: '#10B981' },
  closed: { label: 'Closed', bg: '#F3F4F6', text: '#374151', dot: '#6B7280' },
  reopened: { label: 'Reopened', bg: '#FEE2E2', text: '#991B1B', dot: '#EF4444' },
};

export default function StatusBadge({ status }) {
  const normalized = (status || 'open').toLowerCase().replace(' ', '_');
  const config = STATUS_CONFIG[normalized] || STATUS_CONFIG.open;

  return (
    <span
      className={`status-badge status-${normalized}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.25rem 0.625rem',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: '600',
        backgroundColor: config.bg,
        color: config.text,
        whiteSpace: 'nowrap'
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: config.dot
        }}
      />
      {config.label}
    </span>
  );
}

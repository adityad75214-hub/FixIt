import React from 'react';
import { Clock, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function SLAIndicator({
  isOverdue = false,
  timeRemainingMinutes = null,
  targetHours = null,
  compact = false
}) {
  let status = 'within';
  let label = 'Within Target';
  let color = 'var(--sla-within)';
  let bg = 'rgba(22, 163, 74, 0.12)';

  if (isOverdue) {
    status = 'overdue';
    label = 'Overdue';
    color = 'var(--sla-overdue)';
    bg = 'rgba(220, 38, 38, 0.12)';
  } else if (timeRemainingMinutes !== null && timeRemainingMinutes <= 120) {
    status = 'risk';
    label = 'At Risk';
    color = 'var(--sla-risk)';
    bg = 'rgba(217, 119, 6, 0.12)';
  }

  const formatRemaining = (mins) => {
    if (mins === null || mins === undefined) return 'N/A';
    if (mins < 0) return `${Math.abs(Math.round(mins / 60))}h overdue`;
    if (mins < 60) return `${mins}m remaining`;
    const hrs = Math.floor(mins / 60);
    const remM = mins % 60;
    return remM > 0 ? `${hrs}h ${remM}m remaining` : `${hrs}h remaining`;
  };

  if (compact) {
    return (
      <span
        data-testid="sla-indicator-compact"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.35rem',
          padding: '0.2rem 0.5rem',
          borderRadius: '9999px',
          fontSize: '0.75rem',
          fontWeight: '600',
          color: color,
          backgroundColor: bg,
          border: `1px solid ${color}33`,
          whiteSpace: 'nowrap'
        }}
      >
        <Clock size={12} />
        {label} ({formatRemaining(timeRemainingMinutes)})
      </span>
    );
  }

  return (
    <div
      data-testid="sla-panel"
      style={{
        border: `1px solid ${color}44`,
        backgroundColor: bg,
        borderRadius: 'var(--radius-md)',
        padding: '0.875rem 1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isOverdue ? (
            <AlertCircle size={16} color={color} />
          ) : (
            <CheckCircle2 size={16} color={color} />
          )}
          <span style={{ fontSize: '0.8125rem', fontWeight: '700', color: color, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            SLA: {label}
          </span>
        </div>
        {targetHours && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Target: {targetHours}h
          </span>
        )}
      </div>

      <div style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-main)' }}>
        {formatRemaining(timeRemainingMinutes)}
      </div>
    </div>
  );
}

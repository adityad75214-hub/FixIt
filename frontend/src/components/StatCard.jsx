import React from 'react';

export default function StatCard({ label, value, subtext, icon: Icon, color = 'var(--brand-blue)', bg = 'var(--brand-blue-light)' }) {
  return (
    <div className="stat-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {subtext && <div className="stat-subtext">{subtext}</div>}
      </div>
      {Icon && (
        <div className="stat-icon" style={{ backgroundColor: bg, color: color }}>
          <Icon size={22} />
        </div>
      )}
    </div>
  );
}

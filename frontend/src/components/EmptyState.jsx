import React from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({ icon: Icon = Inbox, title = 'No records found', description = 'There is currently no data matching your criteria.', action }) {
  return (
    <div style={{
      padding: '3.5rem 1.5rem',
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        backgroundColor: 'var(--surface-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-subtle)',
        marginBottom: '1rem'
      }}>
        <Icon size={28} />
      </div>
      <h4 style={{ fontSize: '1rem', fontWeight: '600', color: '#1E293B', marginBottom: '0.25rem' }}>
        {title}
      </h4>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '360px', marginBottom: action ? '1.25rem' : '0' }}>
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}

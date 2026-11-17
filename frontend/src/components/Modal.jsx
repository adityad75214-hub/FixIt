import React from 'react';
import { X } from 'lucide-react';

export default function Modal({ isOpen, onClose, title, children, maxWidth = '550px' }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
          paddingBottom: '0.75rem',
          borderBottom: '1px solid var(--surface-subtle)'
        }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-main)' }}>{title}</h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-subtle)',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center',
              borderRadius: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>
        <div>
          {children}
        </div>
      </div>
    </div>
  );
}

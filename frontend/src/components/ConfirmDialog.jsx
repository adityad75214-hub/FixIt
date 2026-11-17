import React from 'react';
import { ShieldAlert, Info, CheckCircle, AlertTriangle, X } from 'lucide-react';
import Modal from './Modal';

export default function ConfirmDialog({
  isOpen,
  title = 'Are you sure?',
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'danger',
  onConfirm,
  onCancel,
  isLoading = false
}) {
  if (!isOpen) return null;

  const typeConfig = {
    danger: {
      icon: <ShieldAlert size={24} color="var(--priority-critical)" />,
      btnClass: 'btn-danger'
    },
    warning: {
      icon: <AlertTriangle size={24} color="var(--priority-high)" />,
      btnClass: 'btn-primary'
    },
    info: {
      icon: <Info size={24} color="var(--brand-blue)" />,
      btnClass: 'btn-primary'
    },
    success: {
      icon: <CheckCircle size={24} color="var(--sla-within)" />,
      btnClass: 'btn-primary'
    }
  }[type] || {
    icon: <Info size={24} color="var(--brand-blue)" />,
    btnClass: 'btn-primary'
  };

  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', margin: '0.5rem 0 1.5rem 0' }}>
        <div style={{ flexShrink: 0, marginTop: '2px' }}>
          {typeConfig.icon}
        </div>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
          {message}
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="btn btn-secondary"
        >
          {cancelText}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isLoading}
          className={`btn ${typeConfig.btnClass}`}
        >
          {isLoading ? 'Processing...' : confirmText}
        </button>
      </div>
    </Modal>
  );
}

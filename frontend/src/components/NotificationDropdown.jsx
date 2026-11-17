import React, { useState, useEffect, useRef } from 'react';
import { Bell, Check, Clock, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { notificationService } from '../api/services';

export default function NotificationDropdown() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  const fetchNotifs = async () => {
    try {
      const res = await notificationService.getNotifications();
      setNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (e) {
      console.error("Failed to load notifications", e);
    }
  };

  useEffect(() => {
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 15000); // Polling every 15s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (e) {
      console.error(e);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await notificationService.markAsRead(id);
      setUnreadCount(prev => Math.max(0, prev - 1));
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="btn btn-secondary btn-sm"
        style={{ position: 'relative', padding: '0.5rem', borderRadius: '50%', border: 'none' }}
        title="Notifications"
      >
        <Bell size={20} color="var(--text-muted)" />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '-2px',
            right: '-2px',
            backgroundColor: '#EF4444',
            color: '#FFFFFF',
            fontSize: '0.65rem',
            fontWeight: '700',
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid #FFFFFF'
          }}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="notification-panel" style={{
          position: 'absolute',
          right: 0,
          marginTop: '0.5rem',
          width: '360px',
          backgroundColor: '#FFFFFF',
          borderRadius: '10px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15)',
          border: '1px solid var(--border-color)',
          zIndex: 100,
          overflow: 'hidden'
        }}>
          <div className="notification-panel-header" style={{
            padding: '0.875rem 1rem',
            borderBottom: '1px solid var(--surface-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-main)'
          }}>
            <span style={{ fontWeight: '600', fontSize: '0.875rem' }}>Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--brand-blue)',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                <Check size={14} /> Mark all read
              </button>
            )}
          </div>

          <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-subtle)', fontSize: '0.8125rem' }}>
                No notifications right now
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`notification-item ${n.is_read ? 'is-read' : 'is-unread'}`}
                  onClick={() => !n.is_read && handleMarkRead(n.id)}
                  style={{
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid var(--surface-subtle)',
                    backgroundColor: n.is_read ? '#FFFFFF' : 'var(--brand-blue-light)',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontWeight: n.is_read ? '500' : '600', fontSize: '0.8125rem', color: 'var(--text-main)' }}>
                      {n.title}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>
                      {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem', lineHeight: '1.4' }}>
                    {n.message}
                  </p>
                  {n.link && (
                    <Link
                      to={n.link}
                      onClick={() => setOpen(false)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        fontSize: '0.7rem',
                        color: 'var(--brand-blue)',
                        marginTop: '0.35rem',
                        fontWeight: '500'
                      }}
                    >
                      View ticket <ExternalLink size={10} />
                    </Link>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

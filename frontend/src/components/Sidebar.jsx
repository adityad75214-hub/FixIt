import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Ticket,
  BookOpen,
  Users,
  ShieldAlert,
  BarChart3,
  Clock,
  UserCheck,
  Lightbulb,
  Building2,
  Tags,
  AlertTriangle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export default function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const role = user?.role || 'student';

  const linkStyle = ({ isActive }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.625rem 0.875rem',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: isActive ? '600' : '500',
    color: isActive ? '#FFFFFF' : 'var(--text-subtle)',
    backgroundColor: isActive ? 'var(--brand-blue)' : 'transparent',
    transition: 'all 0.15s ease',
    marginBottom: '0.25rem'
  });

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 40,
            display: 'block'
          }}
          className="sidebar-backdrop"
        />
      )}

      <aside
        style={{
          width: '260px',
          backgroundColor: 'var(--primary-navy)',
          color: '#FFFFFF',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          zIndex: 45,
          transition: 'transform 0.2s ease'
        }}
        className={`sidebar ${isOpen ? 'open' : ''}`}
      >
        <div style={{ padding: '1.25rem 1rem', flex: 1, overflowY: 'auto' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#60A5FA', padding: '0 0.5rem 0.625rem 0.5rem' }}>{t('Main Menu')}
          </div>

          <NavLink to="/dashboard" style={linkStyle} onClick={onClose}>
            <LayoutDashboard size={18} />{t('Dashboard')}
          </NavLink>

          {/* Student & Faculty & Admin Links */}
          {(role === 'student' || role === 'faculty' || role === 'admin') && (
            <NavLink to="/tickets/new" style={linkStyle} onClick={onClose}>
              <PlusCircle size={18} />{t('Report Issue')}
            </NavLink>
          )}

          <NavLink to="/tickets" style={linkStyle} onClick={onClose}>
            <Ticket size={18} />
            {role === 'admin' ? t('All Tickets') : role === 'staff' ? t('Ticket Queue') : t('My Tickets')}
          </NavLink>

          <NavLink to="/knowledge-base" style={linkStyle} onClick={onClose}>
            <BookOpen size={18} />{t('Knowledge Base')}
          </NavLink>
          <NavLink to="/features" style={linkStyle} onClick={onClose}>
            <Lightbulb size={18} />
            {role === 'admin' ? t('Feature Roadmap') : t('Suggest a Feature')}
          </NavLink>

          {/* IT Staff Specific Links */}
          {(role === 'staff' || role === 'admin') && (
            <NavLink to="/incidents" style={linkStyle} onClick={onClose}>
              <AlertTriangle size={18} />{t('Campus Incidents')}
            </NavLink>
          )}
          {role === 'staff' && (
            <>
              <div style={{ fontSize: '0.6875rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#60A5FA', padding: '1.25rem 0.5rem 0.625rem 0.5rem' }}>{t('IT Staff Portal')}
              </div>
              <NavLink to="/tickets?assigned_to_me=true" style={linkStyle} onClick={onClose}>
                <UserCheck size={18} />{t('My Assignments')}
              </NavLink>
            </>
          )}

          {/* Admin Specific Links */}
          {role === 'admin' && (
            <>
              <div style={{ fontSize: '0.6875rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#60A5FA', padding: '1.25rem 0.5rem 0.625rem 0.5rem' }}>{t('Administration')}
              </div>
              <NavLink to="/admin/users" style={linkStyle} onClick={onClose}>
                <Users size={18} />{t('User Directory')}
              </NavLink>
              <NavLink to="/admin/sla" style={linkStyle} onClick={onClose}>
                <Clock size={18} />{t('SLA Policies')}
              </NavLink>
              <NavLink to="/admin/reports" style={linkStyle} onClick={onClose}>
                <BarChart3 size={18} />{t('Analytics & Reports')}
              </NavLink>
              <NavLink to="/admin/audit-logs" style={linkStyle} onClick={onClose}>
                <ShieldAlert size={18} />{t('Audit Logs')}
              </NavLink>
              <NavLink to="/admin/campus" style={linkStyle} onClick={onClose}>
                <Building2 size={18} />{t('Campus Setup')}
              </NavLink>
              <NavLink to="/admin/categories" style={linkStyle} onClick={onClose}>
                <Tags size={18} />{t('Issue Categories')}
              </NavLink>
            </>
          )}
        </div>

        <div style={{ padding: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
          <div>FixIt Campus Support v2.1</div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{t('Campus Support Platform')}</div>
        </div>
      </aside>
    </>
  );
}

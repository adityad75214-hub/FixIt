import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Wrench, LogOut, User as UserIcon, Menu, Moon, Sun } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import NotificationDropdown from './NotificationDropdown';

export default function Navbar({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleLabels = {
    student: { label: t('Student'), bg: 'rgba(37, 99, 235, 0.12)', text: 'var(--brand-blue)' },
    faculty: { label: t('Faculty'), bg: 'rgba(139, 92, 246, 0.12)', text: '#8B5CF6' },
    staff: { label: t('IT Staff'), bg: 'rgba(22, 163, 74, 0.12)', text: '#16A34A' },
    admin: { label: t('Administrator'), bg: 'rgba(220, 38, 38, 0.12)', text: '#DC2626' },
  };

  const roleStyle = roleLabels[user?.role] || roleLabels.student;

  return (
    <header style={{
      height: '64px',
      backgroundColor: 'var(--surface-header)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.5rem',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      transition: 'background-color 0.2s ease, border-color 0.2s ease'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          onClick={onToggleSidebar}
          aria-label={t('Toggle navigation menu')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.375rem',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center'
          }}
          className="sidebar-toggle"
        >
          <Menu size={22} />
        </button>

        <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            backgroundColor: 'var(--brand-blue)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}>
            <Wrench size={20} />
          </div>
          <div>
            <span style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>FixIt</span>
            <span style={{ fontSize: '0.6875rem', display: 'block', color: 'var(--text-muted)', lineHeight: '1', fontWeight: '500' }}>{t('CAMPUS IT HELPDESK')}</span>
          </div>
        </Link>
      </div>

      <div className="navbar-actions" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Dark/Light Theme Toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          style={{
            background: 'none',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.4rem',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Role Pill */}
        <span className="navbar-role" style={{
          backgroundColor: roleStyle.bg,
          color: roleStyle.text,
          fontSize: '0.75rem',
          fontWeight: '700',
          padding: '0.25rem 0.625rem',
          borderRadius: '9999px',
          textTransform: 'uppercase',
          letterSpacing: '0.04em'
        }}>
          {roleStyle.label}
        </span>

        {/* In-app Notification Bell */}
        <NotificationDropdown />

        {/* User Profile Pill */}
        <div className="navbar-user" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', borderLeft: '1px solid var(--border-color)', paddingLeft: '1rem' }}>
          <div className="navbar-user-details" style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.8125rem', fontWeight: '600', color: 'var(--text-main)', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.name}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {user?.department || t('Campus Community')}
            </div>
          </div>

          <Link
            to="/profile"
            aria-label={t('Profile settings')}
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              backgroundColor: 'var(--surface-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-main)',
              border: '1px solid var(--border-color)'
            }}
          >
            <UserIcon size={16} />
          </Link>

          <button
            onClick={handleLogout}
            title={t("Log Out")}
            aria-label={t("Log Out")}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              padding: '0.25rem'
            }}
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  );
}

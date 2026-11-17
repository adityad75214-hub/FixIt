import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Wrench, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const DEMO_MODE_ENABLED = import.meta.env.DEV && import.meta.env.VITE_DEMO_MODE_ENABLED !== 'false';
const PUBLIC_REGISTRATION_ENABLED = import.meta.env.DEV && import.meta.env.VITE_PUBLIC_REGISTRATION_ENABLED !== 'false';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-main)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2rem 1rem'
    }}>
      <div style={{ maxWidth: '440px', width: '100%' }}>
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.75rem' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'var(--primary-navy)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <Wrench size={24} />
            </div>
            <span style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--primary-navy)', letterSpacing: '-0.02em' }}>FixIt</span>
          </Link>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-main)' }}>Sign in to your account</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            College IT Helpdesk & Issue Management System
          </p>
        </div>

        {/* Development-only demo login controls. Disabled in the production build. */}
        {DEMO_MODE_ENABLED && <div style={{
          backgroundColor: 'var(--brand-blue-light)',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          padding: '1rem',
          marginBottom: '1.5rem'
        }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--primary-navy)', marginBottom: '0.5rem', letterSpacing: '0.04em' }}>
            Quick Demo Role Selector (1-Click Fill):
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => handleQuickDemo('admin@college.edu', 'Admin@123')}
              style={{ fontSize: '0.75rem', fontWeight: '600' }}
            >
              👑 Administrator
            </button>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => handleQuickDemo('staff.network@college.edu', 'Staff@123')}
              style={{ fontSize: '0.75rem', fontWeight: '600' }}
            >
              🛠️ IT Staff (Network)
            </button>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => handleQuickDemo('prof.sharma@college.edu', 'Faculty@123')}
              style={{ fontSize: '0.75rem', fontWeight: '600' }}
            >
              🎓 Faculty Member
            </button>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => handleQuickDemo('rahul.student@college.edu', 'Student@123')}
              style={{ fontSize: '0.75rem', fontWeight: '600' }}
            >
              📚 Enrolled Student
            </button>
          </div>
        </div>}

        {/* Login Card */}
        <div className="card" style={{ padding: '2rem' }}>
          {error && (
            <div style={{
              backgroundColor: '#FEE2E2',
              border: '1px solid #FCA5A5',
              color: '#991B1B',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  className="form-control"
                  placeholder="name@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{ paddingLeft: '2.5rem' }}
                />
                <Mail size={18} color="var(--text-subtle)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
              </div>
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <label className="form-label" style={{ marginBottom: 0 }}>Password</label>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{ paddingLeft: '2.5rem' }}
                />
                <Lock size={18} color="var(--text-subtle)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-navy"
              style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Authenticating...' : 'Sign In'} <ArrowRight size={16} />
            </button>
          </form>

          {PUBLIC_REGISTRATION_ENABLED && (
            <div style={{ textAlign: 'center', marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-light)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
              Don't have an account?{' '}
              <Link to="/register" style={{ color: 'var(--brand-blue)', fontWeight: '600' }}>
                Register as Student
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Lock, Wrench } from 'lucide-react';
import { institutionService } from '../api/services';

export default function AcceptInvitationPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const token = params.get('token') || '';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    if (!token) {
      setError('This invitation link is missing its token. Ask your institution administrator for a new invitation.');
      return;
    }
    if (password !== confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      const response = await institutionService.acceptAdminInvitation({ token, password });
      setSuccess(response.data?.message || 'Your administrator account has been created.');
      window.history.replaceState({}, document.title, window.location.pathname);
      setTimeout(() => navigate('/login', { replace: true }), 1800);
    } catch (err) {
      setError(err.response?.data?.detail || 'The invitation could not be accepted. It may have expired or already been used.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem 1rem', background: 'var(--bg-main)' }}>
      <div style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '.6rem', textDecoration: 'none' }}>
            <Wrench size={26} /><strong style={{ fontSize: '1.6rem' }}>FixIt</strong>
          </Link>
          <h1 style={{ marginTop: '1rem' }}>Accept administrator invitation</h1>
          <p style={{ color: 'var(--text-muted)' }}>Create a password to activate your college administrator account.</p>
        </div>
        <div className="card" style={{ padding: '2rem' }}>
          {error && <div className="form-error" role="alert" style={{ marginBottom: '1rem' }}><AlertCircle size={17} /> {error}</div>}
          {success && <div role="status" style={{ marginBottom: '1rem', color: 'var(--success, #15803d)' }}><CheckCircle2 size={17} /> {success}</div>}
          {!success && (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="invite-password">New password</label>
                <input id="invite-password" className="form-control" type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} />
                <small>Use at least 12 characters.</small>
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="invite-confirm-password">Confirm password</label>
                <input id="invite-confirm-password" className="form-control" type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
              </div>
              <button className="btn btn-primary" type="submit" disabled={loading || !token} style={{ width: '100%' }}>
                <Lock size={16} /> {loading ? 'Creating account…' : 'Accept invitation and set password'}
              </button>
            </form>
          )}
          <p style={{ marginTop: '1.25rem', textAlign: 'center' }}><Link to="/login">Return to sign in</Link></p>
        </div>
      </div>
    </div>
  );
}

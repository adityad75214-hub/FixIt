import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Wrench, Eye, EyeOff, ArrowRight, CheckCircle2 } from 'lucide-react';
import { authService } from '../api/services';

export default function PasswordRecoveryPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get('token');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const requestReset = async (event) => {
    event.preventDefault();
    setLoading(true); setError(''); setMessage('');
    try {
      const { data } = await authService.requestPasswordReset({ email });
      setMessage(data.message || 'If an account exists for that email, a password reset link will be sent.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to process the request. Please try again.');
    } finally { setLoading(false); }
  };

  const resetPassword = async (event) => {
    event.preventDefault();
    setError(''); setMessage('');
    if (password !== confirmPassword) { setError('The passwords do not match.'); return; }
    setLoading(true);
    try {
      const { data } = await authService.confirmPasswordReset({ token, new_password: password });
      setMessage(data.message || 'Password reset successfully.');
      window.setTimeout(() => navigate('/login', { replace: true }), 1400);
    } catch (err) {
      setError(err.response?.data?.detail || 'This reset link may have expired. Request a new one.');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-main)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem 1rem' }}>
      <div style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.6rem', textDecoration: 'none' }}>
            <span style={{ width: 42, height: 42, borderRadius: 10, background: 'var(--primary-navy)', color: 'white', display: 'grid', placeItems: 'center' }}><Wrench size={23} /></span>
            <strong style={{ fontSize: '1.7rem', color: 'var(--primary-navy)' }}>FixIt</strong>
          </Link>
          <h2 style={{ color: 'var(--text-main)', marginTop: '1rem' }}>{token ? 'Choose a new password' : 'Recover your password'}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{token ? 'Create a new password for your FixIt account.' : 'Enter your registered email. We will send a secure reset link if the account exists.'}</p>
        </div>
        <div className="card" style={{ padding: '2rem' }}>
          {error && <div role="alert" style={{ color: '#991B1B', background: '#FEE2E2', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem' }}>{error}</div>}
          {message && <div role="status" style={{ color: '#065F46', background: '#ECFDF5', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}><CheckCircle2 size={18} />{message}</div>}
          {!token ? (
            <form onSubmit={requestReset}>
              <div className="form-group"><label className="form-label" htmlFor="reset-email">Registered email</label><input id="reset-email" className="form-control" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
              <button className="btn btn-navy" type="submit" disabled={loading} style={{ width: '100%', padding: '0.75rem' }}>{loading ? 'Sending…' : 'Send reset link'} <ArrowRight size={16} /></button>
            </form>
          ) : (
            <form onSubmit={resetPassword}>
              <div className="form-group"><label className="form-label" htmlFor="new-password">New password</label><div style={{ position: 'relative' }}><input id="new-password" className="form-control" type={showPassword ? 'text' : 'password'} autoComplete="new-password" minLength={12} maxLength={128} value={password} onChange={(e) => setPassword(e.target.value)} required style={{ paddingRight: '3rem' }} /><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((v) => !v)} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', border: 0, background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div><small style={{ color: 'var(--text-muted)' }}>Use at least 12 characters.</small></div>
              <div className="form-group"><label className="form-label" htmlFor="confirm-password">Confirm new password</label><div style={{ position: 'relative' }}><input id="confirm-password" className="form-control" type={showConfirm ? 'text' : 'password'} autoComplete="new-password" minLength={12} maxLength={128} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required style={{ paddingRight: '3rem' }} /><button type="button" aria-label={showConfirm ? 'Hide password' : 'Show password'} onClick={() => setShowConfirm((v) => !v)} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', border: 0, background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>{showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></div>
              <button className="btn btn-navy" type="submit" disabled={loading || password.length < 12 || confirmPassword.length < 12} style={{ width: '100%', padding: '0.75rem' }}>{loading ? 'Updating…' : 'Reset password'} <ArrowRight size={16} /></button>
            </form>
          )}
          <div style={{ textAlign: 'center', marginTop: '1.25rem', fontSize: '0.9rem' }}><Link to="/login" style={{ color: 'var(--brand-blue)', fontWeight: 600 }}>Back to sign in</Link></div>
        </div>
      </div>
    </div>
  );
}

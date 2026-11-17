import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Wrench, Shield, CheckCircle2, Clock, Users, ArrowRight, Search, BookOpen, Laptop, Wifi, Monitor } from 'lucide-react';
import { knowledgeBaseService } from '../api/services';

const DEMO_MODE_ENABLED = import.meta.env.DEV && import.meta.env.VITE_DEMO_MODE_ENABLED !== 'false';
const PUBLIC_REGISTRATION_ENABLED = import.meta.env.DEV && import.meta.env.VITE_PUBLIC_REGISTRATION_ENABLED !== 'false';

export default function LandingPage() {
  const [search, setSearch] = useState('');
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const res = await knowledgeBaseService.getArticles();
        setArticles(res.data.slice(0, 4));
      } catch (e) {
        console.error(e);
      }
    };
    fetchArticles();
  }, []);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-main)', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header style={{
        height: '70px',
        backgroundColor: 'var(--surface-header)',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: 'var(--primary-navy)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}>
            <Wrench size={22} />
          </div>
          <div>
            <span style={{ fontSize: '1.35rem', fontWeight: '800', color: 'var(--primary-navy)' }}>FixIt</span>
            <span style={{ fontSize: '0.65rem', display: 'block', color: 'var(--text-muted)', fontWeight: '600' }}>CAMPUS SUPPORT PLATFORM</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link to="/login" className="btn btn-secondary">
            Sign In
          </Link>
          {PUBLIC_REGISTRATION_ENABLED && (
            <Link to="/register" className="btn btn-navy">
              Register Account
            </Link>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        padding: '4.5rem 2rem',
        background: 'linear-gradient(135deg, var(--primary-navy) 0%, var(--primary-navy-dark) 100%)',
        color: '#FFFFFF',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '850px', margin: '0 auto' }}>
          <span style={{
            display: 'inline-block',
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(8px)',
            color: '#CAD2C5',
            fontSize: '0.8125rem',
            fontWeight: '600',
            padding: '0.35rem 0.85rem',
            borderRadius: '9999px',
            marginBottom: '1.25rem'
          }}>
            Campus Technical Support & Facilities
          </span>
          <h1 style={{ fontSize: '2.75rem', fontWeight: '800', lineHeight: '1.2', marginBottom: '1.25rem', letterSpacing: '-0.03em' }}>
            Campus Support & Issue Resolution Platform
          </h1>
          <p style={{ fontSize: '1.125rem', color: '#E7EDE5', lineHeight: '1.6', marginBottom: '2.5rem', maxWidth: '700px', margin: '0 auto 2.5rem auto' }}>
            Empowering students, faculty, and IT teams with centralized ticket tracking, automated staff routing, transparent SLA resolution, and campus-wide technical transparency.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/login" className="btn btn-primary" style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}>
              Report a Problem <ArrowRight size={18} />
            </Link>
            <Link to="/login" className="btn btn-secondary" style={{ padding: '0.85rem 1.75rem', fontSize: '1rem', backgroundColor: 'rgba(255, 255, 255, 0.1)', color: '#FFFFFF', borderColor: 'rgba(255, 255, 255, 0.2)' }}>
              Track My Ticket
            </Link>
          </div>
        </div>
      </section>

      {/* Development-only demo credentials; omitted from production builds. */}
      {DEMO_MODE_ENABLED && <section style={{ backgroundColor: '#FEF3C7', borderBottom: '1px solid #FDE68A', padding: '1rem 2rem' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#92400E', fontWeight: '500' }}>
            <span style={{ fontWeight: '700' }}>Demo Accounts Available:</span>
            <span>Admin (<code>admin@college.edu</code>) • Staff (<code>staff.network@college.edu</code>) • Faculty (<code>prof.sharma@college.edu</code>) • Student (<code>rahul.student@college.edu</code>)</span>
          </div>
          <Link to="/login" style={{ fontSize: '0.8125rem', fontWeight: '700', color: '#B45309', textDecoration: 'underline' }}>
            Go to Quick Login →
          </Link>
        </div>
      </section>}

      {/* Feature Highlights */}
      <section style={{ padding: '4rem 2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '1.875rem', fontWeight: '700', color: 'var(--primary-navy)' }}>Built for the Modern Campus</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginTop: '0.5rem' }}>Full lifecycle problem resolution designed for academic excellence.</p>
        </div>

        <div className="grid-3">
          <div className="card">
            <div style={{ width: '48px', height: '48px', borderRadius: '10px', backgroundColor: 'var(--brand-blue-light)', color: 'var(--brand-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem' }}>
              <Clock size={24} />
            </div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '0.5rem' }}>SLA-Backed Resolution</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: '1.6' }}>
              Strict resolution targets from 2 hours for critical classroom equipment to 72 hours for routine software setups, complete with countdowns and breach alerts.
            </p>
          </div>

          <div className="card">
            <div style={{ width: '48px', height: '48px', borderRadius: '10px', backgroundColor: '#ECFDF5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem' }}>
              <Shield size={24} />
            </div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '0.5rem' }}>Role-Based Access Control</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: '1.6' }}>
              Strict permissions for Students, Faculty, IT Staff, and Administrators. Confidential internal notes remain invisible to general users.
            </p>
          </div>

          <div className="card">
            <div style={{ width: '48px', height: '48px', borderRadius: '10px', backgroundColor: '#FAF5FF', color: '#9333EA', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem' }}>
              <Users size={24} />
            </div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '0.5rem' }}>Intelligent Staff Routing</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: '1.6' }}>
              Automatic ticket assignment balances active staff workload and matches problem categories to specialized hardware, network, and systems technicians.
            </p>
          </div>
        </div>
      </section>

      {/* Self-Service Knowledge Base */}
      <section style={{ padding: '3.5rem 2rem', backgroundColor: 'var(--surface-header)', borderTop: '1px solid var(--border-color)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--primary-navy)' }}>Self-Service Knowledge Base</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.925rem' }}>Find instant answers to common campus support questions before logging a ticket.</p>
            </div>
            <Link to="/login" className="btn btn-secondary">
              Browse All Articles
            </Link>
          </div>

          <div className="grid-2">
            {articles.map((art) => (
              <div key={art.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--brand-blue)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {art.category}
                  </span>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: '600', color: 'var(--text-main)', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
                    {art.title}
                  </h4>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                    {art.content.slice(0, 160)}...
                  </p>
                </div>
                <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                  <span>{art.helpful_count} people found this helpful</span>
                  <Link to="/login" style={{ color: 'var(--brand-blue)', fontWeight: '600' }}>Read Guide →</Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ marginTop: 'auto', backgroundColor: 'var(--text-main)', color: 'var(--text-subtle)', padding: '2.5rem 2rem', fontSize: '0.875rem' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span style={{ color: '#FFFFFF', fontWeight: '700', fontSize: '1.1rem' }}>FixIt Campus Support</span>
            <p style={{ marginTop: '0.25rem', fontSize: '0.8125rem' }}>Campus-wide service requests and issue resolution platform.</p>
          </div>
          <div>
            &copy; 2026 Campus IT Department. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

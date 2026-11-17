import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Wrench, ArrowRight, UserRound, GraduationCap, ShieldCheck, Clock3,
  UsersRound, BookOpen, FileText, Layers3, CheckCircle2, Menu, X
} from 'lucide-react';
import { knowledgeBaseService } from '../api/services';
import './LandingPage.css';

const PUBLIC_REGISTRATION_ENABLED = import.meta.env.VITE_PUBLIC_REGISTRATION_ENABLED === 'true';

export default function LandingPage() {
  const [articles, setArticles] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    let active = true;
    knowledgeBaseService.getArticles()
      .then(({ data }) => { if (active) setArticles((data || []).slice(0, 3)); })
      .catch(() => { if (active) setArticles([]); });
    return () => { active = false; };
  }, []);

  return (
    <div className="landing-page">
      <header className="landing-nav">
        <Link to="/" className="landing-brand" aria-label="FixIt home">
          <span className="landing-brand-mark"><Wrench size={21} /></span>
          <span><strong>FixIt</strong><small>CAMPUS ISSUE MANAGEMENT</small></span>
        </Link>
        <button className="landing-menu-toggle" aria-label="Toggle navigation" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
        <nav className={menuOpen ? 'landing-links is-open' : 'landing-links'}>
          <a href="#home" onClick={() => setMenuOpen(false)}>Home</a>
          <a href="#about" onClick={() => setMenuOpen(false)}>About</a>
          <a href="#how-it-works" onClick={() => setMenuOpen(false)}>How it works</a>
          <a href="#contact" onClick={() => setMenuOpen(false)}>Contact</a>
          <Link className="landing-nav-login" to="/login">Login</Link>
        </nav>
      </header>

      <main>
        <section className="landing-hero" id="home">
          <div className="landing-hero-image" />
          <div className="landing-hero-shade" />
          <div className="landing-hero-content">
            <span className="landing-eyebrow">CAMPUS ISSUE MANAGEMENT PLATFORM</span>
            <h1>Your Campus.<br />Your Issues.<br /><em>One Solution.</em></h1>
            <p>Report campus problems, track progress, and get them resolved through one simple platform.</p>
            <div className="landing-role-cards">
              <Link to={PUBLIC_REGISTRATION_ENABLED ? '/register?role=student' : '/login'} className="landing-role-card">
                <span className="landing-role-icon"><UserRound size={27} /></span>
                <span><strong>Student</strong><small>{PUBLIC_REGISTRATION_ENABLED ? 'Register / Login' : 'Login'} <ArrowRight size={13} /></small></span>
              </Link>
              <Link to={PUBLIC_REGISTRATION_ENABLED ? '/register?role=faculty' : '/login'} className="landing-role-card">
                <span className="landing-role-icon"><GraduationCap size={29} /></span>
                <span><strong>Faculty</strong><small>{PUBLIC_REGISTRATION_ENABLED ? 'Register / Login' : 'Login'} <ArrowRight size={13} /></small></span>
              </Link>
            </div>
            <Link to="/login" className="landing-staff-login"><ShieldCheck size={18} /> Staff &amp; Administrator Login <ArrowRight size={16} /></Link>
          </div>
          <div className="landing-hero-bottom">
            <div><FileText size={22} /><span><strong>Report</strong><small>Submit an issue</small></span></div>
            <div><Layers3 size={22} /><span><strong>Track</strong><small>Follow its status</small></span></div>
            <div><CheckCircle2 size={23} /><span><strong>Resolve</strong><small>Get updates</small></span></div>
          </div>
        </section>

        <section className="landing-features" id="about">
          <div className="landing-section-heading">
            <span className="landing-section-kicker">A clearer way to get support</span>
            <h2>Built for the modern campus</h2>
            <p>From the first report to the final resolution, every request has a clear path forward.</p>
          </div>
          <div className="landing-feature-grid">
            <article className="landing-feature-card"><span className="feature-icon feature-icon-sage"><Clock3 size={22} /></span><h3>SLA-backed resolution</h3><p>Clear response targets, priority handling, countdowns and breach alerts help teams resolve issues on time.</p></article>
            <article className="landing-feature-card"><span className="feature-icon feature-icon-mint"><ShieldCheck size={22} /></span><h3>Role-based access control</h3><p>Students, faculty, support staff and administrators see the tools and information appropriate to their role.</p></article>
            <article className="landing-feature-card"><span className="feature-icon feature-icon-lilac"><UsersRound size={22} /></span><h3>Intelligent staff routing</h3><p>Requests can be assigned to the right support team based on category, skills and current workload.</p></article>
          </div>
        </section>

        <section className="landing-knowledge" id="how-it-works">
          <div className="landing-knowledge-copy">
            <span className="landing-section-kicker">Find an answer first</span>
            <h2>Self-service knowledge base</h2>
            <p>Explore helpful guides and answers to common campus support questions before raising a ticket.</p>
            <Link to="/knowledge-base" className="landing-outline-button">Browse all articles <ArrowRight size={15} /></Link>
          </div>
          <div className="landing-article-list">
            {articles.length ? articles.map((article) => (
              <Link to="/login" className="landing-article" key={article.id}>
                <BookOpen size={18} /><span><small>{article.category || 'GUIDE'}</small><strong>{article.title}</strong></span><ArrowRight size={16} />
              </Link>
            )) : <div className="landing-article landing-article-placeholder"><BookOpen size={19} /><span><strong>Campus help, all in one place</strong><small>Sign in to browse support articles and guides.</small></span></div>}
          </div>
        </section>

        <section className="landing-cta" id="contact">
          <div><span className="landing-section-kicker">One campus. One support journey.</span><h2>Need help with something on campus?</h2><p>Sign in to raise a request or check the progress of an existing ticket.</p></div>
          <Link to="/login" className="landing-cta-button">Go to FixIt <ArrowRight size={17} /></Link>
        </section>
      </main>

      <footer className="landing-footer">
        <Link to="/" className="landing-footer-brand"><Wrench size={18} /><strong>FixIt Campus Support</strong></Link>
        <span>Campus-wide service requests and issue resolution.</span>
        <small>© {new Date().getFullYear()} FixIt. All rights reserved.</small>
      </footer>
    </div>
  );
}

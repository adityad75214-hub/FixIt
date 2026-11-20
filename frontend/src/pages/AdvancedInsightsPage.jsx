import React, { useState } from 'react';
import { Sparkles, Users, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';
import { advancedInsightsService } from '../api/services';

export default function AdvancedInsightsPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [classification, setClassification] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState('');
  const [error, setError] = useState('');

  const run = async (key, action) => {
    setLoading(key); setError('');
    try { await action(); } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to load this insight. Please try again.');
    } finally { setLoading(''); }
  };

  const classify = () => run('classify', async () => {
    const response = await advancedInsightsService.classifyTicket({ title, description });
    setClassification(response.data);
  });
  const recommend = () => run('recommend', async () => {
    const response = await advancedInsightsService.recommendStaff({ category });
    setRecommendations(response.data);
  });
  const loadForecast = () => run('forecast', async () => {
    const response = await advancedInsightsService.getTicketForecast();
    setForecast(response.data);
  });

  const panel = { background: 'var(--surface, #fff)', border: '1px solid var(--border, #e5e7eb)', borderRadius: 12, padding: 20, marginBottom: 18 };
  const field = { width: '100%', padding: '10px 12px', border: '1px solid var(--border, #d1d5db)', borderRadius: 8, background: 'var(--surface, #fff)', color: 'var(--text-main, #111827)', marginTop: 6 };
  const button = { border: 0, borderRadius: 8, padding: '10px 14px', background: 'var(--brand-blue, #244b6b)', color: '#fff', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8, marginTop: 12 };

  return <div className="page-wrapper">
    <div className="page-header">
      <div><h1 className="page-title">Advanced Insights</h1>
      <p className="page-subtitle">Decision support for ticket triage, staffing and campus planning.</p></div>
    </div>
    {error && <div role="alert" style={{ ...panel, borderColor: '#ef4444', color: '#b91c1c' }}><AlertCircle size={16} style={{ verticalAlign: 'middle', marginRight: 8 }} />{error}</div>}
    <section style={panel}>
      <h2 style={{ fontSize: 18, margin: '0 0 6px' }}><Sparkles size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Ticket category suggestions</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Explainable keyword suggestions. This is a baseline, not a trained AI model; confirm the category manually.</p>
      <label>Issue title<input style={field} value={title} maxLength={150} onChange={e => setTitle(e.target.value)} placeholder="e.g. Wi-Fi not connecting in lab" /></label>
      <label style={{ display: 'block', marginTop: 12 }}>Issue description<textarea style={{ ...field, minHeight: 90 }} value={description} maxLength={5000} onChange={e => setDescription(e.target.value)} placeholder="Describe what happened and where..." /></label>
      <button style={button} disabled={loading === 'classify' || title.trim().length < 3 || description.trim().length < 5} onClick={classify}>{loading === 'classify' ? 'Analyzing…' : 'Suggest categories'}</button>
      {classification && <div style={{ marginTop: 14 }}>
        <strong>{classification.message}</strong>
        {classification.suggestions?.map(item => <div key={item.category} style={{ padding: '10px 0', borderBottom: '1px solid var(--border, #eee)' }}>
          <strong>{item.category}</strong> · {Math.round(item.confidence * 100)}% heuristic score
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Matched: {item.matched_terms.join(', ')}</div>
        </div>)}
      </div>}
    </section>
    <section style={panel}>
      <h2 style={{ fontSize: 18, margin: '0 0 6px' }}><Users size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Staff recommendations</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Only active staff explicitly qualified for the selected category are considered. Ranking uses current workload and historical resolution rate.</p>
      <label>Issue category<input style={field} value={category} maxLength={80} onChange={e => setCategory(e.target.value)} placeholder="Enter the exact configured staff specialization" /></label>
      <button style={button} disabled={loading === 'recommend' || category.trim().length < 2} onClick={recommend}>{loading === 'recommend' ? 'Ranking…' : 'Find suitable staff'}</button>
      {recommendations && <div style={{ marginTop: 14 }}>
        <strong>{recommendations.message || 'Ranked eligible staff'}</strong>
        {recommendations.recommendations?.map((person, index) => <div key={person.staff_id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border, #eee)' }}>
          <strong>{index + 1}. {person.name}</strong> · Score {person.score}
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{person.active_tickets} active · {person.resolved_tickets} resolved · {person.resolution_rate === null ? 'No resolution history' : person.resolution_rate + '% resolution rate'}</div>
        </div>)}
      </div>}
    </section>
    <section style={panel}>
      <h2 style={{ fontSize: 18, margin: '0 0 6px' }}><TrendingUp size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Ticket volume forecast</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>A simple tenant-local trend estimate. It is not a guarantee and is withheld when fewer than three months of history exist.</p>
      <button style={button} disabled={loading === 'forecast'} onClick={loadForecast}><RefreshCw size={15} />{loading === 'forecast' ? 'Calculating…' : 'Calculate forecast'}</button>
      {forecast && <div style={{ marginTop: 14 }}>
        {forecast.available ? <>
          <div style={{ fontSize: 26, fontWeight: 700 }}>{forecast.forecast.estimated_tickets} tickets</div>
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Estimated next observed month · historical mean absolute error: {forecast.forecast.mean_absolute_error}</div>
        </> : <strong>{forecast.message}</strong>}
        {forecast.observations?.length > 0 && <ul>{forecast.observations.map(item => <li key={item.month}>{item.month}: {item.tickets} tickets</li>)}</ul>}
        <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>{forecast.message}</p>
      </div>}
    </section>
  </div>;
}

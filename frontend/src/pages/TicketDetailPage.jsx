import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Ticket,
  Clock,
  User,
  Building,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Lock,
  Send,
  Star,
  RefreshCw,
  Users,
  ShieldAlert,
  ArrowLeft
} from 'lucide-react';
import { ticketService, commentService, assignmentService, feedbackService, userService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import Modal from '../components/Modal';

export default function TicketDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [attachmentUrl, setAttachmentUrl] = useState('');
  const [commentAttachments, setCommentAttachments] = useState([]);
  const [isInternalNote, setIsInternalNote] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);

  // Modals state
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState('');
  const [statusNote, setStatusNote] = useState('');

  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedStaffId, setSelectedStaffId] = useState('');
  const [assignNote, setAssignNote] = useState('');

  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [rating, setRating] = useState(5);
  const [feedbackComments, setFeedbackComments] = useState('');

  const [priorityModalOpen, setPriorityModalOpen] = useState(false);
  const [newPriority, setNewPriority] = useState('medium');
  const [priorityReason, setPriorityReason] = useState('');

  const fetchTicketData = async () => {
    try {
      const [ticketRes, commentsRes] = await Promise.all([
        ticketService.getTicket(id),
        commentService.getComments(id)
      ]);
      setTicket(ticketRes.data);
      setComments(commentsRes.data || []);
      setNewPriority(ticketRes.data.priority);
    } catch (err) {
      console.error("Failed to load ticket details:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTicketData();
    if (user?.role === 'admin') {
      userService.getStaff()
        .then(res => setStaffList(res.data || []))
        .catch(err => console.error(err));
    }
  }, [id]);

  const handlePostComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setSubmittingComment(true);
    try {
      await commentService.addComment(id, {
        content: commentText,
        is_internal: isInternalNote,
        attachments: commentAttachments
      });
      setCommentText('');
      setAttachmentUrl('');
      setCommentAttachments([]);
      setIsInternalNote(false);
      fetchTicketData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to post comment");
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleStatusChangeSubmit = async () => {
    try {
      await ticketService.updateStatus(id, {
        status: targetStatus,
        note: statusNote,
        hold_reason: targetStatus === 'on_hold' ? statusNote : undefined,
        resolution_notes: targetStatus === 'resolved' ? statusNote : undefined
      });
      setStatusModalOpen(false);
      setStatusNote('');
      fetchTicketData();
    } catch (err) {
      alert(err.response?.data?.detail || "Invalid status transition");
    }
  };

  const handleAssignSubmit = async () => {
    try {
      await assignmentService.assignTicket(id, {
        staff_id: selectedStaffId,
        note: assignNote
      });
      setAssignModalOpen(false);
      setAssignNote('');
      fetchTicketData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to assign staff member");
    }
  };

  const handleAutoAssign = async () => {
    try {
      await assignmentService.autoAssign(id);
      fetchTicketData();
    } catch (err) {
      alert(err.response?.data?.detail || "Auto-assignment failed");
    }
  };

  const handleFeedbackSubmit = async () => {
    try {
      await feedbackService.submitFeedback({
        ticket_id: ticket.ticket_id,
        rating: rating,
        comments: feedbackComments
      });
      setFeedbackModalOpen(false);
      fetchTicketData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to submit feedback");
    }
  };

  const handlePrioritySubmit = async () => {
    try {
      await ticketService.updatePriority(id, {
        priority: newPriority,
        reason: priorityReason
      });
      setPriorityModalOpen(false);
      setPriorityReason('');
      fetchTicketData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update priority");
    }
  };

  if (loading) {
    return <div className="page-wrapper" style={{ textAlign: 'center', padding: '4rem' }}>Loading ticket...</div>;
  }

  if (!ticket) {
    return <div className="page-wrapper" style={{ textAlign: 'center', padding: '4rem' }}>Ticket not found or access denied.</div>;
  }

  const isStaffOrAdmin = ['staff', 'admin'].includes(user?.role);
  const isAdmin = user?.role === 'admin';
  const canWorkTicket = isAdmin || (user?.role === 'staff' && ticket.assigned_to?.id === user?.id);
  const canComment = user?.role !== 'staff' || ticket.assigned_to?.id === user?.id;
  const isCreator = ticket.created_by?.id === user?.id;

  return (
    <div className="page-wrapper">
      {/* Back button & Ticket Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <button
          onClick={() => navigate(-1)}
          className="btn btn-secondary btn-sm"
          style={{ marginBottom: '1rem' }}
        >
          <ArrowLeft size={14} /> Back to Tickets
        </button>

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'monospace', color: 'var(--brand-blue)' }}>
                {ticket.ticket_id}
              </span>
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--text-main)' }}>{ticket.title}</h1>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Reported on {new Date(ticket.created_at).toLocaleString()} by {ticket.created_by?.name} ({ticket.created_by?.role})
            </p>
          </div>

          {/* SLA Countdown pill */}
          <div style={{
            backgroundColor: ticket.is_overdue ? '#FEE2E2' : 'var(--brand-blue-light)',
            border: `1px solid ${ticket.is_overdue ? '#FCA5A5' : '#BFDBFE'}`,
            borderRadius: '10px',
            padding: '0.75rem 1.25rem',
            textAlign: 'right'
          }}>
            <div style={{ fontSize: '0.75rem', fontWeight: '600', color: ticket.is_overdue ? '#991B1B' : 'var(--brand-blue)', textTransform: 'uppercase' }}>
              {ticket.is_overdue ? '⚠️ SLA Breach' : 'SLA Target'}
            </div>
            <div style={{ fontSize: '1.125rem', fontWeight: '700', color: ticket.is_overdue ? '#EF4444' : 'var(--brand-blue)' }}>
              {ticket.status === 'resolved' || ticket.status === 'closed'
                ? 'Resolved'
                : ticket.is_overdue
                ? 'OVERDUE'
                : `${Math.floor((ticket.time_remaining_minutes || 0) / 60)}h ${(ticket.time_remaining_minutes || 0) % 60}m remaining`
              }
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        {/* Left Column: Details, Comments, Timeline */}
        <div>
          {/* Ticket Description Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '0.75rem' }}>
              Problem Description
            </h3>
            <p style={{ fontSize: '0.9375rem', color: 'var(--text-muted)', whiteHeight: '1.6', whiteSpace: 'pre-line' }}>
              {ticket.description}
            </p>

            {ticket.resolution_notes && (
              <div style={{ marginTop: '1.25rem', padding: '1rem', backgroundColor: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: '8px' }}>
                <div style={{ fontWeight: '700', fontSize: '0.875rem', color: '#065F46', marginBottom: '0.25rem' }}>
                  Technician Resolution Summary:
                </div>
                <p style={{ fontSize: '0.875rem', color: '#047857' }}>
                  {ticket.resolution_notes}
                </p>
              </div>
            )}
          </div>

          {/* Comments & Communication Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <h3 className="card-title">
                <MessageSquare size={18} color="var(--brand-blue)" />
                Communication & Updates ({comments.length})
              </h3>
            </div>

            {/* Existing Comments */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
              {comments.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-subtle)', fontSize: '0.875rem' }}>
                  No comments posted yet.
                </div>
              ) : (
                comments.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      padding: '1rem',
                      borderRadius: '8px',
                      backgroundColor: c.is_internal ? '#FFFBEB' : 'var(--bg-main)',
                      border: `1px solid ${c.is_internal ? '#FCD34D' : 'var(--border-color)'}`,
                      position: 'relative'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: '600', fontSize: '0.875rem', color: 'var(--text-main)' }}>
                          {c.author.name}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                          ({c.author.role})
                        </span>
                        {c.is_internal && (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            backgroundColor: '#FEF3C7',
                            color: '#92400E',
                            fontSize: '0.7rem',
                            fontWeight: '700',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            border: '1px solid #FDE68A'
                          }}>
                            <Lock size={10} /> STAFF INTERNAL NOTE
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                        {new Date(c.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: '1.5', whiteSpace: 'pre-line' }}>
                      {c.content}
                    </p>
                    {c.attachments?.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                        {c.attachments.map((url, index) => (
                          <a key={index} href={url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
                            View attachment {index + 1}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Only the ticket owner, assigned technician, or an administrator may post comments. */}
            {canComment && <form onSubmit={handlePostComment}>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <textarea
                  className="form-control"
                  placeholder={isInternalNote ? "Enter private internal troubleshooting note..." : "Add a public reply or question for IT staff..."}
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={3}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label className="form-label">Attach a file or image using a secure HTTPS link (up to 5)</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input type="url" className="form-control" placeholder="https://..." value={attachmentUrl} onChange={(e) => setAttachmentUrl(e.target.value)} />
                  <button type="button" className="btn btn-secondary btn-sm" disabled={!attachmentUrl.startsWith('https://') || commentAttachments.length >= 5} onClick={() => { setCommentAttachments(prev => [...prev, attachmentUrl.trim()]); setAttachmentUrl(''); }}>Add link</button>
                </div>
                {commentAttachments.map((url, index) => <div key={url} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginTop: '0.35rem' }}><span>Attachment {index + 1}: {url}</span><button type="button" className="btn btn-secondary btn-sm" onClick={() => setCommentAttachments(prev => prev.filter((_, i) => i !== index))}>Remove</button></div>)}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {isStaffOrAdmin ? (
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', color: '#B45309', fontWeight: '600', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={isInternalNote}
                      onChange={(e) => setIsInternalNote(e.target.checked)}
                      style={{ accentColor: '#D97706' }}
                    />
                    <Lock size={14} /> Make this an Internal Staff Note (Invisible to students)
                  </label>
                ) : <div />}

                <button
                  type="submit"
                  className="btn btn-primary btn-sm"
                  disabled={submittingComment}
                >
                  <Send size={14} /> {submittingComment ? 'Posting...' : isInternalNote ? 'Post Internal Note' : 'Send Reply'}
                </button>
              </div>
            </form>}
          </div>

          {/* Activity Timeline Card */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Clock size={18} color="var(--brand-blue)" />
                Ticket Activity Timeline
              </h3>
            </div>
            <div className="timeline">
              {(ticket.timeline || []).map((event, idx) => (
                <div key={idx} className="timeline-item">
                  <div className="timeline-dot" />
                  <div className="timeline-meta">
                    {new Date(event.timestamp).toLocaleString()} • {event.actor_name} ({event.actor_role})
                  </div>
                  <div className="timeline-title">
                    {event.action.replace(/_/g, ' ')}
                  </div>
                  {event.note && (
                    <div className="timeline-note">
                      {event.note}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Actions, Metadata, Assignment */}
        <div>
          {/* Actions & Lifecycle Management Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '1rem' }}>
              Ticket Actions
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {/* Staff / Admin Actions */}
              {canWorkTicket && (
                <>
                  {ticket.status !== 'in_progress' && ticket.status !== 'resolved' && ticket.status !== 'closed' && (
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        setTargetStatus('in_progress');
                        setStatusModalOpen(true);
                      }}
                    >
                      Start Investigation (In Progress)
                    </button>
                  )}

                  {ticket.status === 'in_progress' && (
                    <>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          setTargetStatus('on_hold');
                          setStatusModalOpen(true);
                        }}
                      >
                        Place On Hold
                      </button>

                      <button
                        className="btn btn-navy"
                        style={{ backgroundColor: '#10B981' }}
                        onClick={() => {
                          setTargetStatus('resolved');
                          setStatusModalOpen(true);
                        }}
                      >
                        <CheckCircle2 size={16} /> Mark as Resolved
                      </button>
                    </>
                  )}

                  {ticket.status === 'on_hold' && (
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        setTargetStatus('in_progress');
                        setStatusModalOpen(true);
                      }}
                    >
                      Resume Work
                    </button>
                  )}

                  {isAdmin && (
                    <>
                      <button
                        className="btn btn-secondary"
                        onClick={() => setAssignModalOpen(true)}
                      >
                        <Users size={16} /> {ticket.assigned_to ? 'Reassign Staff' : 'Assign to IT Staff'}
                      </button>

                      {!ticket.assigned_to && (
                        <button
                          className="btn btn-secondary"
                          onClick={handleAutoAssign}
                        >
                          <RefreshCw size={14} /> Auto-Assign via Load Balance
                        </button>
                      )}

                      <button
                        className="btn btn-secondary"
                        onClick={() => setPriorityModalOpen(true)}
                      >
                        <AlertCircle size={16} /> Change Priority Level
                      </button>
                    </>
                  )}
                </>
              )}

              {/* Student/Faculty Resolution Confirmation or Reopen */}
              {isCreator && ticket.status === 'resolved' && (
                <>
                  <button
                    className="btn btn-navy"
                    style={{ backgroundColor: '#10B981' }}
                    onClick={() => {
                      setTargetStatus('closed');
                      setStatusModalOpen(true);
                    }}
                  >
                    <CheckCircle2 size={16} /> Confirm Resolution & Close
                  </button>

                  <button
                    className="btn btn-danger"
                    onClick={() => {
                      setTargetStatus('reopened');
                      setStatusModalOpen(true);
                    }}
                  >
                    Issue Not Fixed? Reopen Ticket
                  </button>

                  {!ticket.has_feedback && (
                    <button
                      className="btn btn-primary"
                      onClick={() => setFeedbackModalOpen(true)}
                    >
                      <Star size={16} /> Rate Support Service
                    </button>
                  )}
                </>
              )}

              {isCreator && ticket.status === 'closed' && !ticket.has_feedback && (
                <button
                  className="btn btn-primary"
                  onClick={() => setFeedbackModalOpen(true)}
                >
                  <Star size={16} /> Rate Support Service
                </button>
              )}
            </div>
          </div>

          {/* Details Card */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '1rem' }}>
              Ticket Information
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem', fontSize: '0.875rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Problem Type</span>
                <span style={{ fontWeight: '600', color: 'var(--text-main)', textTransform: 'capitalize' }}>{(ticket.problem_domain || 'technical').replaceAll('_', ' ')}</span>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Category & Subcategory</span>
                <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{ticket.category}</span>
                {ticket.subcategory && <span style={{ color: 'var(--text-muted)' }}> • {ticket.subcategory}</span>}
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>{ticket.location_type === 'campus' || !ticket.location_type ? 'Campus Location' : 'Location'}</span>
                <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>
                  {ticket.building} ({ticket.floor}) - {ticket.room}
                </span>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Department & Users Impacted</span>
                <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>
                  {ticket.department || 'Campus Wide'} ({ticket.affected_users || 1} people)
                </span>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Assigned Staff</span>
                {ticket.assigned_to ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.2rem' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'var(--brand-blue-light)', color: 'var(--brand-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '700', fontSize: '0.75rem' }}>
                      {ticket.assigned_to.name.charAt(0)}
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{ticket.assigned_to.name}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{ticket.assigned_to.email}</div>
                    </div>
                  </div>
                ) : (
                  <span style={{ color: 'var(--text-subtle)', fontStyle: 'italic' }}>Unassigned (In queue)</span>
                )}
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>SLA Target Resolution</span>
                <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{ticket.sla_target_hours} hours target</span>
              </div>

              {ticket.linked_incident_id && (
                <div style={{ backgroundColor: '#FEF3C7', padding: '0.5rem 0.75rem', borderRadius: '6px' }}>
                  <span style={{ color: '#92400E', fontSize: '0.75rem', fontWeight: '700' }}>Linked Master Incident:</span>
                  <div style={{ fontWeight: '600', color: '#B45309', fontSize: '0.8125rem' }}>{ticket.linked_incident_id}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Status Modal */}
      <Modal
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title={`Update Status to ${targetStatus.replace('_', ' ').toUpperCase()}`}
      >
        <div className="form-group">
          <label className="form-label">
            {targetStatus === 'on_hold' ? 'Reason for Placing On Hold *' : targetStatus === 'resolved' ? 'Resolution Steps & Outcome *' : 'Status Note / Troubleshooting Update'}
          </label>
          <textarea
            className="form-control"
            rows={3}
            placeholder="Enter details..."
            value={statusNote}
            onChange={(e) => setStatusNote(e.target.value)}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => setStatusModalOpen(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleStatusChangeSubmit}>Confirm Update</button>
        </div>
      </Modal>

      {/* Staff Assignment Modal */}
      <Modal
        isOpen={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Assign Ticket to IT Staff Member"
      >
        <div className="form-group">
          <label className="form-label">Select Staff Member</label>
          <select
            className="form-control"
            value={selectedStaffId}
            onChange={(e) => setSelectedStaffId(e.target.value)}
          >
            <option value="">Choose technician...</option>
            {staffList.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.specialization?.join(', ') || 'General'}) - {s.active_tickets_count} active tickets
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Assignment Note (Optional)</label>
          <input
            type="text"
            className="form-control"
            placeholder="Special instructions..."
            value={assignNote}
            onChange={(e) => setAssignNote(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => setAssignModalOpen(false)}>Cancel</button>
          <button className="btn btn-navy" disabled={!selectedStaffId} onClick={handleAssignSubmit}>Assign Staff</button>
        </div>
      </Modal>

      {/* Priority Modal */}
      <Modal
        isOpen={priorityModalOpen}
        onClose={() => setPriorityModalOpen(false)}
        title="Override Priority Level"
      >
        <div className="form-group">
          <label className="form-label">New Priority Level</label>
          <select
            className="form-control"
            value={newPriority}
            onChange={(e) => setNewPriority(e.target.value)}
          >
            <option value="low">Low (72h SLA)</option>
            <option value="medium">Medium (24h SLA)</option>
            <option value="high">High (8h SLA)</option>
            <option value="critical">Critical (2h SLA)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Reason for Override *</label>
          <input
            type="text"
            className="form-control"
            placeholder="e.g. Impacting ongoing classroom examination"
            value={priorityReason}
            onChange={(e) => setPriorityReason(e.target.value)}
            required
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => setPriorityModalOpen(false)}>Cancel</button>
          <button className="btn btn-navy" onClick={handlePrioritySubmit}>Apply Priority</button>
        </div>
      </Modal>

      {/* 1-5 Star Feedback Modal */}
      <Modal
        isOpen={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
        title="Rate IT Support Service"
      >
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            How satisfied are you with the technical resolution provided by IT support?
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: star <= rating ? '#F59E0B' : '#CBD5E1',
                  transition: 'transform 0.15s ease'
                }}
              >
                <Star size={32} fill={star <= rating ? '#F59E0B' : 'none'} />
              </button>
            ))}
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: '700', color: '#D97706', marginTop: '0.5rem' }}>
            {rating === 5 ? 'Excellent Service!' : rating === 4 ? 'Very Good' : rating === 3 ? 'Satisfactory' : rating === 2 ? 'Needs Improvement' : 'Poor'}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Comments or Feedback (Optional)</label>
          <textarea
            className="form-control"
            rows={3}
            placeholder="Share what went well or how our IT team can improve..."
            value={feedbackComments}
            onChange={(e) => setFeedbackComments(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => setFeedbackModalOpen(false)}>Cancel</button>
          <button className="btn btn-navy" onClick={handleFeedbackSubmit}>Submit Rating</button>
        </div>
      </Modal>
    </div>
  );
}

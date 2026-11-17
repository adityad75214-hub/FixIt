import { describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../src/App';
import PriorityIndicator from '../src/components/PriorityIndicator';
import SLAIndicator from '../src/components/SLAIndicator';
import ConfirmDialog from '../src/components/ConfirmDialog';

describe('FixIt Design System & Navigation Suite', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders landing page with platform branding and sign in link', () => {
    render(<App />);
    const headings = screen.getAllByText(/Campus Support/i);
    expect(headings.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/FixIt/i).length).toBeGreaterThan(0);
  });

  it('renders PriorityIndicator with correct colors and NO SLA text', () => {
    const { rerender } = render(<PriorityIndicator priority="critical" />);
    const criticalElement = screen.getByTestId('priority-indicator');
    expect(criticalElement.textContent).toBe('Critical');
    // Ensure no SLA text inside priority badge
    expect(criticalElement.textContent).not.toMatch(/hour|sla|deadline|target/i);

    rerender(<PriorityIndicator priority="high" />);
    expect(screen.getByTestId('priority-indicator').textContent).toBe('High');
  });

  it('renders separate SLAIndicator correctly across statuses', () => {
    const { rerender } = render(
      <SLAIndicator isOverdue={false} timeRemainingMinutes={180} targetHours={8} />
    );
    const panel = screen.getByTestId('sla-panel');
    expect(panel.textContent).toMatch(/Within Target/i);
    expect(panel.textContent).toMatch(/3h remaining/i);

    rerender(
      <SLAIndicator isOverdue={true} timeRemainingMinutes={-60} targetHours={2} />
    );
    expect(screen.getByTestId('sla-panel').textContent).toMatch(/Overdue/i);
  });

  it('renders ConfirmDialog and responds to actions', () => {
    let confirmed = false;
    let cancelled = false;

    render(
      <ConfirmDialog
        isOpen={true}
        title="Delete Confirmation"
        message="Are you sure you want to proceed?"
        onConfirm={() => { confirmed = true; }}
        onCancel={() => { cancelled = true; }}
      />
    );

    expect(screen.getByText('Delete Confirmation')).toBeDefined();
    expect(screen.getByText('Are you sure you want to proceed?')).toBeDefined();

    fireEvent.click(screen.getByText('Confirm'));
    expect(confirmed).toBe(true);

    fireEvent.click(screen.getByText('Cancel'));
    expect(cancelled).toBe(true);
  });
});

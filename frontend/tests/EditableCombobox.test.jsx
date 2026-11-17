import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import EditableCombobox from '../src/components/EditableCombobox';
import {
  PREDEFINED_BUILDINGS,
  PREDEFINED_CATEGORIES,
  CATEGORIES_WITH_SUBCATEGORIES
} from '../src/constants/taxonomy';

describe('EditableCombobox & Taxonomy Integration', () => {
  it('renders with initial value and shows dropdown suggestions on click', () => {
    let currentValue = 'Main Academic Block';
    const handleChange = (e) => { currentValue = e.target.value; };

    render(
      <EditableCombobox
        name="building"
        value={currentValue}
        onChange={handleChange}
        suggestions={PREDEFINED_BUILDINGS}
        placeholder="Type or select building"
      />
    );

    const input = screen.getByPlaceholderText('Type or select building');
    expect(input.value).toBe('Main Academic Block');

    // Click toggle to open suggestions
    const toggleBtn = screen.getByLabelText(/Toggle suggestions for building/i);
    fireEvent.click(toggleBtn);

    // Verify predefined buildings appear in dropdown list
    expect(screen.getByText('Computer Science and Engineering (CSE) Block')).toBeTruthy();
    expect(screen.getByText('Cafeteria Block')).toBeTruthy();
  });

  it('allows typing completely custom values not in the suggestion list', () => {
    let typedValue = '';
    const handleChange = (e) => { typedValue = e.target.value; };

    render(
      <EditableCombobox
        name="building"
        value={typedValue}
        onChange={handleChange}
        suggestions={PREDEFINED_BUILDINGS}
        placeholder="Type custom location"
      />
    );

    const input = screen.getByPlaceholderText('Type custom location');
    fireEvent.change(input, { target: { value: 'Advanced Nanotechnology Wing' } });

    expect(typedValue).toBe('Advanced Nanotechnology Wing');
  });

  it('verifies 15 categories and component-based subcategories in taxonomy', () => {
    expect(PREDEFINED_CATEGORIES.length).toBe(15);
    expect(PREDEFINED_CATEGORIES).toContain('Network & Internet');
    expect(PREDEFINED_CATEGORIES).toContain('General IT Services');

    const networkSubs = CATEGORIES_WITH_SUBCATEGORIES['Network & Internet'];
    expect(networkSubs).toContain('Wi-Fi');
    expect(networkSubs).toContain('Network Switch');
    expect(networkSubs).toContain('Firewall');
    // Ensure no problem descriptions
    expect(networkSubs).not.toContain('Not Working');
    expect(networkSubs).not.toContain('Slow Connection');
  });
});

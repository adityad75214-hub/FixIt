import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

/**
 * EditableCombobox Component
 * Allows user to:
 * 1. Type freely (custom value).
 * 2. Click or focus to see suggestions.
 * 3. Filter suggestions in real time as they type.
 * 4. Navigate suggestions with ArrowUp / ArrowDown and select with Enter.
 * 5. Dismiss with Escape or clicking outside.
 */
export default function EditableCombobox({
  id,
  name,
  value = '',
  onChange,
  onSelect,
  placeholder = '',
  suggestions = [],
  disabled = false,
  required = false,
  'data-testid': testId,
  className = '',
  style = {}
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  // Filter suggestions case-insensitively based on typed value
  // If user opened dropdown via button click or focused without modifying, show all suggestions if exactly matching or when user wants to browse
  const filteredSuggestions = React.useMemo(() => {
    if (!value || typeof value !== 'string') return suggestions;
    const lower = value.trim().toLowerCase();

    // Check if input value is an exact match for one of the options (e.g. user selected it previously)
    const exactMatch = suggestions.some(item => typeof item === 'string' && item.toLowerCase() === lower);
    if (exactMatch) {
      // When an exact match is already selected, still present all options so user can easily change it
      return suggestions;
    }

    const filtered = suggestions.filter(item =>
      typeof item === 'string' && item.toLowerCase().includes(lower)
    );
    return filtered;
  }, [suggestions, value]);

  // Click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    onChange(e);
    if (!isOpen) setIsOpen(true);
    setHighlightedIndex(-1);
  };

  const handleSelectOption = (option) => {
    if (onSelect) {
      onSelect(option);
    } else {
      // Simulate synthetic event for standard form handlers
      onChange({ target: { name, value: option } });
    }
    setIsOpen(false);
    setHighlightedIndex(-1);
    if (inputRef.current) inputRef.current.focus();
  };

  const handleKeyDown = (e) => {
    if (disabled) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setHighlightedIndex(prev =>
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setHighlightedIndex(prev =>
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
      }
    } else if (e.key === 'Enter') {
      if (isOpen && highlightedIndex >= 0 && highlightedIndex < filteredSuggestions.length) {
        e.preventDefault();
        handleSelectOption(filteredSuggestions[highlightedIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setHighlightedIndex(-1);
    }
  };

  return (
    <div
      ref={wrapperRef}
      style={{ position: 'relative', width: '100%', ...style }}
    >
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          ref={inputRef}
          type="text"
          id={id}
          name={name}
          value={value}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          data-testid={testId}
          autoComplete="off"
          className={`form-control ${className}`}
          style={{
            paddingRight: '2.5rem',
            width: '100%'
          }}
        />
        <button
          type="button"
          tabIndex={-1}
          disabled={disabled}
          onClick={() => {
            if (!disabled) {
              setIsOpen(prev => !prev);
              if (!isOpen && inputRef.current) inputRef.current.focus();
            }
          }}
          style={{
            position: 'absolute',
            right: '0.75rem',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 0
          }}
          aria-label={`Toggle suggestions for ${name}`}
        >
          <ChevronDown
            size={18}
            style={{
              transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease'
            }}
          />
        </button>
      </div>

      {/* Suggestion Dropdown List */}
      {isOpen && !disabled && (
        <ul
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0,
            right: 0,
            maxHeight: '220px',
            overflowY: 'auto',
            background: 'var(--card-bg, #ffffff)',
            border: '1px solid var(--border-color, var(--border-color))',
            borderRadius: 'var(--radius-sm, 6px)',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            listStyle: 'none',
            margin: 0,
            padding: '4px 0'
          }}
        >
          {filteredSuggestions.length > 0 ? (
            filteredSuggestions.map((item, idx) => {
              const isSelected = item.toLowerCase() === (value || '').toLowerCase();
              const isHighlighted = idx === highlightedIndex;

              return (
                <li
                  key={`${item}-${idx}`}
                  onMouseDown={(e) => {
                    // Prevent blur so handleSelectOption triggers cleanly
                    e.preventDefault();
                    handleSelectOption(item);
                  }}
                  onMouseEnter={() => setHighlightedIndex(idx)}
                  style={{
                    padding: '8px 14px',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    backgroundColor: isHighlighted
                      ? 'var(--bg-main, var(--surface-subtle))'
                      : isSelected
                      ? 'rgba(37, 99, 235, 0.08)'
                      : 'transparent',
                    color: isSelected ? 'var(--brand-blue, var(--brand-blue))' : 'var(--text-main, var(--text-main))',
                    fontWeight: isSelected ? '600' : 'normal'
                  }}
                >
                  <span>{item}</span>
                  {isSelected && <Check size={14} color="var(--brand-blue, var(--brand-blue))" />}
                </li>
              );
            })
          ) : (
            <li
              style={{
                padding: '8px 14px',
                fontSize: '0.8125rem',
                color: 'var(--text-muted, var(--text-muted))',
                fontStyle: 'italic'
              }}
            >
              Custom value &quot;{value}&quot; will be used
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

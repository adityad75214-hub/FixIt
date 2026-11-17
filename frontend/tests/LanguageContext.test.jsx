import React from 'react';
import { describe, expect, it, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { LanguageProvider, LANGUAGE_OPTIONS, useLanguage } from '../src/context/LanguageContext';

function LanguageHarness() {
  const { language, setLanguage, t } = useLanguage();
  return (
    <div>
      <span data-testid="language">{language}</span>
      <span data-testid="dashboard">{t('Dashboard')}</span>
      <span data-testid="notifications">{t('Notifications')}</span>
      {LANGUAGE_OPTIONS.map(({ value }) => <button key={value} type="button" onClick={() => setLanguage(value)}>{value}</button> )}
      <button type="button" onClick={() => setLanguage('kn')}>Kannada</button>
      <button type="button" onClick={() => setLanguage('unsupported')}>Unsupported</button>
    </div>
  );
}

describe('Language preferences', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.lang = 'en';
  });

  it('offers all eight supported languages with native labels', () => {
    expect(LANGUAGE_OPTIONS.map(({ value }) => value)).toEqual([
      'en', 'hi', 'kn', 'ta', 'te', 'ml', 'mr', 'bn'
    ]);
    expect(LANGUAGE_OPTIONS.find(({ value }) => value === 'kn').nativeLabel).toBe('ಕನ್ನಡ');
  });

  it('changes translations and persists the selected language', () => {
    render(
      <LanguageProvider>
        <LanguageHarness />
      </LanguageProvider>
    );

    expect(screen.getByTestId('dashboard').textContent).toBe('Dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Kannada' }));

    expect(screen.getByTestId('language').textContent).toBe('kn');
    expect(screen.getByTestId('dashboard').textContent).toBe('ಡ್ಯಾಶ್‌ಬೋರ್ಡ್');
    expect(localStorage.getItem('fixit_language')).toBe('kn');
    expect(document.documentElement.lang).toBe('kn');
  });

  it('translates shared support and notification labels in every regional language', () => {
    render(<LanguageProvider><LanguageHarness /></LanguageProvider>);
    const expected = {
      en: 'Notifications',
      hi: 'सूचनाएँ',
      kn: 'ಅಧಿಸೂಚನೆಗಳು',
      ta: 'அறிவிப்புகள்',
      te: 'నోటిఫికేషన్‌లు',
      ml: 'അറിയിപ്പുകൾ',
      mr: 'सूचना',
      bn: 'বিজ্ঞপ্তి'
    };
    for (const [code, label] of Object.entries(expected)) {
      fireEvent.click(screen.getByRole('button', { name: code }));
      expect(screen.getByTestId('language').textContent).toBe(code);
      expect(screen.getByTestId('notifications').textContent).toBe(label);
    }
  });

  it('restores the saved language on a fresh provider mount', () => {
    localStorage.setItem('fixit_language', 'ta');
    render(<LanguageProvider><LanguageHarness /></LanguageProvider>);
    expect(screen.getByTestId('language').textContent).toBe('ta');
    expect(screen.getByTestId('notifications').textContent).toBe('அறிவிப்புகள்');
  });

  it('falls back to English for unsupported language codes', () => {
    render(
      <LanguageProvider>
        <LanguageHarness />
      </LanguageProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Unsupported' }));
    expect(screen.getByTestId('language').textContent).toBe('en');
    expect(screen.getByTestId('dashboard').textContent).toBe('Dashboard');
  });
});

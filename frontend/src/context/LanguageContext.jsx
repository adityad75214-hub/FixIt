import React, { createContext, useContext, useEffect, useState } from 'react';

const translations = {
  en: {},
  hi: {
    'Main Menu': 'मुख्य मेनू', Dashboard: 'डैशबोर्ड', 'All Tickets': 'सभी अनुरोध', 'Ticket Queue': 'अनुरोध सूची', 'My Tickets': 'मेरे अनुरोध', 'Enterprise Helpdesk': 'संस्थान सहायता केंद्र', 'Report Issue': 'समस्या दर्ज करें',
    'All Tickets': 'सभी अनुरोध', 'Ticket Queue': 'अनुरोध सूची', 'My Tickets': 'मेरे अनुरोध',
    'Knowledge Base': 'ज्ञान केंद्र', 'Feature Roadmap': 'फ़ीचर रोडमैप', 'Suggest a Feature': 'फ़ीचर सुझाएँ',
    'Campus Incidents': 'कैंपस घटनाएँ', 'IT Staff Portal': 'सहायता कर्मचारी पोर्टल',
    'My Assignments': 'मेरे असाइनमेंट', Administration: 'प्रशासन', 'User Directory': 'उपयोगकर्ता सूची',
    'SLA Policies': 'SLA नीतियाँ', 'Analytics & Reports': 'विश्लेषण और रिपोर्ट',
    'Audit Logs': 'ऑडिट लॉग', 'Campus Setup': 'कैंपस सेटअप', 'Issue Categories': 'समस्या श्रेणियाँ',
    'Student': 'विद्यार्थी', Faculty: 'शिक्षक', 'IT Staff': 'सहायता कर्मचारी', 'Support Staff': 'सहायता कर्मचारी', 'CAMPUS SUPPORT PLATFORM': 'कैंपस सहायता मंच', 'Campus Support Platform': 'कैंपस सहायता मंच', Administrator: 'प्रशासक',
    'CAMPUS IT HELPDESK': 'कैंपस सहायता केंद्र', 'Campus Community': 'कैंपस समुदाय',
    'Profile settings': 'प्रोफ़ाइल सेटिंग', 'Log Out': 'लॉग आउट', 'Toggle navigation menu': 'नेविगेशन मेनू खोलें',
    'My Profile & Security Settings': 'मेरी प्रोफ़ाइल और सुरक्षा सेटिंग',
    'Manage personal contact details and authentication credentials': 'संपर्क विवरण और लॉगिन सुरक्षा प्रबंधित करें',
    'Preferences': 'प्राथमिकताएँ', 'Appearance': 'दिखावट', 'Light theme': 'लाइट थीम',
    'Dark theme': 'डार्क थीम', 'Preferred language': 'पसंदीदा भाषा', 'English': 'अंग्रेज़ी',
    'In-app notifications': 'ऐप सूचनाएँ', 'Email notification preference': 'ईमेल सूचनाएँ',
    'Save Preferences': 'प्राथमिकताएँ सहेजें', 'Save Profile': 'प्रोफ़ाइल सहेजें',
    'Change Password': 'पासवर्ड बदलें', 'Current Password': 'वर्तमान पासवर्ड',
    'New Password': 'नया पासवर्ड', 'Confirm New Password': 'नए पासवर्ड की पुष्टि करें',
    'Update Password': 'पासवर्ड अपडेट करें', 'Profile picture': 'प्रोफ़ाइल तस्वीर',
    'Upload JPG, PNG, WEBP or GIF. Maximum size: 5 MB.': 'JPG, PNG, WEBP या GIF अपलोड करें। अधिकतम आकार: 5 MB।',
    'Personal contact details': 'व्यक्तिगत संपर्क विवरण'
  }
};

const LanguageContext = createContext({ language: 'en', setLanguage: () => {}, t: (value) => value });

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try { return localStorage.getItem('fixit_language') === 'hi' ? 'hi' : 'en'; } catch { return 'en'; }
  });
  const setLanguage = (value) => setLanguageState(value === 'hi' ? 'hi' : 'en');
  useEffect(() => {
    try { localStorage.setItem('fixit_language', language); } catch { /* storage may be unavailable */ }
    document.documentElement.lang = language;
  }, [language]);
  const t = (value) => translations[language]?.[value] || value;
  return <LanguageContext.Provider value={{ language, setLanguage, t }}>{children}</LanguageContext.Provider>;
}

export const useLanguage = () => useContext(LanguageContext);

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
  },

  kn: {
    'Main Menu': 'ಮುಖ್ಯ ಮೆನು', Dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', 'Report Issue': 'ಸಮಸ್ಯೆ ವರದಿ ಮಾಡಿ',
    'All Tickets': 'ಎಲ್ಲಾ ವಿನಂತಿಗಳು', 'Ticket Queue': 'ವಿನಂತಿಗಳ ಸರತಿ', 'My Tickets': 'ನನ್ನ ವಿನಂತಿಗಳು',
    'Knowledge Base': 'ಜ್ಞಾನ ಸಂಪನ್ಮೂಲ', 'Feature Roadmap': 'ವೈಶಿಷ್ಟ್ಯಗಳ ಯೋಜನೆ', 'Suggest a Feature': 'ವೈಶಿಷ್ಟ್ಯ ಸೂಚಿಸಿ',
    'Campus Incidents': 'ಕ್ಯಾಂಪಸ್ ಘಟನೆಗಳು', 'IT Staff Portal': 'ಸಹಾಯ ಸಿಬ್ಬಂದಿ ಪೋರ್ಟಲ್', 'My Assignments': 'ನನ್ನ ಕಾರ್ಯಗಳು',
    Administration: 'ಆಡಳಿತ', 'User Directory': 'ಬಳಕೆದಾರರ ಪಟ್ಟಿ', 'SLA Policies': 'SLA ನೀತಿಗಳು',
    'Analytics & Reports': 'ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ವರದಿಗಳು', 'Audit Logs': 'ಆಡಿಟ್ ದಾಖಲೆಗಳು', 'Campus Setup': 'ಕ್ಯಾಂಪಸ್ ಸೆಟಪ್',
    'Issue Categories': 'ಸಮಸ್ಯೆಯ ವರ್ಗಗಳು', Student: 'ವಿದ್ಯಾರ್ಥಿ', Faculty: 'ಬೋಧಕವರ್ಗ', 'IT Staff': 'ಸಹಾಯ ಸಿಬ್ಬಂದಿ',
    'Support Staff': 'ಸಹಾಯ ಸಿಬ್ಬಂದಿ', Administrator: 'ನಿರ್ವಾಹಕರು', 'CAMPUS SUPPORT PLATFORM': 'ಕ್ಯಾಂಪಸ್ ಸಹಾಯ ವೇದಿಕೆ',
    'Campus Support Platform': 'ಕ್ಯಾಂಪಸ್ ಸಹಾಯ ವೇದಿಕೆ', 'Campus Community': 'ಕ್ಯಾಂಪಸ್ ಸಮುದಾಯ',
    'Profile settings': 'ಪ್ರೊಫೈಲ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳು', 'Log Out': 'ಲಾಗ್ ಔಟ್', 'Toggle navigation menu': 'ನ್ಯಾವಿಗೇಶನ್ ಮೆನು ತೆರೆಯಿರಿ',
    'My Profile & Security Settings': 'ನನ್ನ ಪ್ರೊಫೈಲ್ ಮತ್ತು ಭದ್ರತಾ ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    'Manage personal contact details and authentication credentials': 'ಸಂಪರ್ಕ ವಿವರಗಳು ಮತ್ತು ಲಾಗಿನ್ ಭದ್ರತೆಯನ್ನು ನಿರ್ವಹಿಸಿ',
    Preferences: 'ಆದ್ಯತೆಗಳು', Appearance: 'ಗೋಚರತೆ', 'Light theme': 'ಲೈಟ್ ಥೀಮ್', 'Dark theme': 'ಡಾರ್ಕ್ ಥೀಮ್',
    'Preferred language': 'ಆದ್ಯತೆಯ ಭಾಷೆ', English: 'ಇಂಗ್ಲಿಷ್', 'In-app notifications': 'ಆ್ಯಪ್ ಅಧಿಸೂಚನೆಗಳು',
    'Email notification preference': 'ಇಮೇಲ್ ಅಧಿಸೂಚನೆಗಳು', 'Save Preferences': 'ಆದ್ಯತೆಗಳನ್ನು ಉಳಿಸಿ',
    'Save Profile': 'ಪ್ರೊಫೈಲ್ ಉಳಿಸಿ', 'Change Password': 'ಪಾಸ್‌ವರ್ಡ್ ಬದಲಿಸಿ', 'Current Password': 'ಪ್ರಸ್ತುತ ಪಾಸ್‌ವರ್ಡ್',
    'New Password': 'ಹೊಸ ಪಾಸ್‌ವರ್ಡ್', 'Confirm New Password': 'ಹೊಸ ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ',
    'Update Password': 'ಪಾಸ್‌ವರ್ಡ್ ನವೀಕರಿಸಿ', 'Profile picture': 'ಪ್ರೊಫೈಲ್ ಚಿತ್ರ',
    'Personal contact details': 'ವೈಯಕ್ತಿಕ ಸಂಪರ್ಕ ವಿವರಗಳು'
  },
  ta: {
    'Main Menu': 'முதன்மை பட்டி', Dashboard: 'முகப்புப் பலகை', 'Report Issue': 'சிக்கலைப் புகாரளிக்கவும்',
    'All Tickets': 'அனைத்து கோரிக்கைகள்', 'Ticket Queue': 'கோரிக்கை வரிசை', 'My Tickets': 'எனது கோரிக்கைகள்',
    'Knowledge Base': 'அறிவுத் தளம்', 'Feature Roadmap': 'அம்சத் திட்டம்', 'Suggest a Feature': 'அம்சத்தைப் பரிந்துரைக்கவும்',
    'Campus Incidents': 'வளாக நிகழ்வுகள்', 'IT Staff Portal': 'ஆதரவு பணியாளர் தளம்', 'My Assignments': 'எனது பணிகள்',
    Administration: 'நிர்வாகம்', 'User Directory': 'பயனர் பட்டியல்', 'SLA Policies': 'SLA கொள்கைகள்',
    'Analytics & Reports': 'பகுப்பாய்வு மற்றும் அறிக்கைகள்', 'Audit Logs': 'தணிக்கை பதிவுகள்', 'Campus Setup': 'வளாக அமைப்பு',
    'Issue Categories': 'சிக்கல் வகைகள்', Student: 'மாணவர்', Faculty: 'ஆசிரியர் குழு', 'IT Staff': 'ஆதரவு பணியாளர்கள்',
    'Support Staff': 'ஆதரவு பணியாளர்கள்', Administrator: 'நிர்வாகி', 'CAMPUS SUPPORT PLATFORM': 'வளாக ஆதரவு தளம்',
    'Campus Support Platform': 'வளாக ஆதரவு தளம்', 'Campus Community': 'வளாக சமூகம்',
    'Profile settings': 'சுயவிவர அமைப்புகள்', 'Log Out': 'வெளியேறு', 'Toggle navigation menu': 'வழிசெலுத்தல் பட்டியைத் திறக்கவும்',
    'My Profile & Security Settings': 'எனது சுயவிவரம் மற்றும் பாதுகாப்பு அமைப்புகள்',
    'Manage personal contact details and authentication credentials': 'தொடர்பு விவரங்கள் மற்றும் உள்நுழைவு பாதுகாப்பை நிர்வகிக்கவும்',
    Preferences: 'விருப்பத்தேர்வுகள்', Appearance: 'தோற்றம்', 'Light theme': 'ஒளி தோற்றம்', 'Dark theme': 'இருள் தோற்றம்',
    'Preferred language': 'விருப்ப மொழி', English: 'ஆங்கிலம்', 'In-app notifications': 'செயலி அறிவிப்புகள்',
    'Email notification preference': 'மின்னஞ்சல் அறிவிப்புகள்', 'Save Preferences': 'விருப்பங்களைச் சேமிக்கவும்',
    'Save Profile': 'சுயவிவரத்தைச் சேமிக்கவும்', 'Change Password': 'கடவுச்சொல்லை மாற்றவும்', 'Current Password': 'தற்போதைய கடவுச்சொல்',
    'New Password': 'புதிய கடவுச்சொல்', 'Confirm New Password': 'புதிய கடவுச்சொல்லை உறுதிப்படுத்தவும்',
    'Update Password': 'கடவுச்சொல்லைப் புதுப்பிக்கவும்', 'Profile picture': 'சுயவிவரப் படம்',
    'Personal contact details': 'தனிப்பட்ட தொடர்பு விவரங்கள்'
  },
  te: {
    'Main Menu': 'ప్రధాన మెను', Dashboard: 'డ్యాష్‌బోర్డ్', 'Report Issue': 'సమస్యను నివేదించండి',
    'All Tickets': 'అన్ని అభ్యర్థనలు', 'Ticket Queue': 'అభ్యర్థనల క్యూలు', 'My Tickets': 'నా అభ్యర్థనలు',
    'Knowledge Base': 'జ్ఞాన కేంద్రం', 'Feature Roadmap': 'ఫీచర్ ప్రణాళిక', 'Suggest a Feature': 'ఫీచర్ సూచించండి',
    'Campus Incidents': 'క్యాంపస్ సంఘటనలు', 'IT Staff Portal': 'సహాయ సిబ్బంది పోర్టల్', 'My Assignments': 'నా పనులు',
    Administration: 'పరిపాలన', 'User Directory': 'వినియోగదారుల జాబితా', 'SLA Policies': 'SLA విధానాలు',
    'Analytics & Reports': 'విశ్లేషణలు మరియు నివేదికలు', 'Audit Logs': 'ఆడిట్ లాగ్‌లు', 'Campus Setup': 'క్యాంపస్ సెటప్',
    'Issue Categories': 'సమస్య వర్గాలు', Student: 'విద్యార్థి', Faculty: 'అధ్యాపకులు', 'IT Staff': 'సహాయ సిబ్బంది',
    'Support Staff': 'సహాయ సిబ్బంది', Administrator: 'నిర్వాహకుడు', 'CAMPUS SUPPORT PLATFORM': 'క్యాంపస్ సహాయ వేదిక',
    'Campus Support Platform': 'క్యాంపస్ సహాయ వేదిక', 'Campus Community': 'క్యాంపస్ సమాజం',
    'Profile settings': 'ప్రొఫైల్ సెట్టింగ్‌లు', 'Log Out': 'లాగ్ అవుట్', 'Toggle navigation menu': 'నావిగేషన్ మెనూను తెరవండి',
    'My Profile & Security Settings': 'నా ప్రొఫైల్ మరియు భద్రతా సెట్టింగ్‌లు',
    'Manage personal contact details and authentication credentials': 'సంప్రదింపు వివరాలు మరియు లాగిన్ భద్రతను నిర్వహించండి',
    Preferences: 'ప్రాధాన్యతలు', Appearance: 'రూపం', 'Light theme': 'లైట్ థీమ్', 'Dark theme': 'డార్క్ థీమ్',
    'Preferred language': 'ఇష్టమైన భాష', English: 'ఆంగ్లం', 'In-app notifications': 'యాప్ నోటిఫికేషన్‌లు',
    'Email notification preference': 'ఇమెయిల్ నోటిఫికేషన్‌లు', 'Save Preferences': 'ప్రాధాన్యతలను సేవ్ చేయండి',
    'Save Profile': 'ప్రొఫైల్‌ను సేవ్ చేయండి', 'Change Password': 'పాస్‌వర్డ్ మార్చండి', 'Current Password': 'ప్రస్తుత పాస్‌వర్డ్',
    'New Password': 'కొత్త పాస్‌వర్డ్', 'Confirm New Password': 'కొత్త పాస్‌వర్డ్‌ను నిర్ధారించండి',
    'Update Password': 'పాస్‌వర్డ్‌ను నవీకరించండి', 'Profile picture': 'ప్రొఫైల్ చిత్రం',
    'Personal contact details': 'వ్యక్తిగత సంప్రదింపు వివరాలు'
  },
  ml: {
    'Main Menu': 'പ്രധാന മെനു', Dashboard: 'ഡാഷ്ബോർഡ്', 'Report Issue': 'പ്രശ്നം റിപ്പോർട്ട് ചെയ്യുക',
    'All Tickets': 'എല്ലാ അഭ്യർത്ഥനകളും', 'Ticket Queue': 'അഭ്യർത്ഥന ക്യൂ', 'My Tickets': 'എന്റെ അഭ്യർത്ഥനകൾ',
    'Knowledge Base': 'അറിവ് ശേഖരം', 'Feature Roadmap': 'സവിശേഷതാ പദ്ധതി', 'Suggest a Feature': 'സവിശേഷത നിർദ്ദേശിക്കുക',
    'Campus Incidents': 'ക്യാമ്പസ് സംഭവങ്ങൾ', 'IT Staff Portal': 'സഹായ ജീവനക്കാരുടെ പോർട്ടൽ', 'My Assignments': 'എന്റെ ചുമതലകൾ',
    Administration: 'ഭരണനിർവഹണം', 'User Directory': 'ഉപയോക്തൃ പട്ടിക', 'SLA Policies': 'SLA നയങ്ങൾ',
    'Analytics & Reports': 'വിശകലനങ്ങളും റിപ്പോർട്ടുകളും', 'Audit Logs': 'ഓഡിറ്റ് രേഖകൾ', 'Campus Setup': 'ക്യാമ്പസ് ക്രമീകരണം',
    'Issue Categories': 'പ്രശ്ന വിഭാഗങ്ങൾ', Student: 'വിദ്യാർത്ഥി', Faculty: 'അധ്യാപകർ', 'IT Staff': 'സഹായ ജീവനക്കാർ',
    'Support Staff': 'സഹായ ജീവനക്കാർ', Administrator: 'അഡ്മിനിസ്ട്രേറ്റർ', 'CAMPUS SUPPORT PLATFORM': 'ക്യാമ്പസ് സഹായ പ്ലാറ്റ്ഫോം',
    'Campus Support Platform': 'ക്യാമ്പസ് സഹായ പ്ലാറ്റ്ഫോം', 'Campus Community': 'ക്യാമ്പസ് സമൂഹം',
    'Profile settings': 'പ്രൊഫൈൽ ക്രമീകരണങ്ങൾ', 'Log Out': 'ലോഗ് ഔട്ട്', 'Toggle navigation menu': 'നാവിഗേഷൻ മെനു തുറക്കുക',
    'My Profile & Security Settings': 'എന്റെ പ്രൊഫൈലും സുരക്ഷാ ക്രമീകരണങ്ങളും',
    'Manage personal contact details and authentication credentials': 'ബന്ധപ്പെടാനുള്ള വിവരങ്ങളും ലോഗിൻ സുരക്ഷയും നിയന്ത്രിക്കുക',
    Preferences: 'മുൻഗണനകൾ', Appearance: 'രൂപഭാവം', 'Light theme': 'ലൈറ്റ് തീം', 'Dark theme': 'ഡാർക്ക് തീം',
    'Preferred language': 'ഇഷ്ടപ്പെട്ട ഭാഷ', English: 'ഇംഗ്ലീഷ്', 'In-app notifications': 'ആപ്പ് അറിയിപ്പുകൾ',
    'Email notification preference': 'ഇമെയിൽ അറിയിപ്പുകൾ', 'Save Preferences': 'മുൻഗണനകൾ സംരക്ഷിക്കുക',
    'Save Profile': 'പ്രൊഫൈൽ സംരക്ഷിക്കുക', 'Change Password': 'പാസ്‌വേഡ് മാറ്റുക', 'Current Password': 'നിലവിലെ പാസ്‌വേഡ്',
    'New Password': 'പുതിയ പാസ്‌വേഡ്', 'Confirm New Password': 'പുതിയ പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക',
    'Update Password': 'പാസ്‌വേഡ് പുതുക്കുക', 'Profile picture': 'പ്രൊഫൈൽ ചിത്രം',
    'Personal contact details': 'വ്യക്തിഗത ബന്ധപ്പെടൽ വിവരങ്ങൾ'
  },
  mr: {
    'Main Menu': 'मुख्य मेनू', Dashboard: 'डॅशबोर्ड', 'Report Issue': 'समस्या नोंदवा',
    'All Tickets': 'सर्व विनंत्या', 'Ticket Queue': 'विनंत्यांची यादी', 'My Tickets': 'माझ्या विनंत्या',
    'Knowledge Base': 'ज्ञानकोश', 'Feature Roadmap': 'वैशिष्ट्य आराखडा', 'Suggest a Feature': 'वैशिष्ट्य सुचवा',
    'Campus Incidents': 'कॅम्पस घटना', 'IT Staff Portal': 'सहाय्य कर्मचारी पोर्टल', 'My Assignments': 'माझी कामे',
    Administration: 'प्रशासन', 'User Directory': 'वापरकर्ता सूची', 'SLA Policies': 'SLA धोरणे',
    'Analytics & Reports': 'विश्लेषण आणि अहवाल', 'Audit Logs': 'ऑडिट नोंदी', 'Campus Setup': 'कॅम्पस सेटअप',
    'Issue Categories': 'समस्यांचे प्रकार', Student: 'विद्यार्थी', Faculty: 'प्राध्यापक', 'IT Staff': 'सहाय्य कर्मचारी',
    'Support Staff': 'सहाय्य कर्मचारी', Administrator: 'प्रशासक', 'CAMPUS SUPPORT PLATFORM': 'कॅम्पस सहाय्य मंच',
    'Campus Support Platform': 'कॅम्पस सहाय्य मंच', 'Campus Community': 'कॅम्पस समुदाय',
    'Profile settings': 'प्रोफाइल सेटिंग्ज', 'Log Out': 'बाहेर पडा', 'Toggle navigation menu': 'नेव्हिगेशन मेनू उघडा',
    'My Profile & Security Settings': 'माझे प्रोफाइल आणि सुरक्षा सेटिंग्ज',
    'Manage personal contact details and authentication credentials': 'संपर्क तपशील आणि लॉगिन सुरक्षा व्यवस्थापित करा',
    Preferences: 'प्राधान्ये', Appearance: 'दिसणे', 'Light theme': 'लाइट थीम', 'Dark theme': 'डार्क थीम',
    'Preferred language': 'पसंतीची भाषा', English: 'इंग्रजी', 'In-app notifications': 'अॅप सूचना',
    'Email notification preference': 'ईमेल सूचना', 'Save Preferences': 'प्राधान्ये जतन करा',
    'Save Profile': 'प्रोफाइल जतन करा', 'Change Password': 'पासवर्ड बदला', 'Current Password': 'सध्याचा पासवर्ड',
    'New Password': 'नवीन पासवर्ड', 'Confirm New Password': 'नवीन पासवर्डची पुष्टी करा',
    'Update Password': 'पासवर्ड अद्ययावत करा', 'Profile picture': 'प्रोफाइल चित्र',
    'Personal contact details': 'वैयक्तिक संपर्क तपशील'
  },
  bn: {
    'Main Menu': 'প্রধান মেনু', Dashboard: 'ড্যাশবোর্ড', 'Report Issue': 'সমস্যা জানান',
    'All Tickets': 'সব অনুরোধ', 'Ticket Queue': 'অনুরোধের তালিকা', 'My Tickets': 'আমার অনুরোধ',
    'Knowledge Base': 'জ্ঞানভাণ্ডার', 'Feature Roadmap': 'ফিচার পরিকল্পনা', 'Suggest a Feature': 'ফিচার প্রস্তাব করুন',
    'Campus Incidents': 'ক্যাম্পাসের ঘটনা', 'IT Staff Portal': 'সহায়তা কর্মী পোর্টাল', 'My Assignments': 'আমার দায়িত্ব',
    Administration: 'প্রশাসন', 'User Directory': 'ব্যবহারকারীর তালিকা', 'SLA Policies': 'SLA নীতি',
    'Analytics & Reports': 'বিশ্লেষণ ও প্রতিবেদন', 'Audit Logs': 'অডিট লগ', 'Campus Setup': 'ক্যাম্পাস সেটআপ',
    'Issue Categories': 'সমস্যার বিভাগ', Student: 'শিক্ষার্থী', Faculty: 'শিক্ষকমণ্ডলী', 'IT Staff': 'সহায়তা কর্মী',
    'Support Staff': 'সহায়তা কর্মী', Administrator: 'প্রশাসক', 'CAMPUS SUPPORT PLATFORM': 'ক্যাম্পাস সহায়তা প্ল্যাটফর্ম',
    'Campus Support Platform': 'ক্যাম্পাস সহায়তা প্ল্যাটফর্ম', 'Campus Community': 'ক্যাম্পাস সম্প্রদায়',
    'Profile settings': 'প্রোফাইল সেটিংস', 'Log Out': 'লগ আউট', 'Toggle navigation menu': 'নেভিগেশন মেনু খুলুন',
    'My Profile & Security Settings': 'আমার প্রোফাইল ও নিরাপত্তা সেটিংস',
    'Manage personal contact details and authentication credentials': 'যোগাযোগের তথ্য ও লগইন নিরাপত্তা পরিচালনা করুন',
    Preferences: 'পছন্দসমূহ', Appearance: 'চেহারা', 'Light theme': 'লাইট থিম', 'Dark theme': 'ডার্ক থিম',
    'Preferred language': 'পছন্দের ভাষা', English: 'ইংরেজি', 'In-app notifications': 'অ্যাপ বিজ্ঞপ্তি',
    'Email notification preference': 'ইমেল বিজ্ঞপ্তি', 'Save Preferences': 'পছন্দ সংরক্ষণ করুন',
    'Save Profile': 'প্রোফাইল সংরক্ষণ করুন', 'Change Password': 'পাসওয়ার্ড পরিবর্তন করুন', 'Current Password': 'বর্তমান পাসওয়ার্ড',
    'New Password': 'নতুন পাসওয়ার্ড', 'Confirm New Password': 'নতুন পাসওয়ার্ড নিশ্চিত করুন',
    'Update Password': 'পাসওয়ার্ড আপডেট করুন', 'Profile picture': 'প্রোফাইল ছবি',
    'Personal contact details': 'ব্যক্তিগত যোগাযোগের তথ্য'
  }

};

const supplementalTranslations = {
  "hi": {
    "Support Staff Portal": "सहायता कर्मचारी पोर्टल",
    "Loading campus support": "कैंपस सहायता लोड हो रही है…",
    "Notifications": "सूचनाएँ",
    "Mark all read": "सभी को पढ़ा हुआ चिह्नित करें",
    "No notifications right now": "अभी कोई सूचना नहीं है",
    "View request": "अनुरोध देखें"
  },
  "kn": {
    "Support Staff Portal": "ಸಹಾಯ ಸಿಬ್ಬಂದಿ ಪೋರ್ಟಲ್",
    "Loading campus support": "ಕ್ಯಾಂಪಸ್ ಸಹಾಯ ಲೋಡ್ ಆಗುತ್ತಿದೆ…",
    "Notifications": "ಅಧಿಸೂಚನೆಗಳು",
    "Mark all read": "ಎಲ್ಲವನ್ನೂ ಓದಿದಂತೆ ಗುರುತಿಸಿ",
    "No notifications right now": "ಈಗ ಯಾವುದೇ ಅಧಿಸೂಚನೆಗಳಿಲ್ಲ",
    "View request": "ವಿನಂತಿಯನ್ನು ವೀಕ್ಷಿಸಿ"
  },
  "ta": {
    "Support Staff Portal": "ஆதரவு பணியாளர் தளம்",
    "Loading campus support": "வளாக ஆதரவு ஏற்றப்படுகிறது…",
    "Notifications": "அறிவிப்புகள்",
    "Mark all read": "அனைத்தையும் படித்ததாகக் குறிக்கவும்",
    "No notifications right now": "இப்போது அறிவிப்புகள் இல்லை",
    "View request": "கோரிக்கையைப் பார்க்கவும்"
  },
  "te": {
    "Support Staff Portal": "సహాయ సిబ్బంది పోర్టల్",
    "Loading campus support": "క్యాంపస్ సహాయం లోడ్ అవుతోంది…",
    "Notifications": "నోటిఫికేషన్‌లు",
    "Mark all read": "అన్నింటినీ చదివినట్లు గుర్తించండి",
    "No notifications right now": "ప్రస్తుతం నోటిఫికేషన్‌లు లేవు",
    "View request": "అభ్యర్థనను చూడండి"
  },
  "ml": {
    "Support Staff Portal": "സഹായ ജീവനക്കാരുടെ പോർട്ടൽ",
    "Loading campus support": "ക്യാമ്പസ് സഹായം ലോഡ് ചെയ്യുന്നു…",
    "Notifications": "അറിയിപ്പുകൾ",
    "Mark all read": "എല്ലാം വായിച്ചതായി അടയാളപ്പെടുത്തുക",
    "No notifications right now": "ഇപ്പോൾ അറിയിപ്പുകളൊന്നുമില്ല",
    "View request": "അഭ്യർത്ഥന കാണുക"
  },
  "mr": {
    "Support Staff Portal": "सहाय्य कर्मचारी पोर्टल",
    "Loading campus support": "कॅम्पस सहाय्य लोड होत आहे…",
    "Notifications": "सूचना",
    "Mark all read": "सर्व वाचलेले म्हणून चिन्हांकित करा",
    "No notifications right now": "सध्या कोणत्याही सूचना नाहीत",
    "View request": "विनंती पहा"
  },
  "bn": {
    "Support Staff Portal": "সহায়তা কর্মী পোর্টাল",
    "Loading campus support": "ক্যাম্পাস সহায়তা লোড হচ্ছে…",
    "Notifications": "বিজ্ঞপ্তি",
    "Mark all read": "সব পড়া হিসেবে চিহ্নিত করুন",
    "No notifications right now": "এখন কোনো বিজ্ঞপ্তি নেই",
    "View request": "অনুরোধ দেখুন"
  }
};

export const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English', nativeLabel: 'English' },
  { value: 'hi', label: 'Hindi', nativeLabel: 'हिन्दी' },
  { value: 'kn', label: 'Kannada', nativeLabel: 'ಕನ್ನಡ' },
  { value: 'ta', label: 'Tamil', nativeLabel: 'தமிழ்' },
  { value: 'te', label: 'Telugu', nativeLabel: 'తెలుగు' },
  { value: 'ml', label: 'Malayalam', nativeLabel: 'മലയാളം' },
  { value: 'mr', label: 'Marathi', nativeLabel: 'मराठी' },
  { value: 'bn', label: 'Bengali', nativeLabel: 'বাংলা' }
];
const supportedLanguages = new Set(LANGUAGE_OPTIONS.map(({ value }) => value));
const normalizeLanguage = (value) => supportedLanguages.has(value) ? value : 'en';

const LanguageContext = createContext({ language: 'en', setLanguage: () => {}, t: (value) => value });

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try { return normalizeLanguage(localStorage.getItem('fixit_language')); } catch { return 'en'; }
  });
  const setLanguage = (value) => setLanguageState(normalizeLanguage(value));
  useEffect(() => {
    try { localStorage.setItem('fixit_language', language); } catch { /* storage may be unavailable */ }
    document.documentElement.lang = language;
  }, [language]);
  const t = (value) => supplementalTranslations[language]?.[value] || translations[language]?.[value] || value;
  return <LanguageContext.Provider value={{ language, setLanguage, t }}>{children}</LanguageContext.Provider>;
}

export const useLanguage = () => useContext(LanguageContext);

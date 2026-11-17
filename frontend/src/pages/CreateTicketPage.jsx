import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { PlusCircle, AlertTriangle, ArrowRight, ExternalLink } from 'lucide-react';
import { ticketService, categoryService, campusService, knowledgeBaseService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import SLAIndicator from '../components/SLAIndicator';

const DEMO_MODE_ENABLED = import.meta.env.DEV && import.meta.env.VITE_DEMO_MODE_ENABLED !== 'false';

// 15 Predefined Campus Buildings
const PREDEFINED_BUILDINGS = [
  "Main Academic Block",
  "Computer Science and Engineering (CSE) Block",
  "Electronics and Communication (ECE) Block",
  "Mechanical Engineering Block",
  "Electrical Engineering Block",
  "Central Library",
  "Computer Laboratory Block",
  "Administration Block",
  "Auditorium",
  "Workshop Block",
  "Science and Research Block",
  "Hostel Block",
  "Sports Complex",
  "Placement and Training Block",
  "Cafeteria Block"
];

// Predefined Floors
const PREDEFINED_FLOORS = [
  "Basement",
  "Ground Floor",
  "1st Floor",
  "2nd Floor",
  "3rd Floor",
  "4th Floor",
  "5th Floor",
  "6th Floor",
  "7th Floor",
  "8th Floor",
  "9th Floor",
  "10th Floor",
  "Rooftop",
  "Other"
];

// Predefined Rooms
const PREDEFINED_ROOMS = [
  "Classroom 101",
  "Classroom 102",
  "Classroom 201",
  "Classroom 202",
  "Smart Classroom 101",
  "Computer Lab 101",
  "Computer Lab 102",
  "Network Lab 201",
  "Hardware Lab 202",
  "Electronics Lab 101",
  "Physics Lab 101",
  "Chemistry Lab 101",
  "Seminar Hall",
  "Conference Hall",
  "Faculty Room",
  "Staff Room",
  "Server Room",
  "Auditorium",
  "Workshop"
];

// 15 Predefined Categories with Equipment/Technical Subcategories
const CATEGORIES_DATA = {
  "Network & Internet": [
    "Wi-Fi",
    "Router",
    "Network Switch",
    "LAN / Ethernet",
    "Network Cable",
    "Access Point",
    "Firewall",
    "VPN",
    "DNS",
    "DHCP",
    "Network Rack",
    "Network Infrastructure"
  ],
  "Computer & Hardware": [
    "Desktop Computer",
    "Laptop",
    "Monitor",
    "Keyboard",
    "Mouse",
    "CPU",
    "Motherboard",
    "RAM",
    "Hard Disk / SSD",
    "Graphics Card",
    "Webcam",
    "Microphone",
    "Speakers",
    "UPS",
    "Computer Accessories"
  ],
  "Software & Applications": [
    "Operating System",
    "Microsoft Office",
    "Web Browser",
    "Antivirus Software",
    "Programming Software",
    "IDE / Code Editor",
    "Database Software",
    "Engineering Software",
    "Design Software",
    "Utility Software",
    "Licensed Applications",
    "Educational Software"
  ],
  "Classroom & Audio-Visual Equipment": [
    "Projector",
    "Interactive Smart Board",
    "Digital Display",
    "HDMI / VGA Connection",
    "Digital Podium",
    "Classroom Speakers",
    "Microphone",
    "Amplifier",
    "Audio System",
    "Video Conferencing System",
    "Projection Screen",
    "Remote Control",
    "Classroom Recording System"
  ],
  "Printer & Scanner": [
    "Laser Printer",
    "Inkjet Printer",
    "Network Printer",
    "Multifunction Printer",
    "Photocopier",
    "Document Scanner",
    "Barcode Printer",
    "Printer Accessories",
    "Printing Supplies"
  ],
  "Email & User Accounts": [
    "Student Account",
    "Faculty Account",
    "Staff Account",
    "College Email",
    "Google Workspace",
    "Microsoft 365",
    "Login Credentials",
    "User Permissions",
    "Multi-Factor Authentication",
    "Account Management"
  ],
  "Server & Database": [
    "Physical Server",
    "Virtual Server",
    "Database Server",
    "Web Server",
    "Application Server",
    "File Server",
    "Storage Server",
    "Database Management System",
    "Server Backup",
    "Cloud Infrastructure",
    "Virtual Machine",
    "Server Room Infrastructure"
  ],
  "Website & College Portal": [
    "College Website",
    "Student Portal",
    "Faculty Portal",
    "Administration Portal",
    "Learning Management System (LMS)",
    "Attendance Management System",
    "Examination Portal",
    "Result Management System",
    "Fee Management Portal",
    "Admission Portal",
    "Placement Portal",
    "Online Registration System"
  ],
  "Cybersecurity & Data Protection": [
    "Antivirus",
    "Firewall Security",
    "Endpoint Security",
    "Network Security",
    "Email Security",
    "Data Backup",
    "Data Recovery",
    "Access Permissions",
    "Encryption",
    "Identity Management",
    "Security Monitoring"
  ],
  "Electrical & Power Systems": [
    "UPS",
    "Generator",
    "Transformer",
    "Electrical Panel",
    "Power Distribution Board",
    "Electrical Wiring",
    "Power Socket",
    "Circuit Breaker",
    "Battery System",
    "Inverter",
    "Lighting System",
    "Power Backup System"
  ],
  "Laboratory & Technical Equipment": [
    "Arduino Kit",
    "Microcontroller",
    "Raspberry Pi",
    "Robotics Kit",
    "Electronic Trainer Kit",
    "Oscilloscope",
    "Function Generator",
    "Digital Multimeter",
    "3D Printer",
    "CNC Machine",
    "Mechanical Equipment",
    "Civil Engineering Equipment",
    "Physics Laboratory Equipment",
    "Chemistry Laboratory Equipment",
    "Networking Laboratory Equipment",
    "IoT Equipment"
  ],
  "Communication & Telephony": [
    "Landline Telephone",
    "Intercom",
    "VoIP Phone",
    "Public Address System",
    "Communication Cable",
    "Video Conferencing Equipment",
    "Wireless Communication Equipment",
    "Conference Room Communication System"
  ],
  "Building Facilities & Maintenance": [
    "Air Conditioning",
    "Ceiling Fan",
    "Lighting",
    "Plumbing",
    "Water Supply",
    "Drinking Water System",
    "Washroom Facilities",
    "Classroom Furniture",
    "Office Furniture",
    "Doors and Locks",
    "Windows",
    "Elevators / Lifts",
    "Housekeeping",
    "Waste Management",
    "Building Infrastructure"
  ],
  "Security & Access Control": [
    "CCTV Camera",
    "Biometric Scanner",
    "RFID Reader",
    "Access Card",
    "Smart Door Lock",
    "Security Alarm",
    "Gate Barrier",
    "Attendance Scanner",
    "Access Control Panel",
    "Security Monitoring System"
  ],
  "General IT Services": [
    "New Equipment Installation",
    "Hardware Procurement",
    "Software Procurement",
    "Equipment Configuration",
    "Equipment Relocation",
    "IT Consultation",
    "Technical Support",
    "Equipment Maintenance",
    "IT Infrastructure Setup",
    "IT Asset Management"
  ],
  "Academic Support": [
    "Subject Guidance",
    "Course / Syllabus Query",
    "Assignment Support",
    "Project Guidance",
    "Research Guidance",
    "Laboratory Learning Support",
    "Study Resources",
    "Exam Preparation"
  ],
  "Career & Placement Guidance": [
    "Resume Review",
    "Interview Preparation",
    "Internship Guidance",
    "Placement Support",
    "Higher Studies Guidance",
    "Career Counselling"
  ],
  "Administrative & Documentation": [
    "Bonafide Certificate",
    "Transcript / Marksheet",
    "Scholarship Query",
    "Fee / Payment Query",
    "Admission / Enrollment",
    "ID Card",
    "Official Records",
    "General Office Enquiry"
  ],
  "Campus Facilities & Maintenance": [
    "Hostel / Accommodation",
    "Transport",
    "Drinking Water",
    "Washroom / Sanitation",
    "Electricity / Lighting",
    "Furniture",
    "Cleaning / Waste Management",
    "Accessibility",
    "Safety / Security"
  ],
  "Student & Community Support": [
    "Student Guidance",
    "Peer Support",
    "Accessibility Assistance",
    "Community Concern",
    "Volunteer Assistance",
    "Other Support Request"
  ]
};

const PREDEFINED_CATEGORIES = Object.keys(CATEGORIES_DATA);

export default function CreateTicketPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [categories, setCategories] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [hierarchy, setHierarchy] = useState([]);
  const [customLocations, setCustomLocations] = useState([]);
  const [suggestedArticles, setSuggestedArticles] = useState([]);
  const [duplicates, setDuplicates] = useState([]);
  const [hasRestrictedDuplicates, setHasRestrictedDuplicates] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    problem_domain: 'technical',
    location_type: 'campus',
    category: DEMO_MODE_ENABLED ? PREDEFINED_CATEGORIES[0] : '',
    subcategory: DEMO_MODE_ENABLED ? (CATEGORIES_DATA[PREDEFINED_CATEGORIES[0]][0] || '') : '',
    priority: 'medium',
    campus_id: '',
    building: '',
    floor: '',
    room: '',
    department: user?.department || '',
    affected_users: 1
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch categories & full dynamic campus hierarchy
  useEffect(() => {
    const initData = async () => {
      try {
        const [catsRes, campusesRes, hierRes] = await Promise.all([
          categoryService.getCategories(),
          campusService.getCampuses(),
          campusService.getHierarchy()
        ]);
        const cats = catsRes.data || [];
        const campusRows = campusesRes.data || [];
        const blds = hierRes.data?.buildings || [];

        setCategories(cats);
        setCampuses(campusRows);
        setHierarchy(blds);
        setCustomLocations(hierRes.data?.locations || []);
        if (campusRows.length > 0) {
          setFormData(prev => ({ ...prev, campus_id: prev.campus_id || campusRows[0].id }));
        }

        if (cats.length > 0 && !formData.category) {
          setFormData(prev => ({
            ...prev,
            category: cats[0].name,
            subcategory: cats[0].subcategories?.[0] || ''
          }));
        }
      } catch (err) {
        console.error("Failed to load ticket initial data:", err);
      }
    };
    initData();
  }, []);

  // Fetch suggested KB articles when category changes
  useEffect(() => {
    if (formData.category) {
      knowledgeBaseService.getArticles({ category: formData.category })
        .then(res => setSuggestedArticles(res.data?.articles || []))
        .catch(err => console.error(err));
    }
  }, [formData.category]);

  // Real-time Duplicate Detection (debounced)
  useEffect(() => {
    if (formData.title.length >= 6 && formData.building && formData.room) {
      const timer = setTimeout(async () => {
        try {
          const res = await ticketService.checkDuplicates({
            title: formData.title,
            category: formData.category,
            building: formData.building,
            room: formData.room,
            campus_id: formData.campus_id || null
          });
          setDuplicates(res.data.potential_duplicates || []);
          setHasRestrictedDuplicates(Boolean(res.data.has_restricted_matches));
        } catch (e) {
          console.error(e);
        }
      }, 500);
      return () => clearTimeout(timer);
    } else {
      setDuplicates([]);
      setHasRestrictedDuplicates(false);
    }
  }, [formData.title, formData.category, formData.campus_id, formData.building, formData.room]);

  // Merge predefined buildings with database hierarchy buildings
  const allBuildings = useMemo(() => {
    const set = new Set(DEMO_MODE_ENABLED && !formData.campus_id ? PREDEFINED_BUILDINGS : []);
    hierarchy.filter(b => !formData.campus_id || b.campus_id === formData.campus_id).forEach(b => {
      if (b.name) set.add(b.name);
    });
    return Array.from(set);
  }, [hierarchy, formData.campus_id]);

  // Resolve the selected building within the chosen campus.
  const selectedBuildingObj = hierarchy.find(
    b => (!formData.campus_id || b.campus_id === formData.campus_id) && b.name?.toLowerCase() === formData.building?.trim().toLowerCase()
  );

  // Dynamic floor suggestions: database floors if matching building, plus standard floor list
  const allFloors = useMemo(() => {
    if (selectedBuildingObj && selectedBuildingObj.floors?.length > 0) {
      return selectedBuildingObj.floors.map(f => f.floor_name);
    }
    return DEMO_MODE_ENABLED && (!formData.campus_id || Boolean(selectedBuildingObj)) ? PREDEFINED_FLOORS : [];
  }, [selectedBuildingObj, formData.campus_id]);

  // Dynamic room suggestions
  const selectedFloorObj = selectedBuildingObj?.floors?.find(
    f => f.floor_name?.toLowerCase() === formData.floor?.trim().toLowerCase()
  );

  const allRooms = useMemo(() => {
    const configuredRooms = selectedFloorObj?.rooms?.map(r => r.room_number) || [];
    const configuredPlaces = customLocations
      .filter(location => location.building_id === selectedBuildingObj?.id
        && (!location.floor_id || location.floor_id === selectedFloorObj?.id))
      .map(location => location.name);
    const configured = Array.from(new Set([...configuredRooms, ...configuredPlaces]));
    if (configured.length) return configured;
    return DEMO_MODE_ENABLED && (!formData.campus_id || Boolean(selectedBuildingObj && (!selectedBuildingObj.floors?.length || selectedFloorObj))) ? PREDEFINED_ROOMS : [];
  }, [selectedFloorObj, selectedBuildingObj, formData.campus_id, customLocations]);

  // All categories
  const allCategories = useMemo(() => {
    const set = new Set(DEMO_MODE_ENABLED ? PREDEFINED_CATEGORIES : []);
    categories.forEach(c => {
      if (c.name) set.add(c.name);
    });
    return Array.from(set);
  }, [categories]);

  // Dynamic subcategories based on current category
  const allSubcategories = useMemo(() => {
    if (!formData.category) return [];

    // Database category is authoritative; predefined values are development/demo-only.
    const dbMatch = categories.find(
      c => c.name?.toLowerCase() === formData.category.trim().toLowerCase()
    );
    if (dbMatch) return dbMatch.subcategories || [];

    const predefined = DEMO_MODE_ENABLED ? CATEGORIES_DATA[formData.category] : null;
    if (predefined) return predefined;

    return [];
  }, [formData.category, categories]);

  const handleDomainChange = (e) => {
    const problem_domain = e.target.value;
    const defaultCategoryByDomain = {
      technical: 'Network and Wi-Fi',
      academic: 'Academic Support',
      administrative: 'Administrative and Documentation',
      facilities: 'Campus Facilities and Maintenance',
      personal_support: 'Student and Community Support',
      community: 'Student and Community Support',
      other: 'Student and Community Support'
    };
    setFormData(prev => ({
      ...prev,
      problem_domain,
      category: defaultCategoryByDomain[problem_domain] || prev.category,
      subcategory: ''
    }));
  };

  const handleCategoryChange = (e) => {
    const newCategory = e.target.value;
    const oldSubcategory = formData.subcategory;

    const validSubs = categories.find(c => c.name?.toLowerCase() === newCategory?.toLowerCase())?.subcategories ||
      (DEMO_MODE_ENABLED ? CATEGORIES_DATA[newCategory] : null) || [];

    const shouldKeepSub = validSubs.includes(oldSubcategory);

    setFormData(prev => ({
      ...prev,
      category: newCategory,
      subcategory: shouldKeepSub ? oldSubcategory : ''
    }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      if (name === 'building') return { ...prev, building: value, floor: '', room: '' };
      if (name === 'floor') return { ...prev, floor: value, room: '' };
      return { ...prev, [name]: value };
    });
  };

  // Map priority to SLA target for display panel
  const slaTargetMap = {
    critical: 2,
    high: 8,
    medium: 24,
    low: 72
  };
  const activeSlaTarget = slaTargetMap[formData.priority] || 24;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.location_type === 'campus' &&
        ((campuses.length > 0 && !formData.campus_id) || !formData.building || !formData.floor || !formData.room)) {
      setError('Please select a campus and provide a valid Building, Floor, and Room, or choose a non-campus location type.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload = {
        title: formData.title,
        description: formData.description,
        problem_domain: formData.problem_domain,
        location_type: formData.location_type,
        category: formData.category,
        subcategory: formData.subcategory || null,
        priority: formData.priority,
        campus_id: formData.location_type === 'campus' ? (formData.campus_id || null) : null,
        building: formData.location_type === 'campus' ? formData.building : 'Not applicable',
        floor: formData.location_type === 'campus' ? formData.floor : 'Not applicable',
        room: formData.location_type === 'campus' ? formData.room : 'Not applicable',
        department: formData.department || null,
        affected_users: parseInt(formData.affected_users, 10) || 1
      };

      const res = await ticketService.createTicket(payload, true);
      const createdTicket = res.data;
      navigate(`/tickets/${createdTicket.id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to submit ticket. Please check location details and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '850px', margin: '0 auto', paddingBottom: '3rem' }}>
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--text-main)', letterSpacing: '-0.025em' }}>
          Report a Campus Technical Issue
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Submit a ticket to campus IT support. We track SLA resolution targets based on issue severity and location.
        </p>
      </div>

      {/* Suggested Knowledge Base Articles for Deflection */}
      {suggestedArticles.length > 0 && (
        <div style={{
          backgroundColor: 'rgba(37, 99, 235, 0.05)',
          border: '1px solid rgba(37, 99, 235, 0.2)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          marginBottom: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.125rem' }}>💡</span>
            <span style={{ fontSize: '0.875rem', fontWeight: '700', color: 'var(--brand-blue)' }}>
              Self-Service Solutions Available for &quot;{formData.category}&quot;
            </span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Check if these quick guides solve your problem before submitting a ticket:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
            {suggestedArticles.slice(0, 3).map((art) => (
              <Link
                key={art.id}
                to={`/knowledge-base?search=${encodeURIComponent(art.title)}`}
                target="_blank"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.625rem 0.875rem',
                  backgroundColor: 'var(--card-bg)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  textDecoration: 'none',
                  fontSize: '0.8125rem',
                  fontWeight: '600',
                  color: 'var(--text-main)'
                }}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {art.title}
                </span>
                <ExternalLink size={14} color="var(--text-muted)" style={{ flexShrink: 0, marginLeft: '0.5rem' }} />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Duplicate Ticket Warning */}
      {(duplicates.length > 0 || hasRestrictedDuplicates) && (
        <div style={{
          backgroundColor: 'rgba(217, 119, 6, 0.08)',
          border: '1px solid rgba(217, 119, 6, 0.3)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          marginBottom: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--priority-warning)', marginBottom: '0.5rem' }}>
            <AlertTriangle size={18} />
            <span style={{ fontWeight: '700', fontSize: '0.875rem' }}>
              Potential Duplicate Complaints Detected at this Location
            </span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            {duplicates.length > 0
              ? `Similar issues have already been reported in ${formData.building} (${formData.room}). You can view tickets you are authorized to access:`
              : `A similar issue may already have been reported in ${formData.building} (${formData.room}). Existing ticket details are restricted to their owners and assigned technicians.`}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {duplicates.map((dup) => (
              <div
                key={dup.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  backgroundColor: 'var(--card-bg)',
                  padding: '0.625rem 0.875rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.8125rem'
                }}
              >
                <div>
                  <span style={{ fontWeight: '700', fontFamily: 'monospace', color: 'var(--brand-blue)', marginRight: '0.5rem' }}>
                    {dup.ticket_id}
                  </span>
                  <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{dup.title}</span>
                  <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>({dup.status})</span>
                </div>
                <Link
                  to={`/tickets/${dup.id}`}
                  target="_blank"
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.75rem' }}
                >
                  View Ticket <ExternalLink size={12} />
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ padding: '2rem' }}>
        {error && (
          <div style={{
            backgroundColor: 'rgba(220, 38, 38, 0.1)',
            border: '1px solid rgba(220, 38, 38, 0.3)',
            color: 'var(--priority-critical)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.875rem',
            marginBottom: '1.5rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Title */}
          <div className="form-group">
            <label className="form-label">Complaint Title *</label>
            <input
              type="text"
              name="title"
              className="form-control"
              placeholder="e.g. Projector HDMI port defective in Smart Classroom 101"
              value={formData.title}
              onChange={handleChange}
              minLength={5}
              required
            />
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="form-label">Detailed Description of Problem *</label>
            <textarea
              name="description"
              className="form-control"
              placeholder="Please provide specific details: What happened? What errors appeared? Is it occurring during an ongoing lecture?"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              minLength={10}
              required
            />
          </div>

          {/* General-purpose problem domains */}
          <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="problem-domain">What kind of help do you need? *</label>
              <select id="problem-domain" name="problem_domain" className="form-control" value={formData.problem_domain} onChange={handleDomainChange} required>
                <option value="technical">Technical support</option>
                <option value="academic">Academic and learning support</option>
                <option value="administrative">Administrative and documentation</option>
                <option value="facilities">Campus facilities and maintenance</option>
                <option value="personal_support">Student guidance and personal support</option>
                <option value="community">Community and shared concerns</option>
                <option value="other">Other / not sure</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="location-type">Where does this problem apply? *</label>
              <select id="location-type" name="location_type" className="form-control" value={formData.location_type} onChange={handleChange} required>
                <option value="campus">At a campus location</option>
                <option value="remote">Online / remote</option>
                <option value="not_applicable">No specific location</option>
              </select>
            </div>
          </div>

          {/* Category & Subcategory: Dual-Mode Editable Dropdowns */}
          <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Category *</label>
              <input
                type="text"
                list="category-suggestions"
                name="category"
                data-testid="category-input"
                className="form-control"
                placeholder="Select or type category (e.g. Network & Internet)"
                value={formData.category}
                onChange={handleCategoryChange}
                required
              />
              <datalist id="category-suggestions">
                {allCategories.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </div>

            <div className="form-group">
              <label className="form-label">Subcategory</label>
              <input
                type="text"
                list="subcategory-suggestions"
                name="subcategory"
                data-testid="subcategory-input"
                className="form-control"
                placeholder="Select or type subcategory (e.g. Wi-Fi, Projector)"
                value={formData.subcategory}
                onChange={handleChange}
              />
              <datalist id="subcategory-suggestions">
                {allSubcategories.map((sub) => (
                  <option key={sub} value={sub} />
                ))}
              </datalist>
            </div>
          </div>

          {formData.location_type === 'campus' && <>
          {/* Campus is a required parent in a multi-campus installation. */}
          {campuses.length > 0 && <div className="form-group" style={{ maxWidth: '420px' }}>
            <label className="form-label" htmlFor="ticket-campus">Campus *</label>
            <select id="ticket-campus" name="campus_id" className="form-control" value={formData.campus_id} onChange={e => setFormData(prev => ({ ...prev, campus_id: e.target.value, building: '', floor: '', room: '' }))} required={formData.location_type === 'campus'}>
              <option value="">Select campus</option>
              {campuses.map(campus => <option key={campus.id} value={campus.id}>{campus.name}</option>)}
            </select>
          </div>}
          {campuses.length === 0 && !DEMO_MODE_ENABLED && <p className="form-hint">No campus has been configured yet. Contact your administrator before submitting a ticket.</p>}

          {/* Location Details: database-backed editable suggestions */}
          <div className="grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginTop: '0.5rem', marginBottom: '0.5rem' }}>
            {/* Campus Building */}
            <div className="form-group">
              <label className="form-label">Campus Building *</label>
              <input
                type="text"
                list="building-suggestions"
                name="building"
                data-testid="building-select"
                className="form-control"
                placeholder="Select a configured building"
                value={formData.building}
                onChange={handleChange}
                required={formData.location_type === 'campus'}
              />
              <datalist id="building-suggestions">
                {allBuildings.map((b) => (
                  <option key={b} value={b} />
                ))}
              </datalist>
            </div>

            {/* Floor */}
            <div className="form-group">
              <label className="form-label">Floor *</label>
              <input
                type="text"
                list="floor-suggestions"
                name="floor"
                data-testid="floor-select"
                className="form-control"
                placeholder="Select a configured floor"
                value={formData.floor}
                onChange={handleChange}
                required={formData.location_type === 'campus'}
              />
              <datalist id="floor-suggestions">
                {allFloors.map((flr) => (
                  <option key={flr} value={flr} />
                ))}
              </datalist>
            </div>

            {/* Room / Lab Number */}
            <div className="form-group">
              <label className="form-label">Room / Classroom / Other Location *</label>
              <input
                type="text"
                list="room-suggestions"
                name="room"
                data-testid="room-select"
                className="form-control"
                placeholder="Classroom, lab, hostel room or other location"
                value={formData.room}
                onChange={handleChange}
                required={formData.location_type === 'campus'}
              />
              <datalist id="room-suggestions">
                {allRooms.map((rm) => (
                  <option key={rm} value={rm} />
                ))}
              </datalist>
            </div>
          </div>
          <p className="form-hint">Use a registered campus location. If a building, floor, or room is missing, ask an administrator to add it under Campus Setup.</p>
          </>}
          {formData.location_type !== 'campus' && <p className="form-hint">This request does not require a campus building, floor, or room.</p>}

          {/* Department (Derived), Affected Users, Priority */}
          <div className="grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginTop: '0.5rem' }}>
            <div className="form-group">
              <label className="form-label">Derived Department</label>
              <input
                type="text"
                name="department"
                className="form-control"
                placeholder="Derived from room configuration"
                value={formData.department}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Number of Affected Users</label>
              <input
                type="number"
                name="affected_users"
                className="form-control"
                value={formData.affected_users}
                onChange={handleChange}
                min={1}
                max={500}
              />
            </div>

            {/* Priority Selector */}
            <div className="form-group">
              <label className="form-label">Priority Level *</label>
              <div style={{ position: 'relative' }}>
                <select
                  name="priority"
                  className="form-control"
                  value={formData.priority}
                  onChange={handleChange}
                  style={{
                    paddingLeft: '2rem',
                    fontWeight: '600'
                  }}
                  required
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                  <option value="critical">Critical Priority</option>
                </select>
                <span
                  style={{
                    position: 'absolute',
                    left: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor:
                      formData.priority === 'critical' ? 'var(--priority-critical)' :
                      formData.priority === 'high' ? 'var(--priority-high)' :
                      formData.priority === 'medium' ? 'var(--priority-medium)' :
                      'var(--priority-low)'
                  }}
                />
              </div>
            </div>
          </div>

          {/* SLA Target Information Panel */}
          <div style={{ marginTop: '1.5rem', marginBottom: '2rem' }}>
            <label className="form-label" style={{ marginBottom: '0.5rem' }}>Governing SLA Policy</label>
            <SLAIndicator
              isOverdue={false}
              timeRemainingMinutes={activeSlaTarget * 60}
              targetHours={activeSlaTarget}
            />
          </div>

          {/* Form Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/dashboard')}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              {loading ? (
                <span>Submitting Issue...</span>
              ) : (
                <>
                  <PlusCircle size={18} />
                  <span>Submit Ticket</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

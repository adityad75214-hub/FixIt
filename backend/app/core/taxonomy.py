"""
Centralized Taxonomy for FIXIT Backend:
Contains definitions for:
- 15 Predefined Campus Buildings
- 15 Predefined Categories with component-oriented subcategories
- Predefined Floors & Rooms
"""

from typing import List, Dict

PREDEFINED_BUILDINGS: List[str] = [
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
]

PREDEFINED_FLOORS: List[str] = [
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
]

PREDEFINED_ROOMS: List[str] = [
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
]

CATEGORIES_WITH_SUBCATEGORIES: Dict[str, List[str]] = {
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
        "Subject Guidance", "Course / Syllabus Query", "Assignment Support",
        "Project Guidance", "Research Guidance", "Laboratory Learning Support",
        "Study Resources", "Exam Preparation"
    ],
    "Career & Placement Guidance": [
        "Resume Review", "Interview Preparation", "Internship Guidance",
        "Placement Support", "Higher Studies Guidance", "Career Counselling"
    ],
    "Administrative & Documentation": [
        "Bonafide Certificate", "Transcript / Marksheet", "Scholarship Query",
        "Fee / Payment Query", "Admission / Enrollment", "ID Card",
        "Official Records", "General Office Enquiry"
    ],
    "Campus Facilities & Maintenance": [
        "Hostel / Accommodation", "Transport", "Drinking Water",
        "Washroom / Sanitation", "Electricity / Lighting", "Furniture",
        "Cleaning / Waste Management", "Accessibility", "Safety / Security"
    ],
    "Student & Community Support": [
        "Student Guidance", "Peer Support", "Accessibility Assistance",
        "Community Concern", "Volunteer Assistance", "Other Support Request"
    ]
}

PREDEFINED_CATEGORIES: List[str] = list(CATEGORIES_WITH_SUBCATEGORIES.keys())

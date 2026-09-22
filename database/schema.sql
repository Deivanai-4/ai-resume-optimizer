-- AI Career Intelligence Platform - Full Database Schema
-- Run this file once to initialize the database

CREATE DATABASE IF NOT EXISTS ai_career_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_career_platform;

-- ============================================================
- 1. USERS TABLE (Authentication)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    reset_token VARCHAR(100) NULL,
    reset_token_expires DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email)
) ENGINE=InnoDB;


-- 2. STUDENT PROFILES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    phone VARCHAR(20) NULL,
    date_of_birth DATE NULL,
    gender ENUM('Male', 'Female', 'Other', 'Prefer not to say') NULL,
    location VARCHAR(100) NULL,
    career_objective TEXT NULL,
    photo_path VARCHAR(255) NULL,
    github_url VARCHAR(255) NULL,
    linkedin_url VARCHAR(255) NULL,
    portfolio_url VARCHAR(255) NULL,
    resume_count INT DEFAULT 0,
    profile_completion INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 3. EDUCATION TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS education (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    degree VARCHAR(100) NOT NULL,
    field_of_study VARCHAR(100) NULL,
    institution VARCHAR(150) NOT NULL,
    university VARCHAR(150) NULL,
    start_year INT NULL,
    end_year INT NULL,
    cgpa DECIMAL(4,2) NULL,
    percentage DECIMAL(5,2) NULL,
    is_current BOOLEAN DEFAULT FALSE,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 4. SKILLS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    category ENUM('Programming', 'Framework', 'Database', 'Cloud', 'DevOps', 'Tool', 'Soft Skill', 'Other') DEFAULT 'Other',
    proficiency ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') DEFAULT 'Intermediate',
    proficiency_percent INT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 5. PROJECTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NULL,
    technologies VARCHAR(255) NULL,
    github_url VARCHAR(255) NULL,
    live_url VARCHAR(255) NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;





-- ============================================================
-- 6. CERTIFICATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS certifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    cert_name VARCHAR(150) NOT NULL,
    issuing_org VARCHAR(150) NULL,
    issue_date DATE NULL,
    expiry_date DATE NULL,
    credential_id VARCHAR(100) NULL,
    credential_url VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 7. EXPERIENCE TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS experience (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    location VARCHAR(100) NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    is_current BOOLEAN DEFAULT FALSE,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 8. RESUMES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NULL,
    file_type VARCHAR(10) NOT NULL,
    extracted_text LONGTEXT NULL,
    extracted_skills TEXT NULL,
    is_parsed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 9. COMPANIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) NOT NULL UNIQUE,
    website VARCHAR(255) NULL,
    industry VARCHAR(100) NULL,
    location VARCHAR(150) NULL,
    description TEXT NULL,
    founded_year INT NULL,
    employee_count VARCHAR(50) NULL,
    company_type ENUM('Public', 'Private', 'MNC', 'Startup', 'Government') DEFAULT 'Private',
    logo_url VARCHAR(255) NULL,
    avg_salary VARCHAR(100) NULL,
    recruitment_process TEXT NULL,
    culture TEXT NULL,
    ai_profile LONGTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_slug (slug)
) ENGINE=InnoDB;

-- ============================================================
-- 10. COMPANY SKILLS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS company_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    category ENUM('Programming', 'Framework', 'Database', 'Cloud', 'DevOps', 'Tool', 'Other') DEFAULT 'Other',
    importance ENUM('Required', 'Preferred', 'Nice to have') DEFAULT 'Required',
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 11. COMPANY JOBS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS company_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    job_title VARCHAR(150) NOT NULL,
    job_type ENUM('Full-time', 'Part-time', 'Internship', 'Contract') DEFAULT 'Full-time',
    location VARCHAR(100) NULL,
    salary_range VARCHAR(100) NULL,
    experience_required VARCHAR(50) NULL,
    description TEXT NULL,
    requirements TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    posted_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 12. RESUME ANALYSIS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS resume_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    resume_id INT NOT NULL,
    company_id INT NULL,
    job_title VARCHAR(150) NULL,
    ats_score INT DEFAULT 0,
    skill_match_score INT DEFAULT 0,
    tech_match_score INT DEFAULT 0,
    project_match_score INT DEFAULT 0,
    career_readiness_score INT DEFAULT 0,
    interview_readiness_score INT DEFAULT 0,
    strengths TEXT NULL,
    weaknesses TEXT NULL,
    missing_skills TEXT NULL,
    resume_suggestions TEXT NULL,
    resume_summary TEXT NULL,
    keyword_analysis TEXT NULL,
    grammar_score INT DEFAULT 0,
    formatting_score INT DEFAULT 0,
    overall_score INT DEFAULT 0,
    analysis_data LONGTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 13. OPTIMIZED RESUMES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS optimized_resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    resume_id INT NOT NULL,
    analysis_id INT NULL,
    original_text LONGTEXT NULL,
    optimized_text LONGTEXT NULL,
    professional_summary TEXT NULL,
    changes_made TEXT NULL,
    improvement_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 14. LEARNING ROADMAPS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_roadmaps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_id INT NULL,
    resume_id INT NULL,
    title VARCHAR(200) NULL,
    total_duration_weeks INT DEFAULT 12,
    status ENUM('Active', 'Completed', 'Paused') DEFAULT 'Active',
    completion_percent INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 15. ROADMAP ITEMS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS roadmap_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roadmap_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    priority ENUM('Critical', 'High', 'Medium', 'Low') DEFAULT 'Medium',
    duration_weeks INT DEFAULT 1,
    order_index INT DEFAULT 0,
    status ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started',
    resources TEXT NULL,
    youtube_links TEXT NULL,
    doc_links TEXT NULL,
    project_ideas TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (roadmap_id) REFERENCES learning_roadmaps(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 16. INTERVIEW QUESTIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS interview_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_id INT NULL,
    resume_id INT NULL,
    question TEXT NOT NULL,
    answer TEXT NULL,
    category ENUM('Technical', 'HR', 'Coding', 'Aptitude', 'Company Specific') DEFAULT 'Technical',
    difficulty ENUM('Easy', 'Medium', 'Hard') DEFAULT 'Medium',
    ai_tip TEXT NULL,
    user_answer TEXT NULL,
    score INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- 17. REPORTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    report_type ENUM('Career', 'ATS', 'Resume', 'Learning', 'Placement') DEFAULT 'Career',
    title VARCHAR(200) NULL,
    file_path VARCHAR(500) NULL,
    file_format ENUM('PDF', 'DOCX') DEFAULT 'PDF',
    analysis_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 18. ACTIVITY LOGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT NULL,
    entity_type VARCHAR(50) NULL,
    entity_id INT NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_action (user_id, created_at)
) ENGINE=InnoDB;

-- ============================================================
-- 19. SETTINGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    theme ENUM('light', 'dark') DEFAULT 'light',
    email_notifications BOOLEAN DEFAULT TRUE,
    placement_alerts BOOLEAN DEFAULT TRUE,
    weekly_report BOOLEAN DEFAULT FALSE,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- SEED DATA: Companies
-- ============================================================
INSERT INTO companies (name, slug, website, industry, location, description, founded_year, employee_count, company_type, avg_salary, recruitment_process) VALUES
('Zoho Corporation', 'zoho-corporation', 'https://zoho.com', 'Software Development', 'Chennai, Tamil Nadu, India', 'Zoho is a global technology company that makes software tools for businesses of all sizes. They focus on long-term R&D and build products from the ground up, known for their strong engineering culture and boot-strapped growth.', 1996, '10,000+', 'Private', '4-12 LPA', 'Online Test → Technical Interview → HR Interview'),
('Tata Consultancy Services', 'tcs', 'https://tcs.com', 'IT Services', 'Mumbai, Maharashtra, India', 'TCS is one of the largest IT services companies in the world, offering consulting, IT, and business solutions. Known for mass hiring from campuses every year.', 1968, '600,000+', 'Public', '3-7 LPA', 'TCS NQT → Technical Interview → HR Interview → Offer'),
('Infosys', 'infosys', 'https://infosys.com', 'IT Services', 'Bengaluru, Karnataka, India', 'Infosys is a global leader in next-generation digital services and consulting. They enable clients in more than 50 countries to navigate their digital transformation.', 1981, '300,000+', 'Public', '3.5-8 LPA', 'InfyTQ → Online Test → Technical Interview → HR'),
('Wipro', 'wipro', 'https://wipro.com', 'IT Services', 'Bengaluru, Karnataka, India', 'Wipro Limited is a leading global information technology, consulting and business process services company.', 1945, '250,000+', 'Public', '3.5-7 LPA', 'NLTH Test → Technical Interview → HR Round'),
('Cognizant', 'cognizant', 'https://cognizant.com', 'IT Services', 'Chennai, Tamil Nadu, India', 'Cognizant is a multinational IT services and consulting company. It is one of the worlds leading professional services companies.', 1994, '350,000+', 'Public', '4-8 LPA', 'CoCubes Test → Technical Interview → HR'),
('HCL Technologies', 'hcl-technologies', 'https://hcltech.com', 'IT Services', 'Noida, Uttar Pradesh, India', 'HCL Technologies is an Indian multinational IT services company. They offer a wide range of IT services and solutions.', 1976, '200,000+', 'Public', '3.5-8 LPA', 'Aptitude Test → Technical Interview → HR'),
('Accenture', 'accenture', 'https://accenture.com', 'IT Consulting', 'Dublin, Ireland (India HQ: Mumbai)', 'Accenture is a global professional services company with expertise in digital, cloud and security.', 1989, '750,000+', 'Public', '4-10 LPA', 'Online Assessment → Technical Interview → HR Interview'),
('Amazon', 'amazon', 'https://amazon.com', 'E-Commerce / Cloud', 'Seattle, USA (India: Bengaluru)', 'Amazon is the worlds largest e-commerce company and a leading cloud provider through AWS. Known for high standards and bar-raising interviews.', 1994, '1,500,000+', 'Public', '15-50 LPA', 'OA → Phone Screen → Virtual Onsite (4-5 rounds) → Bar Raiser'),
('Google', 'google', 'https://google.com', 'Technology', 'Mountain View, USA (India: Bengaluru/Hyderabad)', 'Google LLC is an American multinational technology company focusing on AI, search, cloud computing, and advertising.', 1998, '180,000+', 'Public', '20-80 LPA', 'Phone Screen → Technical Rounds (4-5) → Hiring Committee → Offer'),
('Microsoft', 'microsoft', 'https://microsoft.com', 'Technology', 'Redmond, USA (India: Hyderabad)', 'Microsoft Corporation is an American multinational technology company producing computer software, consumer electronics, personal computers, and related services.', 1975, '220,000+', 'Public', '18-70 LPA', 'Online Assessment → Phone Screen → Virtual Onsite (3-4 rounds)'),
('Flipkart', 'flipkart', 'https://flipkart.com', 'E-Commerce', 'Bengaluru, Karnataka, India', 'Flipkart is an Indian e-commerce company. It is the largest e-commerce marketplace in India. Owned by Walmart.', 2007, '50,000+', 'Private', '10-40 LPA', 'Online Test → Technical Rounds (2-3) → Hiring Manager → HR'),
('Swiggy', 'swiggy', 'https://swiggy.com', 'Food Tech', 'Bengaluru, Karnataka, India', 'Swiggy is an Indian online food ordering and delivery platform. Fast-growing startup with strong engineering culture.', 2014, '5,000+', 'Private', '8-35 LPA', 'Online Assessment → Technical Interviews → System Design → HR'),
('Razorpay', 'razorpay', 'https://razorpay.com', 'Fintech', 'Bengaluru, Karnataka, India', 'Razorpay is a full-stack financial solutions company, providing payment gateway, banking, payroll and lending solutions.', 2014, '3,000+', 'Private', '10-40 LPA', 'DSA Round → System Design → Culture Fit → Offer'),
('Freshworks', 'freshworks', 'https://freshworks.com', 'SaaS', 'Chennai, Tamil Nadu, India', 'Freshworks makes it fast and easy for businesses to delight their customers and employees. It creates easy-to-use software.', 2010, '7,000+', 'Public', '8-30 LPA', 'Technical Screen → Coding Round → Design → HR');

-- ============================================================
-- SEED DATA: Company Skills
-- ============================================================
INSERT INTO company_skills (company_id, skill_name, category, importance) VALUES
-- Zoho (id=1)
(1, 'Java', 'Programming', 'Required'), (1, 'Python', 'Programming', 'Required'), (1, 'C++', 'Programming', 'Required'),
(1, 'JavaScript', 'Programming', 'Required'), (1, 'React', 'Framework', 'Required'), (1, 'Angular', 'Framework', 'Preferred'),
(1, 'MySQL', 'Database', 'Required'), (1, 'PostgreSQL', 'Database', 'Preferred'), (1, 'AWS', 'Cloud', 'Preferred'),
(1, 'Docker', 'DevOps', 'Preferred'), (1, 'Git', 'Tool', 'Required'), (1, 'REST API', 'Other', 'Required'),
-- TCS (id=2)
(2, 'Java', 'Programming', 'Required'), (2, 'Python', 'Programming', 'Required'), (2, 'SQL', 'Database', 'Required'),
(2, 'JavaScript', 'Programming', 'Required'), (2, 'Spring Boot', 'Framework', 'Preferred'), (2, 'MySQL', 'Database', 'Required'),
(2, 'Linux', 'Tool', 'Preferred'), (2, 'Git', 'Tool', 'Required'), (2, 'Agile', 'Other', 'Preferred'),
-- Infosys (id=3)
(3, 'Java', 'Programming', 'Required'), (3, 'Python', 'Programming', 'Required'), (3, 'SQL', 'Database', 'Required'),
(3, 'JavaScript', 'Programming', 'Required'), (3, 'Angular', 'Framework', 'Preferred'), (3, 'MySQL', 'Database', 'Required'),
(3, 'AWS', 'Cloud', 'Preferred'), (3, 'Git', 'Tool', 'Required'), (3, '.NET', 'Framework', 'Preferred'),
-- Amazon (id=8)
(8, 'Python', 'Programming', 'Required'), (8, 'Java', 'Programming', 'Required'), (8, 'C++', 'Programming', 'Required'),
(8, 'Data Structures', 'Other', 'Required'), (8, 'Algorithms', 'Other', 'Required'), (8, 'AWS', 'Cloud', 'Required'),
(8, 'System Design', 'Other', 'Required'), (8, 'SQL', 'Database', 'Required'), (8, 'Docker', 'DevOps', 'Preferred'),
(8, 'Kubernetes', 'DevOps', 'Preferred'), (8, 'REST API', 'Other', 'Required'),
-- Google (id=9)
(9, 'Python', 'Programming', 'Required'), (9, 'Java', 'Programming', 'Required'), (9, 'C++', 'Programming', 'Required'),
(9, 'Data Structures', 'Other', 'Required'), (9, 'Algorithms', 'Other', 'Required'), (9, 'System Design', 'Other', 'Required'),
(9, 'Machine Learning', 'Other', 'Preferred'), (9, 'SQL', 'Database', 'Required'), (9, 'Google Cloud', 'Cloud', 'Preferred'),
-- Freshworks (id=14)
(14, 'Ruby on Rails', 'Framework', 'Required'), (14, 'Python', 'Programming', 'Required'), (14, 'React', 'Framework', 'Required'),
(14, 'JavaScript', 'Programming', 'Required'), (14, 'MySQL', 'Database', 'Required'), (14, 'Redis', 'Database', 'Preferred'),
(14, 'AWS', 'Cloud', 'Required'), (14, 'Docker', 'DevOps', 'Required'), (14, 'Git', 'Tool', 'Required');

-- ============================================================
-- SEED DATA: Company Jobs
-- ============================================================
INSERT INTO company_jobs (company_id, job_title, job_type, location, salary_range, experience_required, description) VALUES
(1, 'Backend Developer', 'Full-time', 'Chennai, India', '4-8 LPA', '0-2 years', 'We are looking for a skilled backend developer to join our product team at Zoho. You will work on building scalable REST APIs, microservices, and database solutions.'),
(1, 'Frontend Developer', 'Full-time', 'Chennai, India', '4-8 LPA', '0-2 years', 'Join our frontend team to build beautiful, responsive UIs for millions of Zoho users worldwide using React and Angular.'),
(1, 'Full Stack Developer', 'Full-time', 'Chennai, India', '6-12 LPA', '1-3 years', 'Build end-to-end features for our suite of 50+ products at Zoho Corporation.'),
(2, 'System Engineer', 'Full-time', 'Pan India', '3.5-5 LPA', 'Fresher', 'TCS System Engineer role for fresh graduates. Training provided in the first few months before project deployment.'),
(2, 'Software Developer', 'Full-time', 'Pan India', '4-7 LPA', '0-2 years', 'Develop and maintain software applications for TCS clients across domains.'),
(3, 'Software Engineer', 'Full-time', 'Pan India', '3.5-6 LPA', 'Fresher', 'Infosys Software Engineer role for freshers. Comprehensive training at Mysuru campus.'),
(8, 'SDE-1', 'Full-time', 'Bengaluru, India', '20-35 LPA', '0-2 years', 'Software Development Engineer at Amazon. Work on large-scale distributed systems that power the worlds largest e-commerce and cloud platform.'),
(9, 'Software Engineer', 'Full-time', 'Hyderabad/Bengaluru, India', '25-50 LPA', '0-2 years', 'Engineer at Google working on products used by billions. Involves complex algorithm design and system architecture.'),
(14, 'Software Engineer', 'Full-time', 'Chennai, India', '8-18 LPA', '0-2 years', 'Join Freshworks engineering team to build the next generation of customer experience software used by 60,000+ businesses globally.');

CREATE TABLE IF NOT EXISTS generated_resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    source_resume_id INT,
    company_id INT,
    company_name VARCHAR(255),
    job_role VARCHAR(255),
    job_description TEXT,
    template VARCHAR(255),
    content_json LONGTEXT,
    ats_score INT,
    skill_match INT,
    label VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


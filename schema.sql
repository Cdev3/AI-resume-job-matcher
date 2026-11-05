-- =====================================================================
-- Database Schema for AI Resume & Job Description Matcher
-- =====================================================================

CREATE DATABASE IF NOT EXISTS resume_matcher;
USE resume_matcher;

CREATE TABLE IF NOT EXISTS analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_name VARCHAR(255) NOT NULL DEFAULT 'Unknown Candidate',
    resume_filename VARCHAR(255) DEFAULT 'text_input',
    job_title VARCHAR(255) DEFAULT 'General Software Engineer',
    match_score FLOAT NOT NULL DEFAULT 0.0,
    matched_skills TEXT,
    missing_skills TEXT,
    resume_text LONGTEXT,
    job_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_match_score (match_score),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample Seed Data
INSERT INTO analyses (candidate_name, resume_filename, job_title, match_score, matched_skills, missing_skills)
VALUES
    ('John Doe', 'john_resume.pdf', 'Senior Python Developer', 82.5,
     '["python", "flask", "mysql", "docker", "git", "rest", "linux"]',
     '["kubernetes", "aws", "redis"]'),
    ('Jane Smith', 'jane_cv.docx', 'Full Stack Engineer', 74.0,
     '["javascript", "react", "html", "css", "node.js", "sql"]',
     '["typescript", "docker", "graphql"]'),
    ('Alex Brown', 'alex_resume.pdf', 'DevOps Specialist', 50.0,
     '["linux", "bash", "git", "python"]',
     '["terraform", "ansible", "kubernetes", "jenkins", "aws"]');

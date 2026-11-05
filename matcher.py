"""
Core NLP and Skill Extraction Engine for AI Resume & Job Description Matcher.
"""

import re
import os

# Try importing PDF and DOCX handlers safely
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

# Comprehensive Database of Skills organized by Industry Categories
SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "ruby", "go", "golang", "rust", "swift", "kotlin", "php", "scala",
        "perl", "r", "matlab", "dart", "lua", "haskell", "elixir",
        "objective-c", "assembly", "bash", "shell", "powershell"
    ],
    "Web Development & Frontend": [
        "html", "html5", "css", "css3", "sass", "less", "bootstrap", "tailwind",
        "tailwind css", "react", "react.js", "reactjs", "angular", "angularjs",
        "vue", "vue.js", "vuejs", "svelte", "next.js", "nextjs", "nuxt.js",
        "webpack", "vite", "jquery", "ajax", "dom", "responsive design",
        "web accessibility", "rest", "restful", "rest api", "graphql", "websocket"
    ],
    "Backend & Frameworks": [
        "node.js", "nodejs", "express", "express.js", "django", "flask",
        "fastapi", "spring", "spring boot", "asp.net", ".net", "dotnet",
        "rails", "ruby on rails", "laravel", "symfony", "gin", "nest.js",
        "nestjs", "koa", "tornado", "celery", "microservices"
    ],
    "Databases & Storage": [
        "mysql", "postgresql", "postgres", "mongodb", "sqlite", "oracle",
        "sql server", "mssql", "redis", "cassandra", "dynamodb", "couchdb",
        "elasticsearch", "mariadb", "firebase", "supabase", "sql", "nosql",
        "pl/sql", "t-sql", "prisma", "hibernate", "sqlalchemy"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "docker", "kubernetes", "k8s", "jenkins", "ci/cd", "cicd",
        "terraform", "ansible", "puppet", "chef", "github actions",
        "gitlab ci", "circleci", "nginx", "apache", "linux", "ubuntu",
        "serverless", "lambda", "cloudformation", "helm", "grafana", "prometheus"
    ],
    "AI, ML & Data Science": [
        "machine learning", "deep learning", "artificial intelligence", "ai",
        "nlp", "natural language processing", "computer vision", "tensorflow",
        "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy",
        "scipy", "matplotlib", "seaborn", "plotly", "jupyter", "data analysis",
        "data visualization", "statistics", "data science", "llm", "large language models",
        "langchain", "transformers", "bert", "gpt", "hugging face", "opencv", "spacy", "nltk"
    ],
    "Software Engineering & Tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "agile", "scrum", "kanban", "tdd", "unit testing", "integration testing",
        "pytest", "unittest", "selenium", "cypress", "jest", "postman",
        "swagger", "openapi", "docker compose", "design patterns", "oop",
        "object oriented programming", "data structures", "algorithms"
    ],
    "Mobile Development": [
        "android", "ios", "react native", "flutter", "xamarin",
        "swiftui", "jetpack compose", "mobile development"
    ],
    "Cybersecurity": [
        "cybersecurity", "network security", "penetration testing",
        "vulnerability assessment", "owasp", "encryption", "ssl", "tls",
        "oauth", "jwt", "authentication", "authorization", "firewall", "soc"
    ],
    "Soft Skills & Leadership": [
        "problem solving", "communication", "teamwork", "collaboration",
        "leadership", "critical thinking", "time management", "mentoring",
        "project management", "adaptability", "analytical skills", "creativity"
    ]
}

# Build mapping of canonical skill names
CANONICAL_SKILLS = {}
for category, skills in SKILL_CATEGORIES.items():
    for s in skills:
        CANONICAL_SKILLS[s.lower()] = category


def extract_text_from_pdf(filepath):
    """Extract raw text from a PDF file."""
    if PyPDF2 is None:
        return ""
    text_content = []
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
    return "\n".join(text_content)


def extract_text_from_docx(filepath):
    """Extract raw text from a DOCX file."""
    if docx is None:
        return ""
    text_content = []
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            if para.text:
                text_content.append(para.text)
    except Exception as e:
        print(f"Error reading DOCX {filepath}: {e}")
    return "\n".join(text_content)


def extract_text_from_txt(filepath):
    """Extract text from a plain TXT file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT {filepath}: {e}")
        return ""


def extract_resume_text(filepath):
    """Detect file type and extract clean text."""
    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    if ext == 'pdf':
        return extract_text_from_pdf(filepath)
    elif ext == 'docx':
        return extract_text_from_docx(filepath)
    elif ext == 'txt':
        return extract_text_from_txt(filepath)
    return ""


def extract_candidate_name(text):
    """Attempt to extract the candidate's name from resume header lines."""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    stop_words = {'resume', 'curriculum', 'vitae', 'cv', 'profile', 'contact', 'summary',
                  'experience', 'education', 'skills', 'objective', 'email', 'phone'}

    for line in lines[:6]:
        # Filter out emails, URLs, phones, or lines with digits
        if '@' in line or 'http' in line or re.search(r'\d', line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4:
            if not any(w.lower() in stop_words for w in words):
                # Clean punctuation
                cleaned = re.sub(r'[^a-zA-Z\s]', '', line).strip()
                if cleaned:
                    return cleaned
    return "Candidate"


def extract_contact_info(text):
    """Extract email, phone, and links if present."""
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text)

    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None
    }


def normalize_skill_name(skill):
    """Map variants to clean names."""
    variants = {
        "reactjs": "react",
        "react.js": "react",
        "vuejs": "vue",
        "vue.js": "vue",
        "nodejs": "node.js",
        "expressjs": "express",
        "express.js": "express",
        "golang": "go",
        "k8s": "kubernetes",
        "cicd": "ci/cd",
        "html5": "html",
        "css3": "css",
        "tailwind css": "tailwind",
        "nextjs": "next.js",
        "postgres": "postgresql",
        "large language models": "llm",
        "amazon web services": "aws",
        "google cloud": "gcp"
    }
    return variants.get(skill, skill)


def extract_skills(text):
    """
    Search text for registered industry skills using accurate regex matching.
    Returns: dict { category_name: [skill_names...] }
    """
    text_lower = " " + text.lower() + " "
    matched_by_cat = {}

    for skill, category in CANONICAL_SKILLS.items():
        # Match with boundary handling (accounting for special chars like c++, c#, .net)
        escaped = re.escape(skill)
        # Handle word boundary: if skill starts/ends with alphanumeric, require word boundary
        pattern = r'(?<![a-zA-Z0-9_])' + escaped + r'(?![a-zA-Z0-9_])'
        if re.search(pattern, text_lower):
            norm = normalize_skill_name(skill)
            if category not in matched_by_cat:
                matched_by_cat[category] = []
            if norm not in matched_by_cat[category]:
                matched_by_cat[category].append(norm)

    return matched_by_cat


def flatten_skills(skills_by_cat):
    """Flatten categorized skill dictionary into a unique sorted list."""
    flattened = set()
    for skills in skills_by_cat.values():
        for s in skills:
            flattened.add(s)
    return sorted(list(flattened))


def generate_recommendations(match_score, missing_by_cat, total_jd_skills):
    """Generate strategic career & resume optimization recommendations."""
    recommendations = []

    # Score-based verdict
    if match_score >= 80:
        recommendations.append({
            "type": "success",
            "icon": "fa-award",
            "title": "Outstanding Match!",
            "message": "Your profile is strongly aligned with this role. Highlight your relevant project accomplishments and quantified outcomes in your interviews."
        })
    elif match_score >= 60:
        recommendations.append({
            "type": "info",
            "icon": "fa-check-circle",
            "title": "Competitive Match with Targetable Gaps",
            "message": "You possess the core foundational skills. Incorporating key missing technologies into your resume or portfolio projects will dramatically increase interview callbacks."
        })
    elif match_score >= 40:
        recommendations.append({
            "type": "warning",
            "icon": "fa-exclamation-triangle",
            "title": "Moderate Alignment",
            "message": "Your resume matches some requirements but has noticeable gaps. Consider completing hands-on projects or certifications covering the primary missing skills."
        })
    else:
        recommendations.append({
            "type": "danger",
            "icon": "fa-times-circle",
            "title": "Significant Skill Gap",
            "message": "This job requires several technologies not currently detected in your resume. Tailor your resume with relevant transferable experience or build dedicated portfolio projects."
        })

    # Category-specific guidance
    for category, skills in missing_by_cat.items():
        if len(skills) >= 2:
            recommendations.append({
                "type": "category-tip",
                "icon": "fa-lightbulb",
                "title": f"Focus Area: {category}",
                "message": f"Add experience or certifications in {', '.join(skills[:4])} to address key requirements in this category."
            })

    return recommendations


def analyze_resume_against_job(resume_text, job_description):
    """
    Main analysis pipeline:
    - Extracts skills from both documents
    - Computes intersection, difference, and gap metrics
    - Categorizes matches and gaps
    - Calculates match score percentage
    - Generates actionable recommendations
    """
    resume_skills_dict = extract_skills(resume_text)
    jd_skills_dict = extract_skills(job_description)

    resume_skills = set(flatten_skills(resume_skills_dict))
    jd_skills = set(flatten_skills(jd_skills_dict))

    matched_skills = sorted(list(resume_skills & jd_skills))
    missing_skills = sorted(list(jd_skills - resume_skills))
    extra_skills = sorted(list(resume_skills - jd_skills))

    # Match score calculation
    if jd_skills:
        score = round((len(matched_skills) / len(jd_skills)) * 100, 1)
    else:
        # If no explicit skills detected in JD, baseline score
        score = 0.0

    # Categorize matched skills
    matched_by_cat = {}
    for skill in matched_skills:
        cat = CANONICAL_SKILLS.get(skill, "Other Skills")
        matched_by_cat.setdefault(cat, []).append(skill)

    # Categorize missing skills
    missing_by_cat = {}
    for skill in missing_skills:
        cat = CANONICAL_SKILLS.get(skill, "Other Skills")
        missing_by_cat.setdefault(cat, []).append(skill)

    recommendations = generate_recommendations(score, missing_by_cat, len(jd_skills))

    return {
        "match_score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "matched_by_cat": matched_by_cat,
        "missing_by_cat": missing_by_cat,
        "total_jd_skills": len(jd_skills),
        "total_resume_skills": len(resume_skills),
        "total_matched": len(matched_skills),
        "total_missing": len(missing_skills),
        "recommendations": recommendations
    }

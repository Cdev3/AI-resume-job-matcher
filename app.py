"""
AI Resume & Job Description Matcher
Flask Application Main Server
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

from config import Config
import db
import matcher

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Render home page with resume upload and job description form."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle resume upload or text submission and perform match analysis."""
    resume_text = ""
    resume_filename = "pasted_text"

    # 1. Check if a file was uploaded
    if 'resume_file' in request.files and request.files['resume_file'].filename:
        file = request.files['resume_file']
        if file and allowed_file(file.filename):
            safe_name = secure_filename(file.filename)
            resume_filename = safe_name
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)

            # Extract text
            resume_text = matcher.extract_resume_text(filepath)

            # Cleanup uploaded file immediately after extraction for security/privacy
            try:
                os.remove(filepath)
            except OSError:
                pass
        else:
            flash("Invalid file format. Please upload a PDF, DOCX, or TXT file.", "danger")
            return redirect(url_for('index'))
    # 2. Or check if resume text was pasted directly
    elif request.form.get('resume_text', '').strip():
        resume_text = request.form.get('resume_text', '').strip()
    else:
        flash("Please upload a resume file or paste your resume text.", "warning")
        return redirect(url_for('index'))

    # Validate job description
    job_description = request.form.get('job_description', '').strip()
    if not job_description:
        flash("Please provide a job description to match against.", "warning")
        return redirect(url_for('index'))

    job_title = request.form.get('job_title', '').strip() or "Software Engineer"
    candidate_name = matcher.extract_candidate_name(resume_text)

    # Perform analysis
    result = matcher.analyze_resume_against_job(resume_text, job_description)
    result['candidate_name'] = candidate_name
    result['job_title'] = job_title
    result['resume_filename'] = resume_filename

    # Save to database
    db.save_analysis({
        'candidate_name': candidate_name,
        'resume_filename': resume_filename,
        'job_title': job_title,
        'match_score': result['match_score'],
        'matched_skills': result['matched_skills'],
        'missing_skills': result['missing_skills'],
        'resume_text': resume_text,
        'job_description': job_description
    })

    return render_template('results.html', result=result)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """REST API endpoint for automated resume and JD matching."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid request. JSON body expected."}), 400

    resume_text = data.get('resume_text', '').strip()
    job_description = data.get('job_description', '').strip()

    if not resume_text or not job_description:
        return jsonify({"error": "Both 'resume_text' and 'job_description' fields are required."}), 400

    job_title = data.get('job_title', 'Software Engineer')
    candidate_name = matcher.extract_candidate_name(resume_text)

    result = matcher.analyze_resume_against_job(resume_text, job_description)
    result['candidate_name'] = candidate_name
    result['job_title'] = job_title

    db.save_analysis({
        'candidate_name': candidate_name,
        'resume_filename': 'api_payload',
        'job_title': job_title,
        'match_score': result['match_score'],
        'matched_skills': result['matched_skills'],
        'missing_skills': result['missing_skills'],
        'resume_text': resume_text,
        'job_description': job_description
    })

    return jsonify(result), 200


@app.route('/dashboard')
def dashboard():
    """Analytics dashboard page displaying historical scans, scores, and trends."""
    data = db.get_dashboard_stats()
    return render_template('dashboard.html', stats=data, analyses=data['analyses'])


@app.route('/api/history', methods=['GET'])
def api_history():
    """Return JSON history of all past analyses."""
    analyses = db.get_all_analyses(limit=100)
    return jsonify({"count": len(analyses), "analyses": analyses})


@app.route('/delete/<int:analysis_id>', methods=['POST'])
def delete_analysis(analysis_id):
    """Delete an analysis entry."""
    db.delete_analysis(analysis_id)
    flash("Record removed from history.", "info")
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    # Initialize Database on startup
    db.init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 AI Resume Matcher server running at http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

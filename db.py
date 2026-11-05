"""
Database abstraction layer for AI Resume Matcher.
Supports MySQL with automatic SQLite fallback for zero-friction local execution.
"""

import os
import json
import sqlite3
from datetime import datetime
from config import Config

# Try importing mysql connector
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception

USE_SQLITE = False


def get_mysql_connection(include_db=True):
    """Attempt to establish a MySQL connection."""
    if not mysql:
        return None
    try:
        kwargs = {
            "host": Config.DB_HOST,
            "port": Config.DB_PORT,
            "user": Config.DB_USER,
            "password": Config.DB_PASSWORD,
            "connect_timeout": 3
        }
        if include_db:
            kwargs["database"] = Config.DB_NAME
        conn = mysql.connector.connect(**kwargs)
        return conn
    except Exception as e:
        return None


def get_sqlite_connection():
    """Create a connection to SQLite database file."""
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_connection():
    """Returns active database connection and engine type ('mysql' or 'sqlite')."""
    global USE_SQLITE
    if not USE_SQLITE:
        conn = get_mysql_connection(include_db=True)
        if conn and conn.is_connected():
            return conn, 'mysql'
        # Switch to SQLite fallback
        USE_SQLITE = True
        print("ℹ️ MySQL not reachable. Falling back to local SQLite database (resume_matcher.db).")

    return get_sqlite_connection(), 'sqlite'


def init_db():
    """Initialize MySQL or SQLite database schema."""
    global USE_SQLITE
    # 1. Try initializing MySQL
    conn_raw = get_mysql_connection(include_db=False)
    if conn_raw and conn_raw.is_connected():
        try:
            cursor = conn_raw.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
            cursor.close()
            conn_raw.close()

            # Now connect to database and create table
            conn = get_mysql_connection(include_db=True)
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analyses (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        candidate_name VARCHAR(255) DEFAULT 'Unknown Candidate',
                        resume_filename VARCHAR(255) DEFAULT 'text_input',
                        job_title VARCHAR(255) DEFAULT 'General Position',
                        match_score FLOAT DEFAULT 0.0,
                        matched_skills TEXT,
                        missing_skills TEXT,
                        resume_text LONGTEXT,
                        job_description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                cursor.close()
                conn.close()
                USE_SQLITE = False
                print(" Connected to MySQL database successfully.")
                return
        except Exception as e:
            print(f"MySQL initialization notice: {e}")

    # 2. Fallback to SQLite
    USE_SQLITE = True
    print("ℹ️ Initializing local SQLite database for instant zero-configuration testing...")
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT DEFAULT 'Unknown Candidate',
            resume_filename TEXT DEFAULT 'text_input',
            job_title TEXT DEFAULT 'General Position',
            match_score REAL DEFAULT 0.0,
            matched_skills TEXT,
            missing_skills TEXT,
            resume_text TEXT,
            job_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(" SQLite database initialized successfully.")


def save_analysis(data):
    """
    Persist analysis record to DB.
    data: dict with candidate_name, resume_filename, job_title, match_score, matched_skills, missing_skills, resume_text, job_description
    """
    conn, engine = get_connection()
    try:
        cursor = conn.cursor()
        matched_json = json.dumps(data.get('matched_skills', []))
        missing_json = json.dumps(data.get('missing_skills', []))

        if engine == 'mysql':
            sql = """
                INSERT INTO analyses 
                (candidate_name, resume_filename, job_title, match_score, matched_skills, missing_skills, resume_text, job_description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data.get('candidate_name', 'Unknown Candidate'),
                data.get('resume_filename', 'text_input'),
                data.get('job_title', 'General Position'),
                data.get('match_score', 0.0),
                matched_json,
                missing_json,
                data.get('resume_text', '')[:10000],
                data.get('job_description', '')[:10000]
            ))
            conn.commit()
            last_id = cursor.lastrowid
        else:
            sql = """
                INSERT INTO analyses 
                (candidate_name, resume_filename, job_title, match_score, matched_skills, missing_skills, resume_text, job_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                data.get('candidate_name', 'Unknown Candidate'),
                data.get('resume_filename', 'text_input'),
                data.get('job_title', 'General Position'),
                data.get('match_score', 0.0),
                matched_json,
                missing_json,
                data.get('resume_text', '')[:10000],
                data.get('job_description', '')[:10000]
            ))
            conn.commit()
            last_id = cursor.lastrowid

        cursor.close()
        conn.close()
        return last_id
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return None


def get_all_analyses(limit=50):
    """Retrieve all past analyses."""
    conn, engine = get_connection()
    results = []
    try:
        if engine == 'mysql':
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, candidate_name, resume_filename, job_title, match_score, matched_skills, missing_skills, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()
            cursor.close()
        else:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, candidate_name, resume_filename, job_title, match_score, matched_skills, missing_skills, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()

        conn.close()

        for row in rows:
            try:
                row['matched_skills'] = json.loads(row.get('matched_skills') or '[]')
            except Exception:
                row['matched_skills'] = []
            try:
                row['missing_skills'] = json.loads(row.get('missing_skills') or '[]')
            except Exception:
                row['missing_skills'] = []

            if isinstance(row.get('created_at'), datetime):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M')
            results.append(row)

        return results
    except Exception as e:
        print(f"Error fetching analyses: {e}")
        return []


def delete_analysis(analysis_id):
    """Delete an analysis record by ID."""
    conn, engine = get_connection()
    try:
        cursor = conn.cursor()
        if engine == 'mysql':
            cursor.execute("DELETE FROM analyses WHERE id = %s", (analysis_id,))
        else:
            cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting analysis: {e}")
        return False


def get_dashboard_stats():
    """Compute aggregate analytics for the dashboard."""
    analyses = get_all_analyses(limit=500)
    if not analyses:
        return {
            "total_analyses": 0,
            "avg_score": 0.0,
            "highest_score": 0.0,
            "lowest_score": 0.0,
            "above_70": 0,
            "below_50": 0,
            "analyses": []
        }

    scores = [a['match_score'] for a in analyses if a.get('match_score') is not None]
    return {
        "total_analyses": len(analyses),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "highest_score": max(scores) if scores else 0.0,
        "lowest_score": min(scores) if scores else 0.0,
        "above_70": len([s for s in scores if s >= 70]),
        "below_50": len([s for s in scores if s < 50]),
        "analyses": analyses
    }

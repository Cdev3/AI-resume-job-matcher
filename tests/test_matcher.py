"""
Unit tests for AI Resume & Job Description Matcher.
Run with: pytest
"""

import sys
import os
import unittest

# Ensure current directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import matcher

class TestResumeMatcher(unittest.TestCase):

    def setUp(self):
        self.sample_resume = """
        John Doe
        Senior Software Engineer
        Email: john.doe@example.com

        Skills:
        - Python, Flask, Django, REST API
        - MySQL, PostgreSQL, Docker, Git
        - Problem solving, Teamwork
        """

        self.sample_job_desc = """
        We are seeking a Senior Backend Developer.
        Required Qualifications:
        - 4+ years of Python and Flask experience
        - Strong background in MySQL and Redis
        - Experience with Docker, Kubernetes, and AWS
        - Excellent communication and problem solving skills
        """

    def test_extract_skills(self):
        skills_dict = matcher.extract_skills(self.sample_resume)
        flat = matcher.flatten_skills(skills_dict)
        self.assertIn("python", flat)
        self.assertIn("flask", flat)
        self.assertIn("mysql", flat)
        self.assertIn("docker", flat)
        self.assertIn("git", flat)

    def test_analyze_match_accuracy(self):
        res = matcher.analyze_resume_against_job(self.sample_resume, self.sample_job_desc)
        self.assertGreater(res['match_score'], 0)
        self.assertIn("python", res['matched_skills'])
        self.assertIn("flask", res['matched_skills'])
        self.assertIn("mysql", res['matched_skills'])
        self.assertIn("docker", res['matched_skills'])

        # Check identified missing skills
        self.assertIn("kubernetes", res['missing_skills'])
        self.assertIn("aws", res['missing_skills'])
        self.assertIn("redis", res['missing_skills'])

    def test_empty_job_description(self):
        res = matcher.analyze_resume_against_job(self.sample_resume, "")
        self.assertEqual(res['match_score'], 0.0)
        self.assertEqual(len(res['matched_skills']), 0)

    def test_candidate_name_extraction(self):
        name = matcher.extract_candidate_name(self.sample_resume)
        self.assertEqual(name, "John Doe")

    def test_recommendations_generation(self):
        res = matcher.analyze_resume_against_job(self.sample_resume, self.sample_job_desc)
        self.assertIsInstance(res['recommendations'], list)
        self.assertGreater(len(res['recommendations']), 0)


if __name__ == '__main__':
    unittest.main()

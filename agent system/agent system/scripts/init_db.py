"""
Initialize database and seed data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import sync_engine, Base, get_sync_db
from db.models import College, Course, TrustedDomain
from config.settings import settings


def init_database():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("Tables created successfully!")


def seed_trusted_domains():
    """Seed initial trusted domains."""
    domains = [
        ("uktech.ac.in", 1.5),
        ("uou.ac.in", 1.5),
        ("hnbgu.ac.in", 1.4),
        ("du.ac.in", 1.4),
        ("iitd.ac.in", 1.5),
        ("iitb.ac.in", 1.5),
        ("nptel.ac.in", 1.5),
        ("swayam.gov.in", 1.4),
    ]
    
    print("Seeding trusted domains...")
    with get_sync_db() as db:
        for domain, score in domains:
            existing = db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()
            if not existing:
                td = TrustedDomain(domain=domain, trust_score=score)
                db.add(td)
        db.commit()
    print("Trusted domains seeded!")


def seed_sample_colleges():
    """Seed sample colleges."""
    colleges = [
        ("Uttarakhand Technical University", "UTU", "uktech.ac.in"),
        ("Uttarakhand Open University", "UOU", "uou.ac.in"),
        ("Delhi University", "DU", "du.ac.in"),
    ]
    
    print("Seeding sample colleges...")
    with get_sync_db() as db:
        for name, short, domain in colleges:
            existing = db.query(College).filter(College.name == name).first()
            if not existing:
                college = College(name=name, short_name=short, domain=domain)
                db.add(college)
        db.commit()
    print("Colleges seeded!")


def seed_sample_courses():
    """Seed sample courses."""
    courses = [
        ("BCAT-001", "Introduction to Computer Science", 1),
        ("CAT-014", "Data Structures", 1),
        ("BBT DSC 101", "Biology Fundamentals", 2),
        ("CS-101", "Programming Basics", 1),
        ("MATH-201", "Advanced Mathematics", 1),
    ]
    
    print("Seeding sample courses...")
    with get_sync_db() as db:
        for code, name, college_id in courses:
            existing = db.query(Course).filter(Course.course_code == code).first()
            if not existing:
                course = Course(course_code=code, course_name=name, college_id=college_id)
                db.add(course)
        db.commit()
    print("Courses seeded!")


def main():
    print("=" * 50)
    print("Database Initialization (SQLite - No Docker)")
    print("=" * 50)
    print(f"Database: {settings.database_url}")
    print()
    
    init_database()
    seed_trusted_domains()
    seed_sample_colleges()
    seed_sample_courses()
    
    print("\n" + "=" * 50)
    print("Database initialization complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start API: uvicorn api.main:app --reload")
    print("2. Start dashboard: streamlit run dashboard/app.py")
    print("3. API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to reset the database with correct SQLite schema
"""
import os
from app import app, db
from models import User, Question, Answer

def reset_database():
    """Drop all tables and recreate with correct schema"""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create all tables with new schema
        db.create_all()
        print("Created all tables with new schema")
        
        # Create demo accounts
        create_demo_accounts()

def create_demo_accounts():
    """Create demo student and admin accounts"""
    # Create demo student account
    student = User()
    student.username = 'student'
    student.email = 'student@intellitutor.com'
    student.first_name = 'Demo'
    student.last_name = 'Student'
    student.role = 'student'
    student.set_password('student123')
    
    # Create demo admin account
    admin = User()
    admin.username = 'admin'
    admin.email = 'admin@intellitutor.com'
    admin.first_name = 'Demo'
    admin.last_name = 'Admin'
    admin.role = 'admin'
    admin.set_password('admin123')
    
    # Add sample questions to database from data_store
    from data_store import SAMPLE_QUESTIONS
    for q_data in SAMPLE_QUESTIONS:
        question = Question()
        question.subject = q_data['subject']
        question.topic = q_data['topic']
        question.question_text = q_data['question_text']
        question.model_answer = q_data['model_answer']
        question.difficulty = q_data['difficulty']
        db.session.add(question)
    
    # Add to database
    db.session.add(student)
    db.session.add(admin)
    db.session.commit()
    
    print("Demo accounts created successfully!")
    print("Student: username='student', password='student123'")
    print("Admin: username='admin', password='admin123'")
    print(f"Added {len(SAMPLE_QUESTIONS)} sample questions to database")

if __name__ == '__main__':
    reset_database()
#!/usr/bin/env python3
"""
Script to create demo accounts for IntelliTutor
"""
from app import app, db
from models import User

def create_demo_accounts():
    """Create demo student and admin accounts"""
    with app.app_context():
        # Check if accounts already exist
        if User.query.filter_by(username='student').first():
            print("Demo accounts already exist.")
            return
        
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
        
        # Add to database
        db.session.add(student)
        db.session.add(admin)
        db.session.commit()
        
        print("Demo accounts created successfully!")
        print("Student: username='student', password='student123'")
        print("Admin: username='admin', password='admin123'")

if __name__ == '__main__':
    create_demo_accounts()
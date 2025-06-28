from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from app import app, db
from auth import auth_bp, require_login, require_admin
from models import User, Question, Answer
from data_store import (
    get_random_question, 
    get_question_by_id, 
    mock_ai_score, 
    get_all_subjects, 
    get_topics_by_subject,
    get_questions_by_subject,
    SAMPLE_QUESTIONS
)
import random

# Register the auth blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page for logged out users, dashboard for logged in users"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('landing.html')

@app.route('/student/dashboard')
@require_login
def student_dashboard():
    """Student dashboard showing progress and start new question option"""
    user = current_user
    
    # Calculate progress metrics
    accuracy = 0
    if user.questions_attempted > 0:
        accuracy = round((user.questions_correct / user.questions_attempted) * 100, 1)
    
    # Calculate average score
    avg_score = 0
    if user.questions_attempted > 0:
        avg_score = round(user.total_score / user.questions_attempted, 1)
    
    # Check for new badges (every 5 correct answers)
    expected_badges = user.questions_correct // 5
    if expected_badges > user.badges:
        user.badges = expected_badges
        db.session.commit()
        flash(f'Congratulations! You earned a new badge for answering {user.questions_correct} questions correctly!', 'success')
    
    return render_template('student_dashboard.html', 
                         user=user, 
                         accuracy=accuracy, 
                         avg_score=avg_score)

@app.route('/student/question')
@require_login
def get_question():
    """Present a random question to the student"""
    question = get_random_question()
    session['current_question_id'] = question['id']
    return render_template('question.html', question=question)

@app.route('/student/submit', methods=['POST'])
@require_login
def submit_answer():
    """Process student's answer submission"""
    user_answer = request.form.get('answer', '').strip()
    question_id = session.get('current_question_id')
    
    if not user_answer:
        flash('Please provide an answer before submitting.', 'warning')
        return redirect(url_for('get_question'))
    
    if not question_id:
        flash('No question found. Please start a new question.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Get the question details
    question = get_question_by_id(question_id)
    if not question:
        flash('Question not found.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Get mock AI scoring
    scoring_result = mock_ai_score(user_answer, question['model_answer'], question['difficulty'])
    score = scoring_result['score']
    feedback = scoring_result['feedback']
    
    # Save answer to database
    answer = Answer()
    answer.user_id = current_user.id
    answer.question_id = question_id
    answer.user_answer = user_answer
    answer.score = score
    answer.feedback = feedback
    db.session.add(answer)
    
    # Update user statistics
    current_user.questions_attempted += 1
    current_user.total_score += score
    if score >= 70:  # Consider 70+ as correct
        current_user.questions_correct += 1
    
    db.session.commit()
    
    # Clear the session
    session.pop('current_question_id', None)
    
    return render_template('result.html', 
                         question=question,
                         user_answer=user_answer,
                         score=score,
                         feedback=feedback)

@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    """Admin dashboard for managing questions and viewing statistics"""
    
    # Get all subjects and their question counts
    subjects = get_all_subjects()
    subject_stats = {}
    for subject in subjects:
        questions = get_questions_by_subject(subject)
        subject_stats[subject] = {
            'count': len(questions),
            'topics': get_topics_by_subject(subject)
        }
    
    # Get recent answers for monitoring
    recent_answers = Answer.query.order_by(Answer.created_at.desc()).limit(10).all()
    
    # Get user statistics
    total_users = User.query.count()
    active_students = User.query.filter_by(role='student').filter(User.questions_attempted > 0).count()
    
    return render_template('admin_dashboard.html',
                         subjects=subjects,
                         subject_stats=subject_stats,
                         recent_answers=recent_answers,
                         total_users=total_users,
                         active_students=active_students,
                         sample_questions=SAMPLE_QUESTIONS)

@app.route('/admin/upload', methods=['POST'])
@require_admin
def upload_exam():
    """Mock PDF upload functionality (UI only)"""
    
    if 'exam_file' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    file = request.files['exam_file']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    if file and file.filename and file.filename.lower().endswith('.pdf'):
        # Mock processing - in a real system, this would process the PDF
        flash(f'Mock: PDF "{file.filename}" uploaded successfully! In a real system, this would be processed to extract questions.', 'success')
    else:
        flash('Please upload a PDF file only.', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/set_role/<user_id>/<role>')
@require_admin
def set_user_role(user_id, role):
    """Set a user's role (admin function)"""
    
    if role not in ['student', 'admin']:
        flash('Invalid role specified.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get(int(user_id))
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user.role = role
    db.session.commit()
    flash(f'User {user.first_name or user.username} role updated to {role}.', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('403.html'), 404

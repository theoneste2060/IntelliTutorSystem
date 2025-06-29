from flask import render_template, request, redirect, url_for, flash, session
import os
import json
import logging
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
    get_random_question_by_filters,
    SAMPLE_QUESTIONS
)
from exam_processor import exam_processor
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
    
    # Get available subjects for course selection
    subjects = get_all_subjects()
    
    return render_template('student_dashboard.html', 
                         user=user, 
                         accuracy=accuracy, 
                         avg_score=avg_score,
                         subjects=subjects)

@app.route('/student/question')
@require_login
def get_question():
    """Present a random question to the student"""
    # Get filter parameters from URL
    subject = request.args.get('subject')
    topic = request.args.get('topic')
    
    # Get filtered question or random if no filters
    if subject or topic:
        question = get_random_question_by_filters(subject, topic)
        if not question:
            flash(f'No questions found for the selected filters. Getting a random question instead.', 'info')
            question = get_random_question()
    else:
        question = get_random_question()
    
    session['current_question_id'] = question['id']
    return render_template('question.html', question=question, 
                         selected_subject=subject, selected_topic=topic)

@app.route('/api/topics/<subject>')
@require_login
def get_topics_for_subject(subject):
    """API endpoint to get topics for a specific subject"""
    from flask import jsonify
    topics = get_topics_by_subject(subject)
    return jsonify({'topics': topics})

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
    """Upload and process NESA exam PDF with NLP question extraction"""
    
    if 'exam_file' not in request.files:
        flash('No file selected for upload.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    file = request.files['exam_file']
    if file.filename == '':
        flash('No file selected for upload.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if not exam_processor.allowed_file(file.filename):
        flash('Please upload a PDF file only.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Save uploaded file
        filepath = exam_processor.save_uploaded_file(file)
        if not filepath:
            flash('Error saving uploaded file.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get exam metadata from form
        exam_metadata = {
            'course': request.form.get('course', 'General'),
            'level': request.form.get('level', 'Level 5'),
            'subject': request.form.get('subject', 'Construction')
        }
        
        # Process PDF and extract questions
        result = exam_processor.process_pdf(filepath, exam_metadata)
        
        if result['success']:
            # Store extracted questions in temporary file (avoid session size limits)
            import json
            import tempfile
            
            temp_data = {
                'questions': result['questions'],
                'metadata': result['metadata'],
                'user_id': current_user.id
            }
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp_extractions', exist_ok=True)
            
            # Save to temporary file with user ID
            temp_filename = f'temp_extractions/extraction_{current_user.id}.json'
            with open(temp_filename, 'w') as f:
                json.dump(temp_data, f)
            
            # Store just the filename in session
            session['extraction_file'] = temp_filename
            
            flash(f'Successfully extracted {result["total_extracted"]} questions from "{file.filename}". Review and edit below.', 'success')
            return redirect(url_for('review_extracted_questions'))
        else:
            flash(f'Error processing PDF: {result["error"]}', 'error')
            return redirect(url_for('admin_dashboard'))
            
    except Exception as e:
        flash(f'Error uploading exam: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/review-questions')
@require_admin
def review_extracted_questions():
    """Review and edit extracted questions before saving"""
    # Load questions from temporary file
    extraction_file = session.get('extraction_file')
    questions = []
    metadata = {}
    
    if extraction_file and os.path.exists(extraction_file):
        try:
            import json
            with open(extraction_file, 'r') as f:
                temp_data = json.load(f)
                if temp_data.get('user_id') == current_user.id:
                    questions = temp_data.get('questions', [])
                    metadata = temp_data.get('metadata', {})
        except Exception as e:
            logging.error(f"Error loading extraction file: {e}")
    
    if not questions:
        flash('No questions to review. Please upload an exam paper first.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_review_questions.html', 
                         questions=questions, 
                         metadata=metadata,
                         subjects=get_all_subjects())

@app.route('/admin/save-questions', methods=['POST'])
@require_admin
def save_extracted_questions():
    """Save selected and edited questions to database"""
    # Load questions from temporary file
    extraction_file = session.get('extraction_file')
    questions = []
    
    if extraction_file and os.path.exists(extraction_file):
        try:
            with open(extraction_file, 'r') as f:
                temp_data = json.load(f)
                if temp_data.get('user_id') == current_user.id:
                    questions = temp_data.get('questions', [])
        except Exception as e:
            logging.error(f"Error loading extraction file: {e}")
    
    if not questions:
        flash('No questions to save. Please upload an exam paper first.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Get admin selections and modifications
        admin_selections = {}
        
        for question in questions:
            question_id = question['id']
            
            # Check if question was selected
            if request.form.get(f'select_{question_id}'):
                admin_selections[question_id] = {
                    'text': request.form.get(f'text_{question_id}', question['text']),
                    'generated_answer': request.form.get(f'answer_{question_id}', question['generated_answer']),
                    'complexity': request.form.get(f'complexity_{question_id}', question['complexity']),
                    'course': request.form.get(f'course_{question_id}', question['course']),
                    'topic': request.form.get(f'topic_{question_id}', question['topic']),
                    'marks': int(request.form.get(f'marks_{question_id}', question['marks']))
                }
        
        # Save selected questions
        result = exam_processor.save_questions_to_database(questions, admin_selections)
        
        if result['success']:
            flash(f'{result["message"]}', 'success')
            # Clear temporary file and session data
            extraction_file = session.get('extraction_file')
            if extraction_file and os.path.exists(extraction_file):
                try:
                    os.remove(extraction_file)
                except Exception as e:
                    logging.error(f"Error removing temp file: {e}")
            
            session.pop('extraction_file', None)
        else:
            flash(f'Error saving questions: {result["error"]}', 'error')
        
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        flash(f'Error processing form data: {str(e)}', 'error')
        return redirect(url_for('review_extracted_questions'))

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

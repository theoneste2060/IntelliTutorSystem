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
import re
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Database query helper functions
def get_random_question_from_db():
    """Get a random question from database, fallback to sample if none"""
    questions = Question.query.all()
    if questions:
        question = random.choice(questions)
        return {
            'id': question.id,
            'subject': question.subject,
            'topic': question.topic,
            'question_text': question.question_text,
            'model_answer': question.model_answer,
            'difficulty': question.difficulty
        }
    else:
        # Fallback to sample questions if database is empty
        return get_random_question()

def get_all_subjects_from_db():
    """Get all unique subjects from database"""
    db_subjects = db.session.query(Question.subject).distinct().all()
    if db_subjects:
        subjects = [s[0] for s in db_subjects]
        return subjects
    else:
        return get_all_subjects()

def get_topics_by_subject_from_db(subject):
    """Get topics for a specific subject from database"""
    db_topics = Question.query.filter_by(subject=subject).with_entities(Question.topic).distinct().all()
    if db_topics:
        return [t[0] for t in db_topics]
    else:
        return get_topics_by_subject(subject)

def get_random_question_by_filters_from_db(subject=None, topic=None):
    """Get filtered random question from database"""
    query = Question.query
    
    if subject:
        query = query.filter_by(subject=subject)
    if topic:
        query = query.filter_by(topic=topic)
    
    questions = query.all()
    if questions:
        question = random.choice(questions)
        return {
            'id': question.id,
            'subject': question.subject,
            'topic': question.topic,
            'question_text': question.question_text,
            'model_answer': question.model_answer,
            'difficulty': question.difficulty
        }
    else:
        return get_random_question_by_filters(subject, topic)

def get_question_by_id_from_db(question_id):
    """Get specific question by ID from database"""
    question = Question.query.get(question_id)
    if question:
        return {
            'id': question.id,
            'subject': question.subject,
            'topic': question.topic,
            'question_text': question.question_text,
            'model_answer': question.model_answer,
            'difficulty': question.difficulty
        }
    else:
        return get_question_by_id(question_id)

def intelligent_ai_score(user_answer, model_answer, question_difficulty='medium'):
    """
    Intelligent AI scoring using NLP techniques to compare student and model answers
    """
    try:
        # Clean and normalize text
        user_clean = clean_text(user_answer)
        model_clean = clean_text(model_answer)
        
        if not user_clean or len(user_clean) < 5:
            return {
                'score': 0,
                'feedback': 'Answer is too short or empty. Please provide a more detailed response.'
            }
        
        # Calculate similarity score
        similarity_score = calculate_text_similarity(user_clean, model_clean)
        
        # Extract key concepts from both answers
        user_concepts = extract_key_concepts(user_clean)
        model_concepts = extract_key_concepts(model_clean)
        
        # Calculate concept coverage
        concept_coverage = calculate_concept_coverage(user_concepts, model_concepts)
        
        # Assess answer quality
        quality_score = assess_answer_quality(user_clean)
        
        # Calculate final score (weighted combination)
        final_score = int((similarity_score * 0.4 + concept_coverage * 0.4 + quality_score * 0.2) * 100)
        
        # Adjust for difficulty
        if question_difficulty == 'easy' and final_score >= 60:
            final_score = min(100, final_score + 5)
        elif question_difficulty == 'hard' and final_score < 80:
            final_score = max(50, final_score - 5)
        
        # Generate detailed feedback
        feedback = generate_detailed_feedback(user_answer, model_answer, final_score, 
                                           similarity_score, concept_coverage)
        
        return {
            'score': max(0, min(100, final_score)),
            'feedback': feedback
        }
        
    except Exception as e:
        logging.error(f"Error in intelligent scoring: {e}")
        # Fallback to mock scoring
        return mock_ai_score(user_answer, model_answer, question_difficulty)

def clean_text(text):
    """Clean and normalize text for comparison"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\:\;]', '', text)
    
    return text

def calculate_text_similarity(text1, text2):
    """Calculate semantic similarity between two texts using TF-IDF"""
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity
    except:
        # Fallback to simple word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0

def extract_key_concepts(text):
    """Extract key concepts from text using simple NLP techniques"""
    try:
        # Simple word-based concept extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 
                     'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'more',
                     'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also'}
        
        concepts = set()
        for word in words:
            if word not in stop_words and len(word) > 3:
                concepts.add(word)
        
        return concepts
    except:
        # Fallback to simple word extraction
        words = text.split()
        return set(word.lower() for word in words if len(word) > 3)

def calculate_concept_coverage(user_concepts, model_concepts):
    """Calculate how well user answer covers model answer concepts"""
    if not model_concepts:
        return 0.8  # Give benefit of doubt if no model concepts
    
    if not user_concepts:
        return 0.0
    
    # Count matches
    matches = 0
    for model_concept in model_concepts:
        for user_concept in user_concepts:
            # Check for exact match or partial match
            if model_concept == user_concept or model_concept in user_concept or user_concept in model_concept:
                matches += 1
                break
    
    coverage = matches / len(model_concepts)
    return min(1.0, coverage)  # Cap at 1.0

def assess_answer_quality(text):
    """Assess overall quality of the answer"""
    score = 0.5  # Base score
    
    # Length-based scoring
    word_count = len(text.split())
    if word_count >= 20:
        score += 0.2
    elif word_count >= 10:
        score += 0.1
    
    # Structure indicators
    if '.' in text or '!' in text or '?' in text:
        score += 0.1  # Has sentences
    
    if any(word in text.lower() for word in ['first', 'second', 'third', 'finally', 'therefore', 'because']):
        score += 0.1  # Has structure words
    
    # Technical indicators for construction topics
    construction_terms = ['construction', 'building', 'scaffold', 'brick', 'mortar', 'foundation', 
                         'safety', 'material', 'structure', 'tool', 'equipment']
    if any(term in text.lower() for term in construction_terms):
        score += 0.1  # Contains relevant terminology
    
    return min(1.0, score)

def generate_detailed_feedback(user_answer, model_answer, score, similarity, coverage):
    """Generate detailed feedback based on scoring components"""
    feedback_parts = []
    
    if score >= 85:
        feedback_parts.append("🎉 Excellent answer! You demonstrated strong understanding of the concepts.")
    elif score >= 70:
        feedback_parts.append("✅ Good answer! You covered most key points effectively.")
    elif score >= 55:
        feedback_parts.append("👍 Fair answer! You have the right idea but could provide more detail.")
    else:
        feedback_parts.append("📚 Your answer needs improvement. Let's work on understanding the key concepts.")
    
    # Similarity feedback
    if similarity < 0.3:
        feedback_parts.append("Consider reviewing the core concepts - your answer doesn't align closely with the expected response.")
    elif similarity < 0.6:
        feedback_parts.append("You're on the right track, but try to include more specific details from the lesson material.")
    
    # Coverage feedback
    if coverage < 0.4:
        feedback_parts.append("Try to address more of key points mentioned in the model answer.")
    elif coverage < 0.7:
        feedback_parts.append("You covered some important points. Consider expanding on the main concepts.")
    
    # Constructive suggestions
    model_length = len(model_answer.split())
    user_length = len(user_answer.split())
    
    if user_length < model_length * 0.3:
        feedback_parts.append("Your answer is quite brief. Try to provide more detailed explanations and examples.")
    
    return " ".join(feedback_parts)

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
    subjects = get_all_subjects_from_db()
    
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
        question = get_random_question_by_filters_from_db(subject, topic)
        if not question:
            flash(f'No questions found for the selected filters. Getting a random question instead.', 'info')
            question = get_random_question_from_db()
    else:
        question = get_random_question_from_db()
    
    session['current_question_id'] = question['id']
    return render_template('question.html', question=question, 
                         selected_subject=subject, selected_topic=topic)

@app.route('/api/topics/<subject>')
@require_login
def get_topics_for_subject(subject):
    """API endpoint to get topics for a specific subject"""
    from flask import jsonify
    topics = get_topics_by_subject_from_db(subject)
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
    question = get_question_by_id_from_db(question_id)
    if not question:
        flash('Question not found.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Get intelligent AI scoring
    scoring_result = intelligent_ai_score(user_answer, question['model_answer'], question['difficulty'])
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
    
    # Get all subjects and their question counts from database
    subjects = get_all_subjects_from_db()
    subject_stats = {}
    all_questions = []
    
    for subject in subjects:
        # Get questions from database for this subject
        db_questions = Question.query.filter_by(subject=subject).all()
        questions_data = []
        
        for q in db_questions:
            questions_data.append({
                'id': q.id,
                'subject': q.subject,
                'topic': q.topic,
                'question_text': q.question_text[:100] + '...' if len(q.question_text) > 100 else q.question_text,
                'full_question_text': q.question_text,
                'model_answer': q.model_answer,
                'difficulty': q.difficulty,
                'created_at': q.created_at.strftime('%Y-%m-%d') if q.created_at else 'Unknown'
            })
        
        all_questions.extend(questions_data)
        
        subject_stats[subject] = {
            'count': len(db_questions),
            'topics': get_topics_by_subject_from_db(subject),
            'questions': questions_data
        }
    
    # Get recent answers for monitoring
    recent_answers = Answer.query.order_by(Answer.created_at.desc()).limit(10).all()
    
    # Get user statistics
    total_users = User.query.count()
    active_students = User.query.filter_by(role='student').filter(User.questions_attempted > 0).count()
    total_questions = Question.query.count()
    
    return render_template('admin_dashboard.html',
                         subjects=subjects,
                         subject_stats=subject_stats,
                         recent_answers=recent_answers,
                         total_users=total_users,
                         active_students=active_students,
                         total_questions=total_questions,
                         all_questions=all_questions)

@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
@require_admin
def edit_question(question_id):
    """Edit a specific question"""
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        # Update question with form data
        question.subject = request.form.get('subject', question.subject)
        question.topic = request.form.get('topic', question.topic)
        question.question_text = request.form.get('question_text', question.question_text)
        question.model_answer = request.form.get('model_answer', question.model_answer)
        question.difficulty = request.form.get('difficulty', question.difficulty)
        
        try:
            db.session.commit()
            flash(f'Question #{question_id} has been updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating question: {str(e)}', 'error')
    
    return render_template('admin_edit_question.html', 
                         question=question, 
                         subjects=get_all_subjects_from_db())

@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
@require_admin
def delete_question(question_id):
    """Delete a specific question"""
    question = Question.query.get_or_404(question_id)
    
    try:
        # Delete associated answers first
        Answer.query.filter_by(question_id=question_id).delete()
        
        # Delete the question
        db.session.delete(question)
        db.session.commit()
        
        flash(f'Question #{question_id} has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

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

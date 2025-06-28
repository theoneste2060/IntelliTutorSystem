"""
Exam Processing Module for NESA Paper Management
Handles PDF upload, question extraction, and NLP answer generation
"""

import os
from werkzeug.utils import secure_filename
from flask import current_app
from pdf_processor import PDFQuestionExtractor
from models import Question, db
import json
import logging

logger = logging.getLogger(__name__)

class ExamProcessor:
    """Main processor for exam papers and question management"""
    
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'pdf'}
        self.pdf_extractor = PDFQuestionExtractor()
        
        # Create upload folder if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_uploaded_file(self, file):
        """Save uploaded PDF file securely"""
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)
            return filepath
        return None
    
    def process_pdf(self, filepath, exam_metadata=None):
        """Process uploaded PDF and extract questions with NLP answers"""
        try:
            # Extract text from PDF
            text = self.pdf_extractor.extract_text_from_pdf(filepath)
            if not text:
                raise ValueError("Could not extract text from PDF")
            
            # Extract questions with NLP-generated answers
            extracted_questions = self.pdf_extractor.extract_questions(text)
            
            # Process and enhance questions
            processed_questions = []
            for q in extracted_questions:
                processed_q = self._enhance_question(q, exam_metadata)
                processed_questions.append(processed_q)
            
            return {
                'success': True,
                'questions': processed_questions,
                'total_extracted': len(processed_questions),
                'metadata': {
                    'original_file': os.path.basename(filepath),
                    'text_length': len(text),
                    'extraction_method': 'NLP-enhanced'
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                'success': False,
                'error': str(e),
                'questions': []
            }
    
    def _enhance_question(self, question_data, exam_metadata=None):
        """Enhance extracted question with additional metadata"""
        enhanced = {
            'id': f"temp_{hash(question_data['text'])}",  # Temporary ID
            'number': question_data.get('number', ''),
            'text': question_data.get('text', ''),
            'generated_answer': question_data.get('generated_answer', ''),
            'complexity': question_data.get('complexity', 'medium'),
            'type': question_data.get('type', 'general'),
            'marks': question_data.get('marks', 3),
            'subject_keywords': question_data.get('subject', []),
            'course': exam_metadata.get('course', 'General') if exam_metadata else 'General',
            'level': exam_metadata.get('level', 'Level 5') if exam_metadata else 'Level 5',
            'topic': self._determine_topic(question_data),
            'is_selected': True,  # Admin can deselect questions they don't want
            'needs_review': self._needs_manual_review(question_data)
        }
        
        return enhanced
    
    def _determine_topic(self, question_data):
        """Determine topic based on question content and keywords"""
        keywords = question_data.get('subject', [])
        question_text = question_data.get('text', '').lower()
        
        # Topic mapping based on NESA curriculum
        topic_keywords = {
            'scaffolding': ['scaffold', 'scaffolding', 'platform', 'support structure'],
            'elevation': ['elevation', 'height', 'vertical', 'lifting'],
            'safety': ['safety', 'protection', 'hazard', 'risk', 'ppe'],
            'materials': ['brick', 'material', 'concrete', 'mortar', 'cement'],
            'tools': ['tool', 'equipment', 'instrument', 'device'],
            'construction': ['construction', 'building', 'structure', 'foundation'],
            'drawing': ['draw', 'sketch', 'diagram', 'plan', 'blueprint']
        }
        
        for topic, topic_words in topic_keywords.items():
            if any(word in question_text for word in topic_words) or \
               any(word in ' '.join(keywords) for word in topic_words):
                return topic.title()
        
        return 'General Construction'
    
    def _needs_manual_review(self, question_data):
        """Determine if question needs manual review"""
        text = question_data.get('text', '')
        
        # Questions that likely need review
        review_indicators = [
            len(text) < 20,  # Very short questions
            len(text) > 1000,  # Very long questions
            'draw' in text.lower() and 'diagram' in text.lower(),  # Drawing questions
            question_data.get('type') == 'calculation',  # Math problems
            question_data.get('complexity') == 'hard'  # Complex questions
        ]
        
        return any(review_indicators)
    
    def save_questions_to_database(self, questions, admin_selections=None):
        """Save selected and edited questions to database"""
        saved_count = 0
        
        try:
            for question_data in questions:
                # Check if admin selected this question
                question_id = question_data.get('id', '')
                if admin_selections and question_id not in admin_selections:
                    continue
                
                # Get admin modifications if any
                if admin_selections and question_id in admin_selections:
                    modifications = admin_selections[question_id]
                    question_data.update(modifications)
                
                # Create database entry
                question = Question()
                question.subject = question_data.get('course', 'General')
                question.topic = question_data.get('topic', 'General')
                question.question_text = question_data.get('text', '')
                question.model_answer = question_data.get('generated_answer', '')
                question.difficulty = question_data.get('complexity', 'medium')
                
                db.session.add(question)
                saved_count += 1
            
            db.session.commit()
            return {
                'success': True,
                'saved_count': saved_count,
                'message': f'Successfully saved {saved_count} questions to database'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving questions: {e}")
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0
            }
    
    def get_subject_statistics(self):
        """Get statistics about existing questions in database"""
        try:
            stats = {}
            
            # Count by subject
            subjects = db.session.query(Question.subject, db.func.count(Question.id)).\
                     group_by(Question.subject).all()
            
            for subject, count in subjects:
                stats[subject] = {
                    'total_questions': count,
                    'topics': {}
                }
                
                # Count by topic within subject
                topics = db.session.query(Question.topic, db.func.count(Question.id)).\
                        filter(Question.subject == subject).\
                        group_by(Question.topic).all()
                
                for topic, topic_count in topics:
                    stats[subject]['topics'][topic] = topic_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

# Initialize processor
exam_processor = ExamProcessor()
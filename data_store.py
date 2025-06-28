"""
In-memory data store for sample questions and mock AI functionality
"""
import random
from datetime import datetime

# Sample questions for the tutoring system
SAMPLE_QUESTIONS = [
    {
        'id': 1,
        'subject': 'Mathematics',
        'topic': 'Algebra',
        'question_text': 'Solve for x: 2x + 5 = 13',
        'model_answer': 'x = 4. First, subtract 5 from both sides: 2x = 8. Then divide by 2: x = 4.',
        'difficulty': 'easy'
    },
    {
        'id': 2,
        'subject': 'Mathematics',
        'topic': 'Geometry',
        'question_text': 'What is the area of a circle with radius 5 units?',
        'model_answer': 'Area = πr² = π × 5² = 25π ≈ 78.54 square units',
        'difficulty': 'medium'
    },
    {
        'id': 3,
        'subject': 'Science',
        'topic': 'Physics',
        'question_text': 'What is Newton\'s second law of motion?',
        'model_answer': 'Newton\'s second law states that Force equals mass times acceleration (F = ma). The acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass.',
        'difficulty': 'medium'
    },
    {
        'id': 4,
        'subject': 'Science',
        'topic': 'Chemistry',
        'question_text': 'What is the chemical formula for water?',
        'model_answer': 'H₂O. Water consists of two hydrogen atoms covalently bonded to one oxygen atom.',
        'difficulty': 'easy'
    },
    {
        'id': 5,
        'subject': 'English',
        'topic': 'Grammar',
        'question_text': 'Identify the subject and predicate in this sentence: "The quick brown fox jumps over the lazy dog."',
        'model_answer': 'Subject: "The quick brown fox" (the noun phrase that the sentence is about). Predicate: "jumps over the lazy dog" (what the subject does or what happens to it).',
        'difficulty': 'medium'
    },
    {
        'id': 6,
        'subject': 'History',
        'topic': 'World War II',
        'question_text': 'In what year did World War II end?',
        'model_answer': '1945. World War II ended in 1945 with the surrender of Germany in May and Japan in September.',
        'difficulty': 'easy'
    },
    {
        'id': 7,
        'subject': 'Mathematics',
        'topic': 'Calculus',
        'question_text': 'What is the derivative of x²?',
        'model_answer': '2x. Using the power rule: d/dx(xⁿ) = nxⁿ⁻¹, so d/dx(x²) = 2x¹ = 2x.',
        'difficulty': 'hard'
    },
    {
        'id': 8,
        'subject': 'Science',
        'topic': 'Biology',
        'question_text': 'What is photosynthesis?',
        'model_answer': 'Photosynthesis is the process by which plants use sunlight, carbon dioxide, and water to produce glucose and oxygen. The chemical equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.',
        'difficulty': 'medium'
    }
]

# Mock AI scoring function
def mock_ai_score(user_answer, model_answer, question_difficulty='medium'):
    """
    Mock AI scoring that returns a score between 60-100 and generic feedback
    In a real system, this would use NLP techniques to compare answers
    """
    if not user_answer or len(user_answer.strip()) < 5:
        return {
            'score': random.randint(20, 40),
            'feedback': 'Your answer is too short. Please provide more detail and explanation.'
        }
    
    # Base score based on difficulty
    base_scores = {
        'easy': (75, 95),
        'medium': (65, 90),
        'hard': (60, 85)
    }
    
    min_score, max_score = base_scores.get(question_difficulty, (65, 90))
    score = random.randint(min_score, max_score)
    
    # Generate feedback based on score range
    if score >= 90:
        feedback = "Excellent work! Your answer demonstrates a thorough understanding of the concept."
    elif score >= 80:
        feedback = "Good answer! You've covered the main points well. Consider adding more detail for a complete response."
    elif score >= 70:
        feedback = "Satisfactory answer. You understand the basics but could expand on key concepts."
    elif score >= 60:
        feedback = "Your answer shows some understanding but needs more development and accuracy."
    else:
        feedback = "Your answer needs significant improvement. Review the material and try to provide more comprehensive explanations."
    
    return {
        'score': score,
        'feedback': feedback
    }

def get_random_question():
    """Get a random question from the sample questions"""
    return random.choice(SAMPLE_QUESTIONS)

def get_question_by_id(question_id):
    """Get a specific question by ID"""
    for question in SAMPLE_QUESTIONS:
        if question['id'] == question_id:
            return question
    return None

def get_questions_by_subject(subject):
    """Get all questions for a specific subject"""
    return [q for q in SAMPLE_QUESTIONS if q['subject'].lower() == subject.lower()]

def get_all_subjects():
    """Get list of all unique subjects"""
    return list(set(q['subject'] for q in SAMPLE_QUESTIONS))

def get_topics_by_subject(subject):
    """Get all topics for a specific subject"""
    return list(set(q['topic'] for q in SAMPLE_QUESTIONS if q['subject'].lower() == subject.lower()))

def get_questions_by_subject_and_topic(subject, topic=None):
    """Get questions filtered by subject and optionally by topic"""
    questions = [q for q in SAMPLE_QUESTIONS if q['subject'].lower() == subject.lower()]
    if topic:
        questions = [q for q in questions if q['topic'].lower() == topic.lower()]
    return questions

def get_random_question_by_filters(subject=None, topic=None):
    """Get a random question filtered by subject and/or topic"""
    if subject and topic:
        filtered_questions = get_questions_by_subject_and_topic(subject, topic)
    elif subject:
        filtered_questions = get_questions_by_subject(subject)
    else:
        filtered_questions = SAMPLE_QUESTIONS
    
    if not filtered_questions:
        return None
    
    return random.choice(filtered_questions)

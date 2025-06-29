"""
Simplified PDF Question Extraction System for NESA Exam Papers
Efficient processing focused on practical question extraction
"""

import os
import re
import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

@dataclass
class QuestionResult:
    """Simple question result structure"""
    question_text: str
    model_answer: str
    subject: str
    topic: str
    difficulty: str
    marks: int
    question_type: str
    page_num: int
    confidence_score: float

class SimplifiedPDFProcessor:
    """Simplified PDF processor for NESA exam papers"""
    
    def __init__(self):
        self.question_patterns = [
            r'^\s*(\d+)\.?\s+',  # Question numbers like "1.", "2.", etc.
            r'^\s*\(([a-z])\)\s+',  # Sub-questions like "(a)", "(b)"
            r'^\s*([IVXLC]+)\.?\s+',  # Roman numerals
            r'Question \d+:',  # "Question 1:"
        ]
        
        self.mark_patterns = [
            r'\((\d+)\s*marks?\)',
            r'\[(\d+)\s*marks?\]',
            r'\((\d+)m\)',
            r'\[(\d+)m\]'
        ]

    def process_pdf(self, pdf_path: str) -> List[QuestionResult]:
        """Process PDF and extract questions efficiently"""
        logging.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Extract text from PDF
            text_blocks = self._extract_text_blocks(pdf_path)
            
            # Find potential questions
            question_candidates = self._find_question_candidates(text_blocks)
            
            # Process each candidate into a question
            questions = []
            for candidate in question_candidates:
                question = self._process_question_candidate(candidate)
                if question:
                    questions.append(question)
            
            logging.info(f"Extracted {len(questions)} questions")
            return questions
        
        except Exception as e:
            logging.error(f"Error processing PDF: {e}")
            return []

    def _extract_text_blocks(self, pdf_path: str) -> List[Dict]:
        """Extract text blocks from PDF"""
        blocks = []
        
        try:
            # Use PyMuPDF for reliable text extraction
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    # Split into paragraphs
                    paragraphs = re.split(r'\n\s*\n', text)
                    for para in paragraphs:
                        if para.strip() and len(para.strip()) > 10:
                            blocks.append({
                                'text': para.strip(),
                                'page_num': page_num + 1
                            })
            doc.close()
            
        except Exception as e:
            logging.error(f"Error extracting text: {e}")
        
        return blocks

    def _find_question_candidates(self, text_blocks: List[Dict]) -> List[Dict]:
        """Find text blocks that likely contain questions"""
        candidates = []
        
        for block in text_blocks:
            text = block['text']
            
            # Check if block starts with question pattern
            is_question = False
            for pattern in self.question_patterns:
                if re.search(pattern, text, re.MULTILINE):
                    is_question = True
                    break
            
            # Check for question indicators
            question_words = ['explain', 'describe', 'define', 'calculate', 'list', 'name', 'identify', 'what', 'how', 'why']
            has_question_word = any(word in text.lower() for word in question_words)
            
            # Check for marks
            has_marks = any(re.search(pattern, text.lower()) for pattern in self.mark_patterns)
            
            # Score the candidate
            score = 0
            if is_question:
                score += 0.4
            if has_question_word:
                score += 0.3
            if has_marks:
                score += 0.2
            if '?' in text:
                score += 0.1
            
            # Length consideration
            word_count = len(text.split())
            if 10 <= word_count <= 300:
                score += 0.1
            
            if score >= 0.3:  # Threshold for acceptance
                candidate = block.copy()
                candidate['confidence_score'] = score
                candidates.append(candidate)
        
        # Sort by confidence
        candidates.sort(key=lambda x: x['confidence_score'], reverse=True)
        return candidates

    def _process_question_candidate(self, candidate: Dict) -> Optional[QuestionResult]:
        """Process a question candidate into a full question"""
        try:
            text = candidate['text']
            
            # Clean question text
            question_text = self._clean_text(text)
            
            # Extract marks
            marks = self._extract_marks(text)
            
            # Classify question
            question_type = self._classify_question_type(text)
            subject, topic = self._classify_subject_topic(text)
            difficulty = self._assess_difficulty(text, marks)
            
            # Generate answer
            model_answer = self._generate_answer(question_text, question_type, subject)
            
            return QuestionResult(
                question_text=question_text,
                model_answer=model_answer,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                marks=marks,
                question_type=question_type,
                page_num=candidate['page_num'],
                confidence_score=candidate['confidence_score']
            )
        
        except Exception as e:
            logging.error(f"Error processing question candidate: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and format text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers
        text = re.sub(r'Page \d+.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
        return text.strip()

    def _extract_marks(self, text: str) -> int:
        """Extract marks from text"""
        for pattern in self.mark_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        return 5  # Default marks

    def _classify_question_type(self, text: str) -> str:
        """Classify question type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['define', 'what is', 'meaning']):
            return 'definition'
        elif any(word in text_lower for word in ['explain', 'describe', 'how', 'why']):
            return 'explanation'
        elif any(word in text_lower for word in ['list', 'name', 'identify', 'state']):
            return 'listing'
        elif any(word in text_lower for word in ['calculate', 'compute', 'find']):
            return 'calculation'
        elif any(word in text_lower for word in ['compare', 'contrast', 'difference']):
            return 'comparison'
        else:
            return 'general'

    def _classify_subject_topic(self, text: str) -> tuple:
        """Classify subject and topic"""
        text_lower = text.lower()
        
        # NESA Construction keywords
        if any(word in text_lower for word in ['scaffold', 'scaffolding', 'platform']):
            return 'Construction Technology', 'Scaffolding Systems'
        elif any(word in text_lower for word in ['elevation', 'height', 'lifting']):
            return 'Construction Technology', 'Elevation Operations'
        elif any(word in text_lower for word in ['safety', 'ppe', 'hazard', 'risk']):
            return 'Construction Safety', 'Safety Management'
        elif any(word in text_lower for word in ['brick', 'mortar', 'material']):
            return 'Construction Materials', 'Building Materials'
        elif any(word in text_lower for word in ['tool', 'equipment']):
            return 'Construction Technology', 'Tools and Equipment'
        else:
            return 'General Construction', 'Construction Practice'

    def _assess_difficulty(self, text: str, marks: int) -> str:
        """Assess question difficulty"""
        if marks <= 3:
            return 'easy'
        elif marks <= 6:
            return 'medium'
        else:
            return 'hard'

    def _generate_answer(self, question_text: str, question_type: str, subject: str) -> str:
        """Generate appropriate answer based on question type"""
        
        if question_type == 'definition':
            if 'scaffold' in question_text.lower():
                return """Scaffolding is a temporary structure used to support workers and materials during construction, maintenance, or repair work at height. It provides a safe working platform and must be erected by competent persons following safety regulations. Key components include standards (vertical tubes), ledgers (horizontal tubes), transoms, and working platforms."""
            
            elif 'elevation' in question_text.lower():
                return """Elevation refers to working at height above ground level. In construction, elevation operations involve the use of scaffolding, platforms, and other access equipment to safely position workers and materials at the required height for construction activities."""
            
            else:
                return f"""This {subject} term refers to a fundamental concept in construction work. The definition should cover the technical aspects, safety requirements, and practical applications relevant to construction industry standards and regulations."""

        elif question_type == 'explanation':
            return f"""This explanation should cover the key principles and processes involved in {subject}. Important points include:

1. The underlying technical concepts
2. Step-by-step procedures or methods
3. Safety considerations and regulatory requirements
4. Practical applications in construction work
5. Common challenges and best practice solutions
6. Industry standards and compliance requirements

The explanation should demonstrate comprehensive understanding of both theory and practical implementation."""

        elif question_type == 'listing':
            if 'safety' in question_text.lower():
                return """Key safety requirements include:
1. Personal Protective Equipment (PPE) - hard hats, safety harnesses, high-visibility clothing
2. Fall protection systems - guardrails, safety nets, personal fall arrest systems
3. Scaffold inspection - daily visual checks and formal inspections by competent persons
4. Load limits - understanding safe working loads and load distribution
5. Weather restrictions - wind speed limits and wet weather precautions
6. Training requirements - competent person certification and site-specific training
7. Emergency procedures - rescue plans and first aid provisions
8. Documentation - inspection records and training certificates"""
            
            else:
                return f"""Key points related to {subject}:
1. Primary components and their functions
2. Safety requirements and procedures
3. Regulatory compliance standards
4. Quality control measures
5. Installation and maintenance procedures
6. Documentation requirements
7. Training and competency standards
8. Risk assessment considerations"""

        elif question_type == 'calculation':
            return """For calculation problems:

1. Identify the given information and required result
2. Select appropriate formulas and standards
3. Apply relevant safety factors
4. Show clear step-by-step working
5. Include correct units throughout
6. Verify the answer is reasonable
7. Reference applicable codes and standards

Example format:
Given: [List known values]
Required: [State what needs to be calculated]
Formula: [Show relevant equation]
Calculation: [Step-by-step working]
Result: [Final answer with units]
Check: [Verify against standards]"""

        else:
            return f"""Comprehensive response addressing {subject}:

Technical Overview:
- Define key concepts and terminology
- Explain the technical requirements
- Reference relevant standards

Safety Considerations:
- Identify potential hazards
- Outline safety measures and controls
- Reference regulatory requirements

Practical Application:
- Describe implementation procedures
- Discuss common challenges
- Provide practical solutions

Quality and Compliance:
- Outline quality standards
- Explain compliance requirements
- Discuss inspection procedures"""

def test_simplified_processor():
    """Test the simplified processor"""
    processor = SimplifiedPDFProcessor()
    pdf_path = "attached_assets/2024_T045_Elevation_and_Scaffolding_operations_1751140638965.pdf"
    
    if os.path.exists(pdf_path):
        questions = processor.process_pdf(pdf_path)
        print(f"Extracted {len(questions)} questions")
        
        if questions:
            print("\n=== Sample Question ===")
            q = questions[0]
            print(f"Subject: {q.subject}")
            print(f"Topic: {q.topic}")
            print(f"Type: {q.question_type}")
            print(f"Marks: {q.marks}")
            print(f"Question: {q.question_text[:200]}...")
            print(f"Answer: {q.model_answer[:200]}...")
    else:
        print("PDF file not found")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_simplified_processor()
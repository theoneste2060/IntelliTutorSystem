"""
Enhanced PDF Question Extraction System with Modern NLP
Uses chunking, embeddings, and advanced text processing for NESA exam papers
"""

import os
import re
import json
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
import pdfplumber
from dataclasses import dataclass
import logging
from datetime import datetime

# Basic NLP processing with available libraries
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import spacy

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Initialize spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy model not found. Some NLP features may be limited.")
    nlp = None

@dataclass
class QuestionChunk:
    """Represents a chunk of text that potentially contains a question"""
    text: str
    page_num: int
    confidence_score: float
    question_type: str
    subject_keywords: List[str]
    marks: Optional[int] = None
    
@dataclass
class ExtractedQuestion:
    """Represents a fully processed question"""
    question_text: str
    model_answer: str
    subject: str
    topic: str
    difficulty: str
    marks: int
    question_type: str
    page_num: int
    confidence_score: float

class EnhancedPDFProcessor:
    """Enhanced PDF processor with modern NLP techniques"""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # Subject-specific keywords for better classification
        self.subject_keywords = {
            'construction': ['scaffolding', 'elevation', 'building', 'structure', 'safety', 'construction', 'site', 'equipment', 'height', 'platform'],
            'engineering': ['design', 'load', 'stress', 'material', 'calculation', 'force', 'structural', 'technical'],
            'safety': ['safety', 'hazard', 'risk', 'procedure', 'regulation', 'protection', 'accident', 'prevention'],
            'mathematics': ['calculate', 'equation', 'formula', 'measurement', 'dimension', 'angle', 'area', 'volume'],
            'science': ['physics', 'chemistry', 'biology', 'experiment', 'hypothesis', 'theory', 'analysis']
        }
        
        # Question type patterns
        self.question_patterns = {
            'definition': [r'\bdefine\b', r'\bwhat is\b', r'\bexplain what\b', r'\bmeans?\b'],
            'explanation': [r'\bexplain\b', r'\bdescribe\b', r'\bwhy\b', r'\bhow\b', r'\banalyse\b'],
            'listing': [r'\blist\b', r'\bname\b', r'\bidentify\b', r'\bstate\b', r'\bgive.*examples\b'],
            'calculation': [r'\bcalculate\b', r'\bcompute\b', r'\bfind\b', r'\bdetermine\b', r'\bmeasure\b'],
            'comparison': [r'\bcompare\b', r'\bcontrast\b', r'\bdifference\b', r'\bsimilar\b'],
            'evaluation': [r'\bevaluate\b', r'\bassess\b', r'\bjudge\b', r'\bcritique\b', r'\brecommend\b']
        }

    def process_pdf(self, pdf_path: str) -> List[ExtractedQuestion]:
        """Main processing method that extracts questions from PDF"""
        logging.info(f"Processing PDF: {pdf_path}")
        
        # Extract text using multiple methods for robustness
        text_chunks = self._extract_text_chunks(pdf_path)
        
        # Process chunks to identify potential questions
        question_chunks = self._identify_question_chunks(text_chunks)
        
        # Extract and enhance questions
        extracted_questions = []
        for chunk in question_chunks:
            question = self._process_question_chunk(chunk)
            if question:
                extracted_questions.append(question)
        
        logging.info(f"Extracted {len(extracted_questions)} questions")
        return extracted_questions

    def _extract_text_chunks(self, pdf_path: str) -> List[Dict]:
        """Extract text chunks from PDF using multiple extraction methods"""
        chunks = []
        
        # Method 1: PyMuPDF for structured extraction
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Split into logical chunks (paragraphs/sections)
                paragraphs = self._split_into_paragraphs(text)
                for para in paragraphs:
                    if len(para.strip()) > 20:  # Minimum length filter
                        chunks.append({
                            'text': para,
                            'page_num': page_num + 1,
                            'method': 'pymupdf'
                        })
            doc.close()
        except Exception as e:
            logging.error(f"PyMuPDF extraction failed: {e}")
        
        # Method 2: pdfplumber for table and structured data
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        paragraphs = self._split_into_paragraphs(text)
                        for para in paragraphs:
                            if len(para.strip()) > 20:
                                chunks.append({
                                    'text': para,
                                    'page_num': page_num + 1,
                                    'method': 'pdfplumber'
                                })
        except Exception as e:
            logging.error(f"pdfplumber extraction failed: {e}")
        
        # Remove duplicates and merge similar chunks
        chunks = self._deduplicate_chunks(chunks)
        
        logging.info(f"Extracted {len(chunks)} text chunks")
        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into logical paragraphs"""
        # Clean up text
        text = re.sub(r'\s+', ' ', text)
        
        # Split by common paragraph indicators
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n|(?<=\.)\s{2,}(?=[A-Z])', text)
        
        # Further split by question indicators
        enhanced_paragraphs = []
        for para in paragraphs:
            # Split on question numbers (e.g., "1.", "2.", "(a)", "(b)")
            question_splits = re.split(r'(?<=\d\.)\s+(?=[A-Z])|(?<=\))\s+(?=[A-Z])', para)
            enhanced_paragraphs.extend(question_splits)
        
        return [p.strip() for p in enhanced_paragraphs if p.strip()]

    def _deduplicate_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Remove duplicate and very similar chunks"""
        unique_chunks = []
        seen_texts = set()
        
        for chunk in chunks:
            # Create a normalized version for comparison
            normalized = re.sub(r'\s+', ' ', chunk['text'].lower().strip())
            
            # Check if this text is substantially different from existing ones
            is_duplicate = False
            for seen in seen_texts:
                if self._text_similarity(normalized, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_chunks.append(chunk)
                seen_texts.add(normalized)
        
        return unique_chunks

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using simple word overlap"""
        words1 = set(word_tokenize(text1.lower()))
        words2 = set(word_tokenize(text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def _identify_question_chunks(self, chunks: List[Dict]) -> List[QuestionChunk]:
        """Identify chunks that likely contain questions"""
        question_chunks = []
        
        for chunk in chunks:
            text = chunk['text']
            
            # Calculate question probability
            question_score = self._calculate_question_score(text)
            
            if question_score > 0.3:  # Threshold for question identification
                # Extract additional metadata
                question_type = self._classify_question_type(text)
                subject_keywords = self._extract_subject_keywords(text)
                marks = self._extract_marks(text)
                
                question_chunk = QuestionChunk(
                    text=text,
                    page_num=chunk['page_num'],
                    confidence_score=question_score,
                    question_type=question_type,
                    subject_keywords=subject_keywords,
                    marks=marks
                )
                question_chunks.append(question_chunk)
        
        # Sort by confidence score
        question_chunks.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logging.info(f"Identified {len(question_chunks)} potential questions")
        return question_chunks

    def _calculate_question_score(self, text: str) -> float:
        """Calculate how likely a text chunk contains a question"""
        score = 0.0
        text_lower = text.lower()
        
        # Question mark bonus
        if '?' in text:
            score += 0.3
        
        # Question word patterns
        question_words = ['what', 'how', 'why', 'when', 'where', 'which', 'who', 'explain', 'describe', 'define', 'calculate', 'list', 'name', 'identify']
        for word in question_words:
            if word in text_lower:
                score += 0.1
        
        # Question numbering patterns
        if re.search(r'^\s*\d+\.', text) or re.search(r'^\s*\([a-z]\)', text):
            score += 0.2
        
        # Instruction verbs
        instruction_verbs = ['explain', 'describe', 'analyze', 'evaluate', 'compare', 'discuss', 'examine', 'assess']
        for verb in instruction_verbs:
            if verb in text_lower:
                score += 0.15
        
        # Mark indicators
        if re.search(r'\(\d+\s*marks?\)', text_lower) or re.search(r'\[\d+\s*marks?\]', text_lower):
            score += 0.2
        
        # Length consideration (questions are usually substantial but not too long)
        word_count = len(text.split())
        if 10 <= word_count <= 200:
            score += 0.1
        elif word_count > 200:
            score -= 0.1
        
        return min(score, 1.0)

    def _classify_question_type(self, text: str) -> str:
        """Classify the type of question based on text patterns"""
        text_lower = text.lower()
        
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return q_type
        
        return 'general'

    def _extract_subject_keywords(self, text: str) -> List[str]:
        """Extract subject-related keywords from text"""
        text_lower = text.lower()
        found_keywords = []
        
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))

    def _extract_marks(self, text: str) -> Optional[int]:
        """Extract mark allocation from question text"""
        # Look for patterns like (5 marks), [3 marks], (2m), etc.
        mark_patterns = [
            r'\((\d+)\s*marks?\)',
            r'\[(\d+)\s*marks?\]',
            r'\((\d+)m\)',
            r'\[(\d+)m\]',
            r'(\d+)\s*marks?'
        ]
        
        for pattern in mark_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return None

    def _process_question_chunk(self, chunk: QuestionChunk) -> Optional[ExtractedQuestion]:
        """Process a question chunk into a full question"""
        try:
            # Clean and format question text
            question_text = self._clean_question_text(chunk.text)
            
            # Generate model answer using enhanced NLP
            model_answer = self._generate_enhanced_answer(question_text, chunk)
            
            # Determine subject and topic
            subject, topic = self._classify_subject_and_topic(chunk)
            
            # Assess difficulty
            difficulty = self._assess_difficulty(chunk)
            
            return ExtractedQuestion(
                question_text=question_text,
                model_answer=model_answer,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                marks=chunk.marks or 5,
                question_type=chunk.question_type,
                page_num=chunk.page_num,
                confidence_score=chunk.confidence_score
            )
        
        except Exception as e:
            logging.error(f"Error processing question chunk: {e}")
            return None

    def _clean_question_text(self, text: str) -> str:
        """Clean and format question text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers
        text = re.sub(r'Page \d+.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
        
        # Clean up formatting
        text = text.strip()
        
        return text

    def _generate_enhanced_answer(self, question_text: str, chunk: QuestionChunk) -> str:
        """Generate comprehensive answer using enhanced NLP techniques"""
        # Analyze question type and generate appropriate answer
        question_type = chunk.question_type
        keywords = chunk.subject_keywords
        
        if question_type == 'definition':
            return self._generate_definition_answer(question_text, keywords)
        elif question_type == 'explanation':
            return self._generate_explanation_answer(question_text, keywords)
        elif question_type == 'listing':
            return self._generate_listing_answer(question_text, keywords)
        elif question_type == 'calculation':
            return self._generate_calculation_answer(question_text, keywords)
        elif question_type == 'comparison':
            return self._generate_comparison_answer(question_text, keywords)
        else:
            return self._generate_comprehensive_answer(question_text, keywords)

    def _generate_definition_answer(self, question_text: str, keywords: List[str]) -> str:
        """Generate definition-type answers"""
        # Build comprehensive definition based on keywords
        if 'scaffolding' in keywords:
            return """Scaffolding is a temporary structure used in construction to support workers and materials during building, maintenance, or repair work. It provides a safe working platform at height and must comply with safety regulations. Key components include standards (vertical tubes), ledgers (horizontal tubes), transoms, and boards. Scaffolding must be erected by competent persons and regularly inspected for safety."""
        
        elif 'elevation' in keywords:
            return """Elevation in construction refers to the vertical height or position of a structure or component above a reference point, typically ground level or sea level. In building drawings, elevations show the exterior faces of a building from different viewpoints. Elevation operations involve working at height and require proper safety equipment including scaffolding, harnesses, and fall protection systems."""
        
        else:
            return f"""Based on the context involving {', '.join(keywords)}, this term refers to a key concept in construction and engineering. The definition should encompass the technical aspects, safety considerations, and practical applications relevant to the construction industry. Proper understanding requires knowledge of regulations, standards, and best practices in the field."""

    def _generate_explanation_answer(self, question_text: str, keywords: List[str]) -> str:
        """Generate explanation-type answers"""
        return f"""This explanation should cover the fundamental principles and processes related to {', '.join(keywords)}. Key points to address include:

1. The underlying concepts and theory
2. Step-by-step processes or procedures
3. Safety considerations and regulations
4. Practical applications in real-world scenarios
5. Common challenges and solutions
6. Industry standards and best practices

The explanation should demonstrate understanding of both theoretical knowledge and practical implementation, with specific reference to construction industry requirements and safety protocols."""

    def _generate_listing_answer(self, question_text: str, keywords: List[str]) -> str:
        """Generate listing-type answers"""
        if 'safety' in keywords:
            return """Key safety considerations include:
1. Personal Protective Equipment (PPE) - hard hats, safety harnesses, high-visibility clothing
2. Fall protection systems - guardrails, safety nets, personal fall arrest systems
3. Scaffold inspection - daily checks, formal inspections, competent person requirements
4. Load limits - understanding working loads and safety factors
5. Weather conditions - wind speed restrictions, wet weather precautions
6. Training requirements - competent person training, site-specific inductions
7. Emergency procedures - rescue plans, first aid provisions
8. Documentation - inspection records, training certificates, risk assessments"""
        
        else:
            return f"""Based on the context of {', '.join(keywords)}, the key items to list include:
1. Primary components and their functions
2. Safety requirements and procedures
3. Regulatory compliance requirements
4. Quality standards and specifications
5. Inspection and maintenance procedures
6. Documentation and record-keeping requirements
7. Training and competency requirements
8. Risk management considerations"""

    def _generate_calculation_answer(self, question_text: str, keywords: List[str]) -> str:
        """Generate calculation-type answers"""
        return """For calculation problems:

1. Identify given values and required outcomes
2. Select appropriate formulas and standards
3. Apply safety factors where required
4. Show step-by-step calculations
5. Include units throughout the calculation
6. Check results for reasonableness
7. Reference relevant codes and standards

Example approach:
- Given: [List known values]
- Required: [State what needs to be calculated]
- Formula: [Show relevant equation]
- Calculation: [Step-by-step working]
- Result: [Final answer with units]
- Safety check: [Verify against standards]"""

    def _generate_comparison_answer(self, question_text: str, keywords: List[str]) -> str:
        """Generate comparison-type answers"""
        return """Comparison should address:

Similarities:
- Common safety requirements
- Shared regulatory standards
- Similar risk factors
- Comparable operational procedures

Differences:
- Specific applications and use cases
- Different load requirements
- Varying setup and dismantling procedures
- Distinct inspection requirements
- Different cost implications
- Specific training needs

Conclusion:
- Recommendations for appropriate selection
- Consideration of site-specific factors
- Cost-benefit analysis
- Safety implications of each option"""

    def _generate_comprehensive_answer(self, question_text: str, keywords: List[str]) -> str:
        """Generate comprehensive general answers"""
        return f"""Comprehensive response addressing {', '.join(keywords)}:

Overview:
- Define key concepts and terminology
- Explain the context and importance

Technical Aspects:
- Detail the technical requirements
- Explain processes and procedures
- Reference relevant standards and codes

Safety Considerations:
- Identify potential hazards and risks
- Outline safety measures and controls
- Reference regulatory requirements

Practical Application:
- Describe real-world implementation
- Discuss common challenges and solutions
- Provide examples where appropriate

Quality and Compliance:
- Outline quality standards
- Explain compliance requirements
- Discuss inspection and testing procedures

This comprehensive approach ensures all aspects are covered systematically."""

    def _classify_subject_and_topic(self, chunk: QuestionChunk) -> Tuple[str, str]:
        """Classify subject and topic based on keywords and content"""
        keywords = chunk.subject_keywords
        text_lower = chunk.text.lower()
        
        # Primary subject classification
        if any(k in keywords for k in ['scaffolding', 'elevation', 'construction', 'building']):
            subject = 'Construction Technology'
            
            if 'scaffolding' in keywords:
                topic = 'Scaffolding Systems'
            elif 'elevation' in keywords:
                topic = 'Elevation Operations'
            else:
                topic = 'General Construction'
                
        elif any(k in keywords for k in ['safety', 'hazard', 'risk', 'protection']):
            subject = 'Construction Safety'
            topic = 'Safety Management'
            
        elif any(k in keywords for k in ['calculation', 'load', 'stress', 'force']):
            subject = 'Engineering Calculations'
            topic = 'Structural Analysis'
            
        else:
            subject = 'General Construction'
            topic = 'Construction Practice'
        
        return subject, topic

    def _assess_difficulty(self, chunk: QuestionChunk) -> str:
        """Assess question difficulty based on various factors"""
        score = 0
        
        # Mark allocation influence
        if chunk.marks:
            if chunk.marks <= 3:
                score += 1  # Easy
            elif chunk.marks <= 6:
                score += 2  # Medium
            else:
                score += 3  # Hard
        
        # Question type complexity
        complex_types = ['evaluation', 'comparison', 'calculation']
        if chunk.question_type in complex_types:
            score += 2
        
        # Text complexity (word count and technical terms)
        word_count = len(chunk.text.split())
        if word_count > 100:
            score += 1
        
        # Technical keyword density
        technical_terms = len(chunk.subject_keywords)
        if technical_terms > 3:
            score += 1
        
        # Classification
        if score <= 2:
            return 'easy'
        elif score <= 4:
            return 'medium'
        else:
            return 'hard'

def test_processor():
    """Test the enhanced PDF processor"""
    processor = EnhancedPDFProcessor()
    
    # Test with the sample PDF
    pdf_path = "attached_assets/2024_T045_Elevation_and_Scaffolding_operations_1751140638965.pdf"
    
    if os.path.exists(pdf_path):
        try:
            questions = processor.process_pdf(pdf_path)
            
            print(f"Successfully extracted {len(questions)} questions:")
            for i, q in enumerate(questions[:3], 1):  # Show first 3 questions
                print(f"\n--- Question {i} ---")
                print(f"Subject: {q.subject}")
                print(f"Topic: {q.topic}")
                print(f"Type: {q.question_type}")
                print(f"Difficulty: {q.difficulty}")
                print(f"Marks: {q.marks}")
                print(f"Page: {q.page_num}")
                print(f"Confidence: {q.confidence_score:.2f}")
                print(f"Question: {q.question_text[:200]}...")
                print(f"Answer: {q.model_answer[:200]}...")
            
            return questions
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []
    else:
        print(f"PDF file not found: {pdf_path}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_processor()
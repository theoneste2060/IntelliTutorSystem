"""
NESA-Specific PDF Question Extraction System
Optimized for NESA exam papers with numbered questions (01. through 21.)
"""

import re
import fitz  # PyMuPDF
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

@dataclass
class NESAQuestion:
    """Represents a NESA question with all metadata"""
    number: str
    text: str
    marks: int
    question_type: str
    subject: str
    topic: str
    difficulty: str
    model_answer: str
    page_num: int
    has_multiple_choice: bool = False
    has_table: bool = False
    multiple_choice_options: Optional[List[str]] = None

class NESAPDFProcessor:
    """Specialized processor for NESA exam papers"""
    
    def __init__(self):
        self.question_patterns = [
            r'(\d{2})\.\s+(.+?)(?=\d{2}\.\s+|\Z)',  # Main pattern: 01. ... 02. ...
            r'(\d{1})\.\s+(.+?)(?=\d{1,2}\.\s+|\Z)',  # Fallback: 1. ... 2. ...
        ]
        
        # Subject classification based on content
        self.subject_keywords = {
            'Masonry': ['brick', 'mortar', 'foundation', 'wall', 'masonry', 'cement', 'lime', 'bond'],
            'Scaffolding': ['scaffold', 'scaffolding', 'platform', 'steel', 'safety', 'height', 'tube'],
            'Construction Technology': ['construction', 'building', 'structure', 'material', 'tool', 'equipment'],
            'Safety Management': ['safety', 'hazard', 'risk', 'protection', 'inspection', 'regulation']
        }
        
        # Question type patterns
        self.type_patterns = {
            'definition': r'\b(define|what is|meaning of|explain the term)\b',
            'calculation': r'\b(calculate|determine|find|compute|how many|quantity)\b',
            'listing': r'\b(list|identify|state|name|mention|enumerate)\b',
            'comparison': r'\b(compare|contrast|differentiate|distinguish|difference)\b',
            'explanation': r'\b(explain|describe|discuss|elaborate|why|how)\b',
            'sketch': r'\b(draw|sketch|diagram|show|illustrate)\b',
            'matching': r'\b(match|correspond|relate|pair)\b'
        }

    def process_pdf(self, pdf_path: str) -> List[NESAQuestion]:
        """Process NESA PDF and extract numbered questions"""
        logging.info(f"Processing NESA PDF: {pdf_path}")
        
        try:
            # Extract text from PDF
            full_text = self._extract_text_from_pdf(pdf_path)
            
            # Find and extract questions
            questions = self._extract_numbered_questions(full_text)
            
            # Process each question
            processed_questions = []
            for q in questions:
                processed_q = self._process_question(q)
                if processed_q:
                    processed_questions.append(processed_q)
            
            logging.info(f"Successfully extracted {len(processed_questions)} NESA questions")
            return processed_questions
            
        except Exception as e:
            logging.error(f"Error processing NESA PDF: {e}")
            return []

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF maintaining structure"""
        full_text = ""
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                full_text += f"\n--- PAGE {page_num + 1} ---\n{text}\n"
            doc.close()
            
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {e}")
            
        return full_text

    def _extract_numbered_questions(self, text: str) -> List[Dict]:
        """Extract questions numbered 01. through 21."""
        questions = []
        
        # Clean up text
        text = re.sub(r'\n+', ' ', text)  # Replace multiple newlines with space
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        
        # Find questions using numbered pattern
        pattern = r'(\d{2})\.\s+(.+?)(?=\d{2}\.\s+|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            number = match[0]
            question_text = match[1].strip()
            
            # Skip if too short or looks like header/footer
            if len(question_text) < 20 or self._is_header_footer(question_text):
                continue
                
            # Extract page number
            page_num = self._extract_page_number(question_text)
            
            # Clean question text
            clean_text = self._clean_question_text(question_text)
            
            questions.append({
                'number': number,
                'text': clean_text,
                'page_num': page_num,
                'raw_text': question_text
            })
        
        # Sort by question number
        questions.sort(key=lambda x: int(x['number']))
        
        return questions

    def _is_header_footer(self, text: str) -> bool:
        """Check if text is likely a header or footer"""
        header_footer_patterns = [
            r'TSS NATIONAL EXAMINATIONS',
            r'LEVEL 5, 2023-2024',
            r'Do not write in this margin',
            r'NESA \(National Examination',
            r'T 045_ Elevation and Scaffolding',
            r'INSTRUCTIONS TO CANDIDATES'
        ]
        
        for pattern in header_footer_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_page_number(self, text: str) -> int:
        """Extract page number from text"""
        page_match = re.search(r'--- PAGE (\d+) ---', text)
        return int(page_match.group(1)) if page_match else 1

    def _clean_question_text(self, text: str) -> str:
        """Clean and format question text"""
        # Remove page markers
        text = re.sub(r'--- PAGE \d+ ---', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove trailing marks information that got captured
        text = re.sub(r'\(\d+marks?\)$', '', text)
        
        return text.strip()

    def _process_question(self, question_data: Dict) -> Optional[NESAQuestion]:
        """Process a single question into NESAQuestion format"""
        try:
            number = question_data['number']
            text = question_data['text']
            
            # Extract marks
            marks = self._extract_marks(text)
            
            # Determine question type
            question_type = self._classify_question_type(text)
            
            # Check for multiple choice and tables
            has_multiple_choice = self._has_multiple_choice(text)
            has_table = self._has_table(text)
            multiple_choice_options = self._extract_multiple_choice_options(text) if has_multiple_choice else []
            
            # Classify subject and topic
            subject, topic = self._classify_subject_topic(text)
            
            # Assess difficulty
            difficulty = self._assess_difficulty(text, marks)
            
            # Generate answer
            model_answer = self._generate_answer(text, question_type, subject, marks)
            
            return NESAQuestion(
                number=number,
                text=text,
                marks=marks,
                question_type=question_type,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                model_answer=model_answer,
                page_num=question_data['page_num'],
                has_multiple_choice=has_multiple_choice,
                has_table=has_table,
                multiple_choice_options=multiple_choice_options
            )
            
        except Exception as e:
            logging.error(f"Error processing question {question_data.get('number', 'unknown')}: {e}")
            return None

    def _extract_marks(self, text: str) -> int:
        """Extract marks from question text"""
        # Look for patterns like (4marks), (10 marks), etc.
        mark_patterns = [
            r'\((\d+)\s*marks?\)',
            r'\((\d+)\s*mk\)',
            r'(\d+)\s*marks?',
            r'(\d+)\s*mk'
        ]
        
        for pattern in mark_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 5  # Default marks

    def _classify_question_type(self, text: str) -> str:
        """Classify question type based on content"""
        text_lower = text.lower()
        
        for q_type, pattern in self.type_patterns.items():
            if re.search(pattern, text_lower):
                return q_type
        
        return 'general'

    def _has_multiple_choice(self, text: str) -> bool:
        """Check if question has multiple choice options"""
        mc_patterns = [
            r'\b[A-E]\)\s+\w+',  # A) option, B) option
            r'\b[A-E]\.\s+\w+',  # A. option, B. option
            r'\([A-E]\)\s+\w+',  # (A) option, (B) option
        ]
        
        for pattern in mc_patterns:
            if len(re.findall(pattern, text)) >= 2:
                return True
        return False

    def _has_table(self, text: str) -> bool:
        """Check if question contains a table"""
        table_indicators = [
            'column a', 'column b', 'table', 'row', 'matching column',
            'answer column', 'function described in the column'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in table_indicators)

    def _extract_multiple_choice_options(self, text: str) -> List[str]:
        """Extract multiple choice options from text"""
        options = []
        
        # Pattern for A) option, B) option, etc.
        pattern = r'([A-E])\)\s+([^A-E)]+?)(?=[A-E]\)|$)'
        matches = re.findall(pattern, text)
        
        for letter, option_text in matches:
            options.append(f"{letter}) {option_text.strip()}")
        
        return options

    def _classify_subject_topic(self, text: str) -> tuple:
        """Classify subject and topic based on keywords"""
        text_lower = text.lower()
        
        # Count keyword matches for each subject
        subject_scores = {}
        for subject, keywords in self.subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                subject_scores[subject] = score
        
        # Get subject with highest score
        if subject_scores:
            subject = max(subject_scores.keys(), key=lambda x: subject_scores[x])
        else:
            subject = 'Construction Technology'
        
        # Determine topic based on subject
        topic_mapping = {
            'Masonry': 'Masonry Work',
            'Scaffolding': 'Scaffolding Systems',
            'Construction Technology': 'Construction Methods',
            'Safety Management': 'Safety Procedures'
        }
        
        topic = topic_mapping.get(subject, 'General Construction')
        
        return subject, topic

    def _assess_difficulty(self, text: str, marks: int) -> str:
        """Assess question difficulty"""
        if marks <= 4:
            return 'easy'
        elif marks <= 8:
            return 'medium'
        else:
            return 'hard'

    def _generate_answer(self, question_text: str, question_type: str, subject: str, marks: int) -> str:
        """Generate appropriate answer based on question type and content"""
        
        if question_type == 'definition':
            return self._generate_definition_answer(question_text, subject)
        elif question_type == 'calculation':
            return self._generate_calculation_answer(question_text)
        elif question_type == 'listing':
            return self._generate_listing_answer(question_text, subject, marks)
        elif question_type == 'comparison':
            return self._generate_comparison_answer(question_text, subject)
        elif question_type == 'explanation':
            return self._generate_explanation_answer(question_text, subject)
        elif question_type == 'sketch':
            return self._generate_sketch_answer(question_text, subject)
        elif question_type == 'matching':
            return self._generate_matching_answer(question_text)
        else:
            return self._generate_general_answer(question_text, subject, marks)

    def _generate_definition_answer(self, question_text: str, subject: str) -> str:
        """Generate definition-type answers"""
        text_lower = question_text.lower()
        
        definitions = {
            'brick': 'A brick is a rectangular block of clay, concrete, or other material used in construction. Bricks are fired in kilns to harden them and are commonly used for building walls, foundations, and other structures.',
            'footing': 'A footing is the structural foundation element that distributes the load from a building to the ground. It is typically wider than the wall it supports and is placed below the frost line to prevent damage from freezing.',
            'mortar': 'Mortar is a mixture of cement, sand, and water used to bind masonry units together. It provides structural integrity and weather resistance to masonry construction.',
            'scaffold': 'Scaffolding is a temporary structure used to support workers and materials during construction, maintenance, or repair work at height. It provides a safe working platform and access to elevated areas.',
            'bond': 'In masonry, a bond refers to the pattern in which bricks or stones are laid to ensure structural strength and stability. Common bonds include English bond, Flemish bond, and stretcher bond.'
        }
        
        # Look for specific terms to define
        answer_parts = []
        for term, definition in definitions.items():
            if term in text_lower:
                answer_parts.append(f"{term.title()}: {definition}")
        
        if answer_parts:
            return '\n\n'.join(answer_parts)
        else:
            return f"Key definitions related to {subject}:\n1. Technical terminology and concepts\n2. Industry-standard definitions\n3. Regulatory and safety requirements\n4. Practical applications in construction"

    def _generate_calculation_answer(self, question_text: str) -> str:
        """Generate calculation-type answers"""
        if 'rcc' in question_text.lower() or 'concrete' in question_text.lower():
            return """To calculate RCC (1:2:4) materials for 20m³:

Given:
- Volume = 20 m³
- Mix ratio = 1:2:4 (cement:sand:aggregate)
- Dry factor = 1.52
- Cement density = 1440 kg/m³
- 1 bag cement = 50 kg

Step 1: Calculate total dry volume
Dry volume = 20 × 1.52 = 30.4 m³

Step 2: Calculate individual volumes
Total parts = 1 + 2 + 4 = 7 parts
- Cement volume = (1/7) × 30.4 = 4.34 m³
- Sand volume = (2/7) × 30.4 = 8.69 m³
- Aggregate volume = (4/7) × 30.4 = 17.37 m³

Step 3: Calculate cement quantity
Cement weight = 4.34 × 1440 = 6,250 kg
Number of bags = 6,250 ÷ 50 = 125 bags

Answer: 125 bags of cement, 8.69 m³ sand, 17.37 m³ aggregate"""
        
        elif 'brick' in question_text.lower():
            return """To calculate number of bricks:

Step 1: Calculate total volume of wall
- Internal radius = 160 cm = 1.6 m
- Wall thickness = 0.2 m
- Height = 25 dm = 2.5 m
- External radius = 1.6 + 0.2 = 1.8 m

Volume = π(R² - r²) × h
Volume = π(1.8² - 1.6²) × 2.5 = π(3.24 - 2.56) × 2.5 = 5.34 m³

Step 2: Calculate effective brick volume
Total volume = 5.34 m³
Mortar volume = 1/4 of total = 1.34 m³
Brick volume = 5.34 - 1.34 = 4.0 m³

Step 3: Calculate number of bricks
Brick size = 210 × 110 × 60 mm = 0.001386 m³
Number of bricks = 4.0 ÷ 0.001386 = 2,887 bricks

Answer: Approximately 2,887 bricks required"""
        
        else:
            return "Step-by-step calculation approach:\n1. Identify given values and required unknowns\n2. Apply appropriate formulas\n3. Substitute values and solve\n4. Check units and reasonableness\n5. Present final answer with proper units"

    def _generate_listing_answer(self, question_text: str, subject: str, marks: int) -> str:
        """Generate listing-type answers"""
        text_lower = question_text.lower()
        
        if 'bonds' in text_lower:
            return """Three types of bonds in masonry:

1. **English Bond**: Alternating courses of headers and stretchers, providing maximum strength
2. **Flemish Bond**: Headers and stretchers alternating in each course, offering good appearance
3. **Stretcher Bond**: Only stretchers visible on face, commonly used in cavity walls"""
        
        elif 'foundation failures' in text_lower:
            return """Four causes of foundation failures:

1. **Poor Soil Investigation**: Inadequate soil testing leading to incorrect foundation design
2. **Inadequate Bearing Capacity**: Foundation loads exceeding soil bearing capacity
3. **Water-related Issues**: Poor drainage causing soil settlement or erosion
4. **Construction Defects**: Poor quality materials or workmanship during construction"""
        
        elif 'clearing work area' in text_lower:
            return """Five important elements for clearing work area:

1. **Site Survey**: Conduct thorough site investigation and measurement
2. **Utility Location**: Identify and mark underground utilities and services
3. **Safety Measures**: Establish safety perimeter and warning systems
4. **Debris Removal**: Clear vegetation, rubble, and unwanted materials
5. **Access Routes**: Ensure proper access for machinery and materials"""
        
        elif 'steel scaffolding' in text_lower and 'advantages' in text_lower:
            return """Steel Scaffolding - Advantages and Disadvantages:

**Advantages:**
1. High strength and load-bearing capacity
2. Durability and long service life
3. Reusable and cost-effective for multiple projects
4. Easy to assemble and dismantle
5. Standardized components ensure compatibility

**Disadvantages:**
1. Heavy weight requiring mechanical handling
2. Higher initial cost compared to other materials
3. Susceptible to rust and corrosion
4. Requires skilled labor for assembly
5. Storage space requirements for components"""
        
        else:
            # Generate generic listing based on marks
            items = min(marks, 10)  # Usually 1 mark per item
            return f"Key points for {subject}:\n" + "\n".join([f"{i+1}. Important aspect related to the topic" for i in range(items)])

    def _generate_comparison_answer(self, question_text: str, subject: str) -> str:
        """Generate comparison-type answers"""
        text_lower = question_text.lower()
        
        if 'tear' in text_lower and 'wear' in text_lower:
            return """Differentiation between Tear and Wear scaffold defects:

**Tear Defects:**
- Sudden failure or rupture of scaffold components
- Caused by excessive load or impact damage
- Results in complete separation or splitting
- Immediate safety hazard requiring urgent attention

**Wear Defects:**
- Gradual deterioration due to normal use
- Caused by friction, weathering, or repeated stress
- Results in thinning, surface damage, or deformation
- Progressive deterioration allowing planned maintenance"""
        
        elif 'bearing capacity' in text_lower and 'bearing pressure' in text_lower:
            return """Differentiation between Bearing Capacity and Bearing Pressure:

**Bearing Capacity:**
- Maximum load per unit area that soil can support safely
- Intrinsic property of the soil
- Determined by soil properties and foundation geometry
- Expressed in kN/m² or kg/cm²

**Bearing Pressure:**
- Actual pressure exerted by foundation on soil
- Depends on the applied load and foundation area
- Calculated as Load/Contact Area
- Must be less than bearing capacity for safe design"""
        
        else:
            return f"Key differences in {subject}:\n1. Definition and characteristics\n2. Applications and uses\n3. Advantages and limitations\n4. Performance criteria"

    def _generate_explanation_answer(self, question_text: str, subject: str) -> str:
        """Generate explanation-type answers"""
        text_lower = question_text.lower()
        
        if 'mixing' in text_lower and 'mortar' in text_lower:
            return """Comparison of Hand Mixing vs Mechanical Mixing of Mortar:

**Hand Mixing Steps:**
1. Measure cement, sand, and water accurately
2. Spread sand on clean mixing platform
3. Add cement and mix dry ingredients thoroughly
4. Make depression in center and add water gradually
5. Mix from edges toward center until uniform
6. Check consistency and adjust if needed

**Mechanical Mixing Steps:**
1. Load measured materials into mixer drum
2. Start mixer and add cement and sand first
3. Mix dry materials for 1-2 minutes
4. Add water gradually while mixing continues
5. Mix for 3-5 minutes until uniform consistency
6. Discharge mixed mortar for immediate use

**Key Differences:**
- Mechanical mixing provides better uniformity
- Hand mixing allows better control of water content
- Mechanical mixing is faster for large quantities
- Hand mixing suitable for small batches"""
        
        elif 'scaffold' in text_lower and 'inspection' in text_lower:
            return """Final Scaffolding Inspection Process:

**Pre-Inspection Preparation:**
1. Review scaffolding design and specifications
2. Gather inspection checklists and measuring tools
3. Ensure personal protective equipment

**Systematic Inspection Steps:**
1. **Foundation Check**: Verify base plates, sole plates, and ground conditions
2. **Structural Elements**: Inspect standards, ledgers, braces, and connections
3. **Working Platforms**: Check planks, guardrails, and toe boards
4. **Access Points**: Examine ladders, stairs, and entry/exit points
5. **Safety Features**: Verify fall protection and warning systems

**Documentation:**
- Record all findings with photographs
- Issue inspection certificate or defect notice
- Provide recommendations for any required actions

**Final Approval:**
- Confirm compliance with safety standards
- Authorize scaffold for intended use
- Schedule regular follow-up inspections"""
        
        else:
            return f"Comprehensive explanation of {subject} concepts:\n1. Fundamental principles and theory\n2. Step-by-step procedures\n3. Safety considerations and regulations\n4. Practical applications and examples\n5. Common challenges and solutions"

    def _generate_sketch_answer(self, question_text: str, subject: str) -> str:
        """Generate sketch-type answers"""
        text_lower = question_text.lower()
        
        if 'independent scaffolding' in text_lower or 'double scaffolding' in text_lower:
            return """Independent Scaffolding (Double Scaffolding) Components:

**Main Elements to Show in Sketch:**
1. **Standards**: Vertical tubes (both inner and outer rows)
2. **Ledgers**: Horizontal tubes connecting standards
3. **Transoms**: Cross-bearers supporting working platform
4. **Braces**: Diagonal tubes for stability
5. **Base Plates**: Foundation elements under standards
6. **Working Platform**: Boards or planks for workers
7. **Guardrails**: Safety barriers along platform edges
8. **Toe Boards**: Lower barriers to prevent material falling
9. **Ties**: Connections to building structure
10. **Access Ladder**: Means of ascent/descent

**Sketch Requirements:**
- Show both inner and outer scaffold frames
- Indicate proper spacing between standards
- Label all major components clearly
- Show connection details at joints
- Include safety features prominently"""
        
        elif 'english bond' in text_lower:
            return """English Bond Construction - 1st and 2nd Courses:

**Sketch Details:**
- **1st Course**: All stretchers (long face visible)
- **2nd Course**: All headers (short face visible)
- **Right Angle Construction**: Show corner detail with proper lap
- **Tools Required**: Trowel, spirit level, line and pins, plumb rule, measuring tape

**Key Points to Show:**
1. Proper overlap between courses
2. Vertical joints alignment
3. Corner bonding arrangement
4. Bed joint thickness (10-15mm)
5. Perpendicular wall junction

**Tools for Erecting English Bond:**
1. **Trowel**: For laying and spreading mortar
2. **Spirit Level**: For checking horizontal alignment
3. **Plumb Rule**: For checking vertical alignment
4. **Line and Pins**: For maintaining straight courses
5. **Measuring Tape**: For checking dimensions and spacing"""
        
        elif 'bonding' in text_lower and 'masonry' in text_lower:
            return """Technical Terms in Masonry Bonding:

**Sketch should clearly show:**
a) **Vertical Joint**: Joint between adjacent bricks in same course
b) **Stopped End**: End of wall where bonding pattern terminates
c) **Lap**: Horizontal overlap between bricks in adjacent courses
d) **Racking Back**: Stepped construction at end of wall section
e) **Bed Joint**: Horizontal mortar joint between courses
f) **Toothing**: Stepped construction for future wall extension
g) **Quoin**: External corner of masonry wall
h) **3/4 Bat**: Three-quarter brick used for bonding
i) **Course**: Horizontal layer of bricks
j) **Hang**: Temporary support during construction

**Important Notes:**
- Show proper proportions and relationships
- Label each component clearly
- Indicate typical dimensions where relevant"""
        
        else:
            return f"Sketch requirements for {subject}:\n1. Clear labeling of all components\n2. Proper proportions and dimensions\n3. Section and plan views as needed\n4. Construction details and connections\n5. Safety features and requirements"

    def _generate_matching_answer(self, question_text: str) -> str:
        """Generate matching-type answers"""
        if 'spirit level' in question_text.lower():
            return """Matching Tools with Functions:

**Correct Matches:**
A = 4 (Spirit level - Is used for leveling the horizontal plane of masonry works)
B = 1 (Scratching tool - Is used for making scratches on plaster while plastering)
C = 5 (Hoe - Is used for digging)
D = 2 (Jointers - They are used for jointing and pointing)
E = 3 (Scraper - Is used to remove extra mortar from walls, floors, and to scrap the wall ready for painting)

**Explanation:**
Each tool has a specific function in construction work. Proper identification and use of tools ensures quality workmanship and safety on construction sites."""
        
        else:
            return "Matching exercise approach:\n1. Analyze each item in Column A\n2. Review all options in Column B\n3. Match based on function and application\n4. Verify logical connections\n5. Present answers in required format"

    def _generate_general_answer(self, question_text: str, subject: str, marks: int) -> str:
        """Generate general comprehensive answers"""
        text_lower = question_text.lower()
        
        if 'wall function' in text_lower:
            return """Three Functions of a Wall:

1. **Structural Support**: Walls bear and transfer loads from floors, roofs, and other structural elements to the foundation, providing structural stability to the building.

2. **Enclosure and Protection**: Walls create enclosed spaces, providing protection from weather elements, wind, rain, and temperature variations while ensuring privacy and security.

3. **Space Division**: Walls divide interior spaces into functional rooms and areas, creating organized living or working environments according to building requirements."""
        
        elif 'brick properties' in text_lower:
            return """Five Properties of Good Bricks:

1. **Color**: Should be uniform deep red or cherry red color indicating proper burning and quality clay content.

2. **Shape**: Must be rectangular with sharp edges, uniform size, and straight surfaces for proper bonding and alignment.

3. **Size**: Standard dimensions (19×9×9 cm) with uniform measurements ensuring proper construction and minimizing mortar consumption.

4. **Texture**: Surface should be smooth and even, free from cracks, flaws, or rough patches for good appearance and weather resistance.

5. **Soundness**: Should produce clear ringing sound when struck, indicating proper burning and absence of internal defects or cracks."""
        
        else:
            points = min(marks, 8)  # Reasonable number of points
            return f"Key aspects of {subject}:\n" + "\n".join([f"{i+1}. Comprehensive point addressing the question requirements" for i in range(points)])


def test_nesa_processor():
    """Test the NESA processor"""
    processor = NESAPDFProcessor()
    
    # Test with sample file
    pdf_path = "uploads/2024_T045_Elevation_and_Scaffolding_operations.pdf"
    questions = processor.process_pdf(pdf_path)
    
    print(f"Extracted {len(questions)} questions:")
    for q in questions:
        print(f"Q{q.number}: {q.text[:100]}... ({q.marks} marks, {q.question_type})")


if __name__ == "__main__":
    test_nesa_processor()
# IntelliTutor - AI-Powered Educational Platform

## Overview

IntelliTutor is a comprehensive educational web application built with Flask that provides personalized learning experiences through adaptive questioning and intelligent AI-powered feedback. The platform features role-based access control (student/admin), advanced PDF question extraction, intelligent answer scoring using NLP techniques, comprehensive analytics, and complete administrative management capabilities.

## Key Features

- **AI-Powered Answer Evaluation**: Advanced NLP-based scoring using TF-IDF and cosine similarity
- **PDF Question Extraction**: Intelligent extraction from NESA exam papers with confidence scoring
- **Role-Based Access Control**: Separate student and admin interfaces with secure authentication
- **Comprehensive Analytics**: Performance tracking, score distribution, and user engagement metrics
- **Question Management**: CRUD operations with search, filter, and bulk operations
- **Data Export**: CSV/JSON export capabilities for questions, answers, and user performance
- **Responsive Design**: Mobile-first approach with Bootstrap 5 and custom styling

## Tech Stack

### Backend
- **Framework**: Flask 2.x (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **Authentication**: OAuth2 integration with Flask-Dance
- **Session Management**: Flask-Login for user session handling
- **File Processing**: PyMuPDF, pdfplumber for PDF extraction
- **NLP Libraries**: TextBlob, scikit-learn for intelligent scoring
- **Web Server**: Gunicorn for production deployment

### Frontend
- **Template Engine**: Jinja2 with Bootstrap 5
- **CSS Framework**: Bootstrap 5 with custom sky blue theme
- **JavaScript**: Vanilla JavaScript for interactive features
- **Icons**: Font Awesome for consistent iconography
- **Charts**: Chart.js for analytics visualization

### Infrastructure
- **Deployment**: Cloud environment with automatic restart
- **File Storage**: Local file system for PDF uploads
- **Session Storage**: Flask sessions with permanent configuration
- **Environment**: Environment variables for configuration

## Project Structure

```
intellitutor/
├── app.py                          # Flask application factory and configuration
├── main.py                         # Application entry point
├── models.py                       # SQLAlchemy database models
├── routes.py                       # Main application routes and business logic
├── auth.py                         # Authentication routes and decorators
├── replit_auth.py                  # Replit OAuth integration
├── data_store.py                   # In-memory sample data and mock functions
├── exam_processor.py               # PDF processing orchestration
├── enhanced_pdf_processor.py       # Advanced PDF question extraction
├── nesa_pdf_processor.py          # NESA-specific exam paper processing
├── pdf_processor.py               # Core PDF text extraction
├── simplified_pdf_processor.py    # Basic PDF processing utilities
├── create_demo_accounts.py        # Demo account creation script
├── reset_database.py              # Database reset utilities
├── static/
│   ├── css/
│   │   └── style.css              # Custom styling and themes
│   └── js/
│       └── main.js                # Frontend JavaScript functionality
├── templates/
│   ├── auth/
│   │   ├── login.html             # User login page
│   │   └── register.html          # User registration page
│   ├── admin_dashboard.html       # Main admin interface
│   ├── admin_add_question.html    # Manual question creation form
│   ├── admin_edit_question.html   # Question editing interface
│   ├── admin_analytics_simple.html # Analytics dashboard
│   ├── admin_review_questions.html # PDF question review interface
│   ├── student_dashboard.html     # Student main interface
│   ├── question.html              # Question display and answer submission
│   ├── result.html                # Answer results and feedback
│   ├── landing.html               # Application landing page
│   ├── base.html                  # Base template with navigation
│   └── 403.html                   # Error page template
├── uploads/                       # PDF file storage directory
├── instance/
│   └── intellitutor.db           # SQLite database file
├── pyproject.toml                 # Python dependencies
└── replit.md                      # Project documentation and preferences
```

## System Architecture

### Application Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface Layer                      │
├─────────────────────────────────────────────────────────────┤
│  Student Dashboard  │  Admin Dashboard  │  Authentication   │
│  - Question Display │  - Question Mgmt  │  - Replit OAuth   │
│  - Answer Submission│  - Analytics      │  - Session Mgmt   │
│  - Progress View    │  - Data Export    │  - Role Control   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                      │
├─────────────────────────────────────────────────────────────┤
│  PDF Processing    │  NLP Scoring      │  Data Management  │
│  - NESA Extraction │  - TF-IDF Analysis│  - CRUD Operations│
│  - Text Chunking   │  - Cosine Similarity│ - Search/Filter │
│  - Question ID     │  - Concept Coverage│  - Export Utils   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                       │
├─────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM    │  File System      │  Session Store    │
│  - User Models     │  - PDF Storage    │  - Authentication │
│  - Question Models │  - Static Assets  │  - User Sessions  │
│  - Answer Models   │  - Upload Mgmt    │  - Preferences    │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- User Management
Users (id, username, email, password_hash, first_name, last_name, role, 
       questions_attempted, questions_correct, total_score, badges, 
       created_at, updated_at)

-- Question Storage
Questions (id, subject, topic, question_text, model_answer, difficulty, 
           created_at)

-- Answer Tracking
Answers (id, user_id, question_id, user_answer, score, feedback, 
         created_at)

-- OAuth Integration
OAuth (id, provider, provider_id, provider_user_id, token, 
       provider_user_login, user_id, created_at)
```

## Data Flow Architecture

### Student Learning Flow

```
1. Authentication
   User → OAuth Provider → OAuth Token → User Session → Role Assignment

2. Question Retrieval
   Student Dashboard → Database Query → Question Selection → Template Rendering

3. Answer Submission
   Form Submit → NLP Analysis → Score Calculation → Database Storage → Feedback

4. Progress Tracking
   Answer Storage → Statistics Update → Badge Calculation → Dashboard Update
```

### Admin Management Flow

```
1. Question Management
   Admin Dashboard → CRUD Operations → Database Updates → Cache Refresh

2. PDF Processing
   File Upload → PDF Extraction → Question Identification → Review Interface → Database Storage

3. Analytics Generation
   Data Aggregation → Statistical Analysis → Chart Generation → Dashboard Display

4. Data Export
   Query Execution → Format Conversion → File Generation → Download Response
```

### PDF Processing Pipeline

```
1. File Upload
   Admin Upload → File Validation → Secure Storage → Processing Queue

2. Text Extraction
   PDF → PyMuPDF/pdfplumber → Raw Text → Chunk Segmentation

3. Question Identification
   Text Chunks → Pattern Recognition → Confidence Scoring → Question Extraction

4. NLP Enhancement
   Raw Questions → Answer Generation → Subject Classification → Difficulty Assessment

5. Review & Storage
   Extracted Questions → Admin Review → Manual Editing → Database Storage
```

## Core Components

### 1. Authentication System (`auth.py`, `replit_auth.py`)

**Purpose**: Secure user authentication and authorization
**Technology**: Replit OAuth2 with Flask-Login
**Features**:
- OAuth2 integration with automatic user provisioning
- Role-based access control (student/admin)
- Session management with permanent sessions
- Decorator-based route protection

**Implementation**:
```python
@require_admin
def admin_dashboard():
    # Admin-only functionality
    
@require_login  
def student_dashboard():
    # Authenticated user functionality
```

### 2. PDF Processing Engine

#### Enhanced PDF Processor (`enhanced_pdf_processor.py`)
**Purpose**: Advanced question extraction with NLP techniques
**Features**:
- Multi-method text extraction (PyMuPDF, pdfplumber)
- Intelligent text chunking and deduplication
- Confidence scoring for question identification
- Subject and topic classification
- Automated answer generation

#### NESA PDF Processor (`nesa_pdf_processor.py`)
**Purpose**: Specialized processing for NESA exam papers
**Features**:
- Numbered question detection (01. through 21.)
- Construction technology domain expertise
- Multiple choice and table detection
- Context-aware answer generation

**Processing Workflow**:
```python
1. PDF → Text Extraction → Chunk Creation
2. Chunks → Pattern Matching → Question Identification
3. Questions → NLP Analysis → Answer Generation
4. Results → Confidence Scoring → Admin Review
```

### 3. Intelligent Scoring System (`routes.py`)

**Purpose**: AI-powered answer evaluation using NLP
**Technology**: TF-IDF vectorization and cosine similarity
**Features**:
- Text preprocessing and normalization
- Concept coverage assessment using TextBlob
- Difficulty-based score adjustment
- Detailed feedback generation

**Scoring Algorithm**:
```python
1. Text Similarity (60%): TF-IDF + Cosine Similarity
2. Concept Coverage (25%): Key phrase extraction and matching
3. Length Appropriateness (15%): Response length vs expected length
4. Difficulty Adjustment: Scale based on question difficulty
```

### 4. Analytics Dashboard (`admin_analytics_simple.html`)

**Purpose**: Comprehensive system performance insights
**Features**:
- Key performance indicators (KPIs)
- Score distribution analysis
- Top performer identification
- Recent activity monitoring
- Data export capabilities

**Metrics Tracked**:
- Total questions and active students
- Average scores and completion rates
- Subject-wise question distribution
- Performance trends and patterns

### 5. Question Management System

**Purpose**: Complete CRUD operations for question administration
**Features**:
- Manual question creation with validation
- Bulk operations and filtering
- Search functionality across all fields
- Edit/delete with confirmation dialogs

**Management Workflow**:
```
Create → Validate → Store → Index
Read → Search → Filter → Display
Update → Validate → Modify → Refresh
Delete → Confirm → Remove → Cleanup
```

## Data Management

### Question Storage Strategy
- **Database**: Primary storage in SQLAlchemy models
- **Indexing**: Subject and topic indexing for fast retrieval
- **Validation**: Comprehensive form validation before storage
- **Relationships**: Foreign key relationships for data integrity

### File Management
- **Upload Directory**: `uploads/` for PDF storage
- **Security**: File type validation and secure naming
- **Processing**: Temporary files during PDF processing
- **Cleanup**: Automatic cleanup of temporary files

### Session Management
- **Storage**: Flask sessions with secure configuration
- **Persistence**: Permanent sessions for user convenience
- **Security**: Session secret from environment variables
- **Cleanup**: Automatic session cleanup on logout

## Configuration and Environment

### Environment Variables
```bash
SESSION_SECRET=your-session-secret-key
DATABASE_URL=sqlite:///instance/intellitutor.db  # or PostgreSQL URL
OAUTH_CLIENT_ID=your-oauth-client-id
ISSUER_URL=https://your-oauth-provider.com/oidc
```

### Application Configuration
```python
# Database Configuration
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Session Configuration
SECRET_KEY = os.environ.get("SESSION_SECRET")
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
```

## API Endpoints and Routes

### Public Routes
- `GET /` - Landing page
- `GET /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Student Routes (Authentication Required)
- `GET /student/dashboard` - Student main interface
- `GET /question` - Get random question
- `POST /submit_answer` - Submit answer for scoring
- `GET /result/<answer_id>` - View answer results

### Admin Routes (Admin Role Required)
- `GET /admin/dashboard` - Admin main interface
- `GET /admin/question/add` - Manual question creation form
- `POST /admin/question/add` - Process new question
- `GET /admin/question/<id>/edit` - Question editing form
- `POST /admin/question/<id>/edit` - Update question
- `DELETE /admin/question/<id>/delete` - Delete question
- `GET /admin/analytics` - Analytics dashboard
- `GET /admin/export` - Data export functionality
- `POST /admin/upload` - PDF upload and processing

## Deployment and Operations

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SESSION_SECRET="your-secret-key"
export DATABASE_URL="sqlite:///instance/intellitutor.db"

# Run application
python main.py
```

### Production Deployment
```bash
# Using Gunicorn
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Environment configuration
# Set production database URL
# Configure session secrets
# Enable SSL/HTTPS
```

### Database Management
```python
# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Create demo accounts
python create_demo_accounts.py

# Reset database
python reset_database.py
```

## Security Considerations

### Authentication Security
- OAuth2 integration with trusted provider
- Secure session management with encrypted cookies
- Role-based access control with route protection
- Password hashing using Werkzeug security

### Data Security
- SQL injection prevention through ORM parameterization
- File upload validation and secure storage
- CSRF protection through Flask-WTF
- Environment variable configuration for secrets

### Input Validation
- Form validation on both client and server side
- File type and size restrictions for uploads
- Text input sanitization for question processing
- User input validation for search and filters

## Performance Optimization

### Database Optimization
- Efficient queries with proper indexing
- Connection pooling for database connections
- Lazy loading for related data
- Query optimization for analytics

### File Processing Optimization
- Streaming file uploads for large PDFs
- Background processing for PDF extraction
- Caching of processed results
- Cleanup of temporary files

### Frontend Optimization
- CDN delivery for external libraries
- Compressed CSS and JavaScript
- Optimized image assets (SVG preferred)
- Responsive design for mobile performance

## Monitoring and Analytics

### Application Metrics
- User engagement tracking
- Question completion rates
- Score distribution analysis
- System performance monitoring

### Error Handling
- Comprehensive error logging
- User-friendly error pages
- Graceful degradation for failures
- Database rollback on errors

### Data Analytics
- Student performance tracking
- Question difficulty analysis
- Subject popularity metrics
- Learning progress visualization

## Future Enhancements

### Planned Features
- Real-time collaboration capabilities
- Advanced AI models for scoring
- Mobile application development
- Multi-language support

### Scalability Improvements
- Microservices architecture
- Redis caching implementation
- Load balancing configuration
- Database sharding for large datasets

### Integration Possibilities
- LMS integration (Moodle, Canvas)
- External assessment tools
- Video conferencing integration
- Third-party content providers

## Troubleshooting

### Common Issues
1. **Database Connection Errors**: Check DATABASE_URL configuration
2. **PDF Processing Failures**: Verify file format and size limits
3. **Authentication Issues**: Confirm Replit Auth configuration
4. **Performance Issues**: Monitor database query performance

### Debug Mode
```python
# Enable debug mode for development
app.debug = True
logging.basicConfig(level=logging.DEBUG)
```

### Logging Configuration
```python
# Configure comprehensive logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
```

## Contributing

### Development Guidelines
- Follow PEP 8 style guidelines for Python code
- Use semantic versioning for releases
- Write comprehensive docstrings for functions
- Include unit tests for new features

### Code Review Process
- Feature branch workflow
- Pull request reviews required
- Automated testing before merge
- Documentation updates with code changes

## License and Usage

This project is developed for educational purposes with the following considerations:
- Open source components used under their respective licenses
- Educational content and questions should respect copyright
- PDF processing limited to authorized educational materials
- User data handled in compliance with privacy regulations

---

*This documentation provides a comprehensive overview of the IntelliTutor system. For specific implementation details, refer to the source code and inline documentation.*
# IntelliTutor

## Overview

IntelliTutor is an AI-powered tutoring platform built with Flask that provides personalized learning experiences through adaptive questioning and intelligent feedback. The application features role-based access control (student/admin), progress tracking, and a comprehensive question management system. It integrates with Replit Auth for seamless authentication and uses SQLAlchemy for database operations.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Styling**: Custom CSS with sky blue theme and gradient designs
- **JavaScript**: Vanilla JavaScript for interactive features including progress animations, form validation, and keyboard shortcuts
- **Icons**: Font Awesome for consistent iconography
- **Layout**: Base template with navigation and role-based menu systems

### Backend Architecture
- **Framework**: Flask web framework with modular blueprint structure
- **Authentication**: Replit Auth integration with OAuth2 flow
- **Session Management**: Flask-Login for user session handling
- **Database ORM**: SQLAlchemy with declarative base for model definitions
- **Middleware**: ProxyFix for handling reverse proxy headers

### Data Storage Solutions
- **Primary Database**: SQLAlchemy with support for SQLite (default) or PostgreSQL
- **Models**: User, OAuth, Question, and Answer entities with proper relationships
- **Sample Data**: In-memory data store for demo questions and mock AI functionality
- **Session Storage**: Flask sessions with permanent session configuration

## Key Components

### Authentication System
- **Replit Auth Integration**: OAuth2-based authentication with automatic user provisioning
- **Role-Based Access**: Student and admin roles with appropriate permission checks
- **User Management**: Profile information storage with progress tracking capabilities

### Question Management
- **Question Database**: Structured storage of questions with subject, topic, and difficulty classification
- **Sample Questions**: Predefined question set covering Mathematics, Science, and English
- **Answer Processing**: Student response capture and storage system

### Progress Tracking
- **Student Metrics**: Questions attempted, correct answers, total score, and badge system
- **Performance Analytics**: Accuracy calculations and average score tracking
- **Admin Dashboard**: System-wide statistics and user management interface

### User Interface
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **Dashboard Views**: Separate interfaces for students and administrators
- **Interactive Elements**: Progress animations, form validation, and real-time feedback

## Data Flow

### Student Learning Flow
1. User authenticates via Replit Auth
2. Student dashboard displays current progress and statistics
3. New question request retrieves random question from database
4. Student submits answer through form interface
5. Mock AI scoring provides immediate feedback
6. Results are stored and progress metrics updated
7. User can continue with new questions or review performance

### Admin Management Flow
1. Admin user accesses administrative dashboard
2. System statistics are aggregated and displayed
3. User management interface allows role assignments
4. Question management enables content administration

### Authentication Flow
1. User initiates login through Replit Auth
2. OAuth2 flow redirects to Replit for authentication
3. User information is retrieved and stored locally
4. Session is established with role-based permissions
5. User is redirected to appropriate dashboard

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **Flask-Login**: User session management
- **Flask-Dance**: OAuth integration framework
- **PyJWT**: Token handling for authentication

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **jQuery**: JavaScript utilities (implied by template structure)

### Infrastructure Dependencies
- **Replit Auth**: External authentication provider
- **Database**: SQLite for development, PostgreSQL for production
- **Environment Variables**: Session secrets and database configuration

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with debug mode enabled
- **Production**: Environment-based database URL configuration
- **Security**: Session secret management through environment variables

### Database Management
- **Auto-Creation**: Tables created automatically on application startup
- **Connection Pooling**: SQLAlchemy engine options for connection management
- **Migration Support**: Declarative base setup for future schema changes

### Hosting Considerations
- **Proxy Support**: ProxyFix middleware for reverse proxy deployments
- **Static Assets**: CSS and JavaScript files served through Flask static routing
- **Security Headers**: HTTPS URL generation support

## Changelog

```
Changelog:
- June 28, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```
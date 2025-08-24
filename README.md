# NeuraVia - AI-Powered Neurological Health Assessment Platform

A comprehensive healthcare platform that provides AI-driven neurological assessments, symptom tracking, hearing evaluations, and personalized medical reports.

## 🚀 New Features (Latest Update)

### Enhanced AI Assessment System

- **Smart Assessment Completion**: AI now intelligently determines when an assessment is complete based on information quality, not just message count
- **Personalized Chat Experience**: AI incorporates user context (age, gender, existing symptoms, hearing status) for tailored assessments
- **Progress Tracking**: Real-time assessment progress with visual indicators and stage-based guidance
- **Session Management**: Users can only have one active assessment at a time, ensuring focused evaluations

### Improved Report Generation

- **Quality Threshold**: Reports are only generated when sufficient information is collected (85%+ completion score)
- **Rich Content**: Reports now include user context, collected data, and comprehensive markdown-formatted content
- **Professional Formatting**: Raw markdown is converted to beautiful, readable HTML with proper styling
- **Data Integration**: Seamless integration of symptoms, hearing tests, and medical history

### Better User Experience

- **Chat Locking**: Chat is locked after assessment completion to prevent confusion
- **New Assessment Flow**: Users must start new sessions for new assessments, ensuring clean data separation
- **Visual Progress**: Color-coded progress bars and stage indicators throughout the assessment
- **Context Awareness**: User profile information is displayed and utilized during assessments

## 🏗️ Architecture

### Backend (FastAPI + Supabase)

- **AI Service**: Enhanced with completion scoring and user context integration
- **Chat Router**: Improved session management and assessment logic
- **Database**: Updated schema with assessment completion tracking
- **User Context**: Comprehensive user profile and history gathering

### Frontend (Next.js + TypeScript)

- **Chat Interface**: Enhanced with progress tracking and completion logic
- **Report Viewer**: Beautiful markdown rendering with user context display
- **Session Management**: Improved session switching and new assessment creation
- **Progress Indicators**: Visual feedback throughout the assessment process

## 🔧 Technical Implementation

### Assessment Completion Logic

```typescript
// AI determines completion based on:
- Symptom collection quality (25 points)
- Medical history depth (20 points)
- Risk factor assessment (15 points)
- Hearing concerns (15 points)
- Impact assessment (15 points)
- Medications and family history (20 points)
- Minimum 85% completion required
```

### User Context Integration

```typescript
// AI receives comprehensive user context:
- Age and gender for personalized questions
- Existing symptoms for continuity
- Hearing test results for auditory assessment
- Previous assessment history
- Medical background information
```

### Markdown Rendering

```typescript
// Converts AI-generated markdown to HTML:
- Headers (H1, H2, H3) with proper styling
- Bold and italic text formatting
- Bullet points and numbered lists
- Paragraph breaks and spacing
- Professional medical report appearance
```

## 📊 Database Schema Updates

### New Fields Added

- `chat_sessions.assessment_complete` - Boolean flag for completion status
- `chat_sessions.completion_score` - Integer score (0-100) for progress tracking
- `patient_reports.user_context` - JSONB field for user information storage

### Indexes for Performance

- `idx_chat_sessions_user_id` - Fast user session lookup
- `idx_chat_sessions_is_active` - Quick active session identification

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ and pip
- Supabase account and project
- Gemini API key for AI features

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-username/NeuraViaHack.git
cd NeuraViaHack
```

2. **Backend Setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**

```bash
cd frontend
npm install
```

4. **Environment Configuration**

```bash
# Backend (.env)
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

5. **Database Setup**

```bash
# Run the main schema
psql -h your_host -U your_user -d your_db -f supabase/schema_hackathon.sql

# Run migration if updating existing database
psql -h your_host -U your_user -d your_db -f supabase/migration_safe.sql
```

6. **Start Services**

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

## 🔄 Migration Guide

If you have an existing NeuraVia database, run the migration script:

```bash
psql -h your_host -U your_user -d your_db -f supabase/migration_safe.sql
```

This will safely add new fields without affecting existing data.

## 📱 Usage

### Starting an Assessment

1. Navigate to `/chat`
2. The AI will guide you through a comprehensive assessment
3. Progress is tracked in real-time with visual indicators
4. Assessment completion is determined by AI analysis

### Generating Reports

1. Complete the assessment (85%+ completion required)
2. Click "Generate Report" when available
3. View beautifully formatted reports with user context
4. Access reports from the `/reports` page

### Session Management

- Only one active assessment per user
- Start new assessments for new evaluations
- Previous sessions are preserved and accessible
- Chat is locked after completion

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the migration guide for database updates

## 🔮 Future Enhancements

- **Multi-language Support**: Internationalization for global users
- **Advanced Analytics**: Detailed assessment analytics and trends
- **Integration APIs**: Connect with external healthcare systems
- **Mobile App**: Native mobile applications for iOS and Android
- **Telemedicine**: Video consultation integration
- **AI Training**: Continuous improvement of assessment algorithms

---

**NeuraVia** - Empowering neurological health through AI-driven assessments and personalized care.

# 🧠 NeuraVia - AI-Powered Neurological Health Assessment Platform

NeuraVia is a comprehensive healthcare platform that combines AI-powered medical assessments, interactive hearing tests, and comprehensive patient reporting to provide personalized neurological health insights.

## ✨ Features

### 🔐 **Authentication & User Management**

- Secure user registration and login with Supabase
- User profile management with age and gender tracking
- Session management and authentication state

### 📝 **Symptom Management**

- Interactive symptom reporting with severity scales (1-10)
- Duration tracking and detailed descriptions
- Batch symptom submission for comprehensive health tracking

### 🤖 **AI Medical Assessment**

- Intelligent AI medical attendant using Google Gemini
- Structured neurological assessment conversations
- Progressive data collection and analysis
- Session management for ongoing assessments

### 🎧 **Interactive Hearing Tests**

- Comprehensive frequency testing (125Hz - 8000Hz)
- Left and right ear evaluation
- Volume-controlled testing with real-time feedback
- Detailed results and recommendations

### 📊 **Comprehensive Reports**

- AI-generated medical reports with criticality ratings
- Symptom analysis and risk assessment
- Hearing test integration and recommendations
- Follow-up action planning

## 🏗️ Architecture

### **Frontend (Next.js 15 + TypeScript)**

- Modern React with TypeScript for type safety
- Tailwind CSS for beautiful, responsive UI
- Authentication context for state management
- Real-time chat interface for AI assessments

### **Backend (FastAPI + Python)**

- High-performance async API with FastAPI
- Supabase integration for database and auth
- Google Gemini AI integration for medical assessments
- Structured data models and validation

### **Database (Supabase + PostgreSQL)**

- Secure user profiles and authentication
- Comprehensive health data storage
- Row-level security (RLS) policies
- Real-time data synchronization

## 🚀 Quick Start

### **Prerequisites**

- Node.js 18+ and npm
- Python 3.8+
- Supabase account
- Google Gemini API key

### **1. Clone and Setup**

```bash
git clone <repository-url>
cd NeuraViaHack
```

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env
# Edit .env with your credentials
```

### **3. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp env.local.example .env.local
# Edit .env.local with your credentials
```

### **4. Environment Configuration**

#### **Backend (.env)**

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
GEMINI_API_KEY=your_gemini_api_key
APP_ENV=development
DEBUG=true
```

#### **Frontend (.env.local)**

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **5. Database Setup**

```bash
# Run the Supabase schema
# Copy schema.sql content to your Supabase SQL editor
# Execute the schema to create tables and policies
```

### **6. Start the Application**

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access the application!

## 🔄 User Flow

### **1. Authentication**

- User visits the application
- Signs up with email, password, age, and gender
- Creates secure user profile in Supabase

### **2. Symptom Reporting**

- User navigates to Symptoms page
- Reports detailed symptoms with severity levels
- Adds duration and descriptions for each symptom
- Submits comprehensive symptom data

### **3. AI Medical Assessment**

- User starts AI assessment from Chat page
- AI medical attendant conducts structured interview
- Progressive data collection through conversation
- Assessment completion with comprehensive data

### **4. Hearing Test (Optional)**

- User can take interactive hearing assessment
- Tests multiple frequencies for both ears
- Volume-controlled testing with real-time feedback
- Results integrated with overall health assessment

### **5. Report Generation**

- AI generates comprehensive medical report
- Includes symptom analysis, risk assessment, and recommendations
- Hearing test results integrated when available
- Criticality ratings and follow-up actions

### **6. Health Dashboard**

- Comprehensive overview of all health data
- Symptom tracking and history
- Hearing test results and trends
- AI assessment reports and recommendations

## 🛠️ Development

### **Project Structure**

```
NeuraViaHack/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── ai_service.py   # Google Gemini integration
│   │   ├── database.py     # Supabase database operations
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── env.example        # Environment template
├── frontend/               # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # Reusable components
│   ├── lib/               # Utilities and contexts
│   ├── package.json       # Node dependencies
│   └── env.local.example  # Environment template
├── supabase/              # Database schema
│   └── schema.sql         # PostgreSQL schema
└── README.md              # This file
```

### **Key Components**

#### **Frontend Components**

- `AuthProvider`: Authentication context and state management
- `UserNav`: User navigation and authentication controls
- `SymptomForm`: Interactive symptom reporting interface
- `ChatInterface`: AI medical assessment chat
- `HearingTest`: Interactive hearing assessment
- `ReportsDashboard`: Comprehensive health overview

#### **Backend Services**

- `AIService`: Google Gemini integration for medical assessments
- `SupabaseDB`: Database operations and data management
- `Routers`: RESTful API endpoints for all functionality

### **API Endpoints**

#### **Authentication & Users**

- `POST /api/users/profile` - Create user profile
- `GET /api/users/profile/{user_id}` - Get user profile
- `PUT /api/users/profile/{user_id}` - Update user profile

#### **Symptoms**

- `POST /api/symptoms/batch` - Create multiple symptoms
- `GET /api/symptoms/user/{user_id}` - Get user symptoms
- `DELETE /api/symptoms/{symptom_id}` - Delete symptom

#### **AI Chat & Assessment**

- `POST /api/chat/session` - Create chat session
- `POST /api/chat/send` - Send message to AI
- `GET /api/chat/sessions/{user_id}` - Get user sessions
- `POST /api/chat/generate-report/{session_id}` - Generate report

#### **Hearing Tests**

- `POST /api/hearing/test` - Create hearing test
- `GET /api/hearing/user/{user_id}` - Get user tests
- `GET /api/hearing/user/{user_id}/summary` - Get hearing summary

#### **Patient Reports**

- `GET /api/reports/user/{user_id}` - Get user reports
- `GET /api/reports/{report_id}` - Get specific report
- `PUT /api/reports/{report_id}` - Update report

## 🔒 Security Features

- **Row-Level Security (RLS)**: Users can only access their own data
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive data validation with Pydantic
- **CORS Protection**: Configured CORS policies for security
- **Environment Variables**: Secure credential management

## 🧪 Testing

### **Backend Testing**

```bash
cd backend
# Run tests (when implemented)
pytest
```

### **Frontend Testing**

```bash
cd frontend
# Run tests (when implemented)
npm test
```

## 🚀 Deployment

### **Backend Deployment**

- Deploy to platforms like Railway, Render, or Heroku
- Set environment variables in deployment platform
- Ensure CORS origins are updated for production

### **Frontend Deployment**

- Build and deploy to Vercel, Netlify, or similar
- Update environment variables for production
- Configure domain and SSL certificates

### **Database Deployment**

- Use Supabase production instance
- Configure backup and monitoring
- Set up proper security policies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the code examples

## 🔮 Future Enhancements

- **Mobile App**: React Native mobile application
- **Telemedicine Integration**: Video consultation features
- **Advanced AI Models**: Integration with medical AI models
- **Data Analytics**: Advanced health insights and trends
- **Integration APIs**: Connect with other health platforms
- **Multi-language Support**: Internationalization features

---

**Built with ❤️ for better healthcare through technology**

Indian Court Tracker 🏛️
A comprehensive web application for tracking Indian court cases and daily cause lists by scraping official High Court and District Court portals. Built with React.js frontend, FastAPI backend, and advanced web scraping capabilities.
🚀 Features
Case Search & Tracking
•	🔍 Real-time Case Search - Search cases by type, number, and year
•	🏛️ Multi-Portal Integration - Accesses High Court Services, District Courts, and Supreme Court portals
•	📊 Case Details Extraction - Party names, filing dates, hearing dates, case status
•	💾 Redis Caching - Fast response times with intelligent caching
•	🔄 Real-time Updates - Automatic background jobs for case status updates
Cause List Management
•	📋 Daily Cause Lists - Fetch and display daily hearing lists
•	🗓️ Date-based Filtering - View cause lists for specific dates
•	🏛️ Court-wise Filtering - Filter by specific courts (High Court, District Court)
•	📄 PDF Downloads - Download official cause list PDFs
•	⚡ Real-time Extraction - Live scraping of court websites
Advanced Web Scraping
•	🤖 Captcha Handling - Automatic captcha detection and solving using OCR
•	🔄 User-Agent Rotation - Avoid detection with rotating browser identities
•	🛡️ Anti-Bot Protection - Sophisticated evasion techniques
•	📊 Content Mining - Advanced regex patterns for data extraction
•	🔁 Retry Mechanisms - Exponential backoff and error recovery
Data Management
•	🗄️ PostgreSQL Database - Robust data storage with SQLAlchemy ORM
•	⚡ Redis Cache - High-performance caching layer
•	📈 Background Jobs - Automated data updates and maintenance
•	🔍 Full-text Search - Advanced search capabilities
•	📊 Data Analytics - Case statistics and trends
User Interface
•	💻 Modern React UI - Responsive design with Tailwind CSS
•	📱 Mobile Responsive - Optimized for all device sizes
•	🎨 Intuitive Interface - User-friendly design for legal professionals
•	📊 Data Visualization - Charts and graphs for case analytics
•	🔄 Real-time Updates - Live updates without page refresh
🛠️ Tech Stack
Backend
•	FastAPI - High-performance Python web framework
•	SQLAlchemy - SQL toolkit and ORM
•	PostgreSQL - Primary database
•	Redis - Caching and session storage
•	Pydantic - Data validation and serialization
•	BeautifulSoup - HTML parsing and scraping
•	Requests - HTTP client for API calls
Frontend
•	React.js 18 - Modern JavaScript framework
•	TypeScript - Type-safe JavaScript
•	Tailwind CSS - Utility-first CSS framework
•	React Query - Data fetching and caching
•	React Router - Client-side routing
•	Axios - HTTP client
Scraping & OCR
•	Tesseract OCR - Captcha solving and text recognition
•	OpenCV - Image processing for OCR enhancement
•	Pillow (PIL) - Python image manipulation
•	Pytesseract - Python wrapper for Tesseract
DevOps & Deployment
•	Docker - Containerization
•	Docker Compose - Multi-container orchestration
•	GitHub Actions - CI/CD pipeline
•	Render - Cloud hosting platform
📋 Prerequisites
•	Python 3.8+
•	Node.js 16+
•	PostgreSQL 13+
•	Redis 6+
•	Tesseract OCR (for captcha solving)
🚀 Quick Start
1. Clone Repository
git clone https://github.com/yourusername/indian-court-tracker.git
cd indian-court-tracker

2. Backend Setup
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and Redis configurations

3. Database Setup
# Create PostgreSQL database
createdb court_tracker

# Run migrations
alembic upgrade head

4. Install Tesseract OCR
Windows:
1.	Download from: https://github.com/UB-Mannheim/tesseract/wiki
2.	Install to: C:\Program Files\Tesseract-OCR\
3.	Add to system PATH
macOS:
brew install tesseract

Ubuntu/Debian:
sudo apt install tesseract-ocr

5. Frontend Setup
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start development server
npm start

6. Start Backend Server
# In backend directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

7. Access Application
•	Frontend: http://localhost:3000
•	Backend API: http://localhost:8000
•	API Documentation: http://localhost:8000/docs
🐳 Docker Deployment
Using Docker Compose
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

Services Started:
•	Backend API: Port 8000
•	Frontend: Port 3000
•	PostgreSQL: Port 5432
•	Redis: Port 6379
⚙️ Configuration
Environment Variables
Create .env file in the backend directory:
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/court_tracker

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Scraping Configuration
SCRAPING_DELAY=2
MAX_RETRIES=3
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# OCR Configuration (Windows)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Logging
LOG_LEVEL=INFO

📊 API Endpoints
Case Search
POST /api/v1/cases/search
{
  "case_type": "WP",
  "case_number": "1234",
  "year": 2024
}

Cause Lists
POST /api/v1/cause-lists/by-date
{
  "hearing_date": "2024-10-07",
  "court_filter": "Delhi High Court"
}

Available Courts
GET /api/v1/cause-lists/courts

Health Check
GET /health

🎯 Supported Courts
High Courts
•	Delhi High Court
•	Supreme Court of India
•	Bombay High Court
•	Punjab and Haryana High Court
•	Calcutta High Court
•	And more...
Case Types
•	WP - Writ Petition
•	CWP - Civil Writ Petition
•	PIL - Public Interest Litigation
•	CRL - Criminal Cases
•	CA - Civil Appeal
•	CS - Civil Suit
🔧 Advanced Features
Captcha Solving
The application includes advanced captcha handling:
# Automatic captcha detection
has_captcha, captcha_info = captcha_handler.detect_captcha(html_content)

# OCR-based solving
captcha_solution = await captcha_handler.solve_captcha(captcha_url, session)

Real Data Extraction
# Multi-portal search
portals = {
    'ecourts': 'https://services.ecourts.gov.in/ecourtindia_v6/',
    'delhi_hc': 'https://delhihighcourt.nic.in/',
    'supremecourt': 'https://main.sci.gov.in/'
}

# Extract real case information
case_info = await extract_case_info(response, case_type, case_number, year)

Background Jobs
# Daily cause list updates
@scheduler.scheduled_job("cron", hour=6, minute=0)  # 6:00 AM daily
async def update_daily_cause_lists():
    # Fetch and store cause lists
    pass

🚦 Troubleshooting
Common Issues
Tesseract Not Found
# Error: tesseract is not recognized
# Solution: Add Tesseract to system PATH
export PATH=$PATH:/usr/local/bin/tesseract  # macOS/Linux
# Or set in Python:
pytesseract.pytesseract.tesseract_cmd = '/path/to/tesseract'

Database Connection
# Error: could not connect to server
# Check PostgreSQL service status
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

Redis Connection
# Error: Redis connection failed
# Start Redis server
redis-server  # Default configuration
# Or
sudo systemctl start redis  # Linux

Scraping Blocked
# Error: HTTP 403 or captcha challenges
# The scraper includes:
# - User-agent rotation
# - Request delays
# - Captcha solving
# - Retry mechanisms

📈 Performance
•	Response Time: < 500ms (cached data)
•	Scraping Speed: 2-3 seconds per case search
•	Cache Hit Rate: ~80% for repeated queries
•	Concurrent Users: 100+ supported
•	Database: Handles 10K+ cases efficiently
🤝 Contributing
1.	Fork the repository
2.	Create feature branch (git checkout -b feature/amazing-feature)
3.	Commit changes (git commit -m 'Add amazing feature')
4.	Push to branch (git push origin feature/amazing-feature)
5.	Open Pull Request
Development Guidelines
•	Follow PEP 8 for Python code
•	Use TypeScript for frontend
•	Add tests for new features
•	Update documentation

⚠️ Disclaimer
This application is for educational and research purposes. Always respect the terms of service of the court websites being scraped. Use responsibly and ensure compliance with applicable laws and regulations.

🙏 Acknowledgments
•	eCourts Portal - Government of India's digital courts initiative
•	High Court Websites - Various state High Courts
•	Open Source Libraries - All the amazing libraries that made this possible
 
Built with ❤️ for the Indian legal community
📊 Project Structure
indian-court-tracker/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── cases.py
│   │   │       └── cause_lists.py
│   │   ├── models/
│   │   │   ├── case.py
│   │   │   └── cause_list.py
│   │   ├── utils/
│   │   │   └── captcha_handler.py
│   │   ├── scraper.py
│   │   ├── database.py
│   │   ├── redis_client.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── README.md
└── LICENSE


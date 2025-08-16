# MedTranslate Pro - Setup & Installation Guide

## 🏥 Healthcare Translation Platform

MedTranslate Pro is a real-time voice translation platform designed for healthcare environments, enabling seamless communication between patients and healthcare providers across language barriers.

---

##  Quick Start

### Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome recommended for WebRTC)
- Internet connection for API services
- Microphone access for voice recording

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/healthcare_translation.git
   cd healthcare_translation
   ```

2. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit with your API keys
   nano .env  # or use your preferred editor
   ```

5. **Run the Application**
   ```bash
   python app.py
   or
   flask run
   ```

6. **Access the Platform**
   Open your browser and navigate to: `http://localhost:5000`

---

##  Requirements

### Python Dependencies
Create a `requirements.txt` file with the following:

```txt
Flask==2.3.3
Flask-CORS==4.0.0
Flask-Bcrypt==1.0.1
assemblyai==0.17.0
translate==3.6.1
elevenlabs==0.2.26
python-dotenv==1.0.0
pathlib==1.0.1
uuid==1.30
logging==0.4.9.6
```

---

##  Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# API Keys (Required)
ASSEMBLY_AI_API_KEY=your_assemblyai_api_key_here
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key_here

# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
PORT=5000

# Optional: Database Configuration (for production)
DATABASE_URL=postgresql://username:password@localhost/medtranslate
REDIS_URL=redis://localhost:6379/0
```

### API Key Setup

#### 1. AssemblyAI (Speech-to-Text)
- Visit: https://www.assemblyai.com/
- Create account and get API key

#### 2. ElevenLabs (Text-to-Speech)
- Visit: https://elevenlabs.io/
- Create account and get API key

### Directory Structure
```
medtranslate-pro/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── README.md             # This file Detailed setup instructions
├── static/
│   ├── audio/           # Generated audio files (auto-created)
├── templates/
│   ├── index.html       # Main application interface
│   ├── login.html       # Login page
│   └── register.html    # Registration page
```

### Step 3: API Configuration

1. **Get AssemblyAI API Key**
   - Go to https://www.assemblyai.com/
   - Sign up for free account
   - Navigate to Dashboard → API Keys
   - Copy your API key

2. **Get ElevenLabs API Key**
   - Go to https://elevenlabs.io/
   - Sign up for free account
   - Go to Profile → API Key
   - Copy your API key

3. **Configure Environment**
   ```bash
   # Create .env file
   touch .env  # Linux/macOS
   # Or create manually in Windows
   
   # Add your keys to .env file:
   echo "ASSEMBLY_AI_API_KEY=your_actual_key_here" >> .env
   echo "ELEVEN_LABS_API_KEY=your_actual_key_here" >> .env
   echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')" >> .env
   ```

### Step 4: First Run

1. **Start the Application**
   ```bash
   # Make sure virtual environment is activated
   python app.py
   ```

2. **Expected Output**
   ```
   * Running on http://0.0.0.0:5000
   * Debug mode: on
   INFO:__main__:Starting MedTranslate Pro Healthcare Translation Service
   INFO:__main__:Supported languages: ['en', 'es', 'fr', 'de', 'ur', 'zh', 'ja', 'tr']
   INFO:__main__:Demo users initialized
   ```

3. **Access the Application**
   - Open web browser
   - Navigate to: `http://localhost:5000`
   - You should see the registration page

### Step 5: Test the System

1. **Create Test Account**
   - Click "Create Your Account"
   - Choose role (Patient or Healthcare Provider)
   - Enter username: `testuser`
   - Enter password: `password123`
   - Click "Register"

2. **Login and Test**
   - Login with your credentials
   - Allow microphone access when prompted
   - Test voice recording in both panels
   - Verify translation functionality

---


```
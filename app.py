import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, url_for, session, redirect
from flask_cors import CORS
import assemblyai as aai
from translate import Translator
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from flask_bcrypt import Bcrypt

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Configuration ===
ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY", "abc")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY", "abc")

# Audio storage configuration
STATIC_AUDIO_DIR = Path("static/audio")
STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Flask app initialization
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for API calls
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))  # Use env variable for production
bcrypt = Bcrypt(app)


# In-memory user storage (will reset on each deployment)
USERS_STORAGE = {}

def load_users():
    """Load users from memory storage"""
    return USERS_STORAGE

def save_users(users_dict):
    """Save users to memory storage"""
    global USERS_STORAGE
    USERS_STORAGE.update(users_dict)
    return True

def add_user(username, password, role):
    """Add a new user to storage"""
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_data = {
        'id': str(uuid.uuid4()),
        'username': username,
        'password': hashed_password,
        'role': role,
        'created_at': datetime.now().isoformat()
    }
    
    users[username] = user_data
    save_users(users)
    return True, "User created successfully"

def get_user(username):
    """Get user by username"""
    users = load_users()
    return users.get(username)

def verify_user(username, password):
    """Verify user credentials"""
    user = get_user(username)
    if user and bcrypt.check_password_hash(user['password'], password):
        return user
    return None

# Enhanced language mapping with more languages and proper codes
LANGUAGE_MAPPING = {
    "en": {"name": "English", "voice_id": "pNInz6obpgDQGcFmaJgB"},  # Adam
    "es": {"name": "Spanish", "voice_id": "onwK4e9ZLuTAKqWW03F9"},  # Daniel
    "fr": {"name": "French", "voice_id": "ThT5KcBeYPX3keUQqHPh"},   # Dorothy
    "de": {"name": "German", "voice_id": "TxGEqnHWrfWFTfGW9XjX"},   # Josh
    "ur": {"name": "Urdu", "voice_id": "wBXNqKUATyqu0RtYt25i"},    # Multilingual
    "zh": {"name": "Chinese", "voice_id": "wBXNqKUATyqu0RtYt25i"},  # Multilingual
    "ja": {"name": "Japanese", "voice_id": "wBXNqKUATyqu0RtYt25i"}, # Multilingual
    "tr": {"name": "Turkish", "voice_id": "wBXNqKUATyqu0RtYt25i"},  # Multilingual
}

# Medical terminology enhancement dictionary
MEDICAL_TERMS = {
    "chest pain": {"es": "dolor de pecho", "fr": "douleur thoracique", "de": "Brustschmerzen"},
    "headache": {"es": "dolor de cabeza", "fr": "mal de tête", "de": "Kopfschmerzen"},
    "fever": {"es": "fiebre", "fr": "fièvre", "de": "Fieber"},
    "nausea": {"es": "náuseas", "fr": "nausée", "de": "Übelkeit"},
    "dizziness": {"es": "mareos", "fr": "étourdissements", "de": "Schwindel"},
    "shortness of breath": {"es": "dificultad para respirar", "fr": "essoufflement", "de": "Kurzatmigkeit"},
}

# Session storage for analytics (in production, use Redis or database)
sessions = {}

# === Helper Functions ===

def enhance_medical_terminology(text, target_lang):
    """Enhance translation with medical-specific terminology."""
    enhanced_text = text.lower()
    
    for term, translations in MEDICAL_TERMS.items():
        if term in enhanced_text and target_lang in translations:
            enhanced_text = enhanced_text.replace(term, translations[target_lang])
    
    return enhanced_text

def audio_transcription_with_enhancement(audio_path, from_lang_code=None):
    """Enhanced transcription with medical terminology focus."""
    if not ASSEMBLY_AI_API_KEY:
        raise RuntimeError("AssemblyAI API key not configured")

    aai.settings.api_key = ASSEMBLY_AI_API_KEY
    
    # Enhanced transcription config for medical context
    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best,
        language_detection=True,
        punctuate=True,
        format_text=True,
        dual_channel=False,
        speaker_labels=False,
        # Medical terminology enhancement
        word_boost=["doctor", "patient", "pain", "symptoms", "medication", "treatment"],
        boost_param="high"
    )
    
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)
    
    if transcript.status == aai.TranscriptStatus.error:
        logger.error(f"Transcription error: {transcript.error}")
        raise RuntimeError(f"Transcription failed: {transcript.error}")
    
    # Log confidence scores for monitoring
    if hasattr(transcript, 'confidence'):
        logger.info(f"Transcription confidence: {transcript.confidence}")
    
    return transcript.text or ""

def enhanced_translation(text, from_lang_code, to_lang_code):
    """Enhanced translation with medical terminology and context awareness."""
    try:
        # First, try medical terminology enhancement
        if to_lang_code in ['es', 'fr', 'de']:
            enhanced_text = enhance_medical_terminology(text, to_lang_code)
            if enhanced_text != text.lower():
                return enhanced_text
        
        # Use the translate library for general translation
        translator = Translator(from_lang=from_lang_code, to_lang=to_lang_code)
        translated = translator.translate(text)
        
        logger.info(f"Translated '{text[:50]}...' from {from_lang_code} to {to_lang_code}")
        return translated
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        # Fallback to basic translation
        return f"[Translation Error: {text}]"

def text_to_speech_with_voice_selection(text, target_lang_code):
    """Enhanced TTS with language-specific voice selection."""
    if not ELEVEN_LABS_API_KEY:
        raise RuntimeError("ElevenLabs API key not configured")

    client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)
    
    # Select appropriate voice for language
    voice_config = LANGUAGE_MAPPING.get(target_lang_code, LANGUAGE_MAPPING["en"])
    voice_id = voice_config["voice_id"]
    
    try:
        # Enhanced voice settings for medical context (clearer, more professional)
        response = client.text_to_speech.convert(
            voice_id=voice_id,
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",  # Higher quality audio
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.7,        # More stable for medical terms
                similarity_boost=0.8,
                style=0.3,           # Less stylistic, more neutral
                use_speaker_boost=True,
            ),
        )

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{timestamp}_{uuid.uuid4().hex[:8]}.mp3"
        output_path = STATIC_AUDIO_DIR / filename
        
        # Save audio file
        with open(output_path, "wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)

        # Return URL for frontend
        audio_url = url_for("static", filename=f"audio/{filename}")
        logger.info(f"TTS audio saved: {filename}")
        
        return audio_url

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise RuntimeError(f"Text-to-speech failed: {str(e)}")

def log_session_analytics(session_id, action, data):
    """Log session analytics for monitoring and improvement."""
    if session_id not in sessions:
        sessions[session_id] = {
            "start_time": datetime.now(),
            "actions": [],
            "languages_used": set(),
            "message_count": 0
        }
    
    sessions[session_id]["actions"].append({
        "timestamp": datetime.now(),
        "action": action,
        "data": data
    })
    
    if action == "translation":
        sessions[session_id]["languages_used"].update([data.get("from_lang"), data.get("to_lang")])
        sessions[session_id]["message_count"] += 1

# === Routes ===

@app.route("/")
def index():
    """Serve the registration page as default."""
    return render_template("register.html")

@app.route("/login_page")
def login():
    """Serve the login page."""
    return render_template("login.html")

@app.route("/register_page")
def register():
    """Serve the registration page."""
    return render_template("register.html")

@app.route("/home")
def home():
    """Serve the main application page."""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template("index.html", languages=LANGUAGE_MAPPING)

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user."""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        if not username or not password or not role:
            return jsonify({'error': 'Missing required fields'}), 400

        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
            
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
            
        if role not in ['patient', 'doctor']:
            return jsonify({'error': 'Invalid role selected'}), 400

        success, message = add_user(username, password, role)
        
        if success:
            logger.info(f"New user registered: {username} as {role}")
            return jsonify({'message': 'User registered successfully'}), 201
        else:
            return jsonify({'error': message}), 409

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/login', methods=['POST'])
def login_user():
    """Login a user."""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        user = verify_user(username, password)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            logger.info(f"User logged in: {username} as {user['role']}")
            return jsonify({
                'message': 'Login successful', 
                'redirect': url_for('home'),
                'user': {
                    'username': user['username'],
                    'role': user['role']
                }
            }), 200

        return jsonify({'error': 'Invalid username or password'}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/logout')
def logout():
    """Logout the current user."""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('index'))

@app.route("/translate", methods=["POST"])
def translate_audio():
    """Enhanced translation endpoint with medical terminology support."""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
        
    start_time = datetime.now()
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    
    try:
        # Validate request
        audio_file = request.files.get("audio")
        from_lang = request.form.get("from_lang", "en")
        to_lang = request.form.get("to_lang", "es")
        
        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400
            
        if from_lang not in LANGUAGE_MAPPING or to_lang not in LANGUAGE_MAPPING:
            return jsonify({"error": "Unsupported language pair"}), 400
        
        # Log session analytics
        log_session_analytics(session_id, "translation_request", {
            "from_lang": from_lang,
            "to_lang": to_lang,
            "audio_size": len(audio_file.read()),
            "user": session.get('username')
        })
        audio_file.seek(0)  # Reset file pointer
        
        # Save uploaded audio with better naming
        original_filename = audio_file.filename or "recording"
        file_extension = Path(original_filename).suffix or ".webm"
        temp_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_extension}"
        temp_path = Path(temp_filename)
        
        audio_file.save(temp_path)
        logger.info(f"Audio saved temporarily: {temp_filename}")
        
        try:
            # Step 1: Enhanced transcription
            logger.info("Starting transcription...")
            original_text = audio_transcription_with_enhancement(str(temp_path), from_lang)
            
            if not original_text.strip():
                return jsonify({"error": "No speech detected in audio"}), 400
            
            # Step 2: Enhanced translation
            logger.info(f"Translating text: {original_text[:100]}...")
            translated_text = enhanced_translation(original_text, from_lang, to_lang)
            
            # Step 3: Enhanced text-to-speech
            logger.info("Generating speech...")
            audio_url = None
            try:
                audio_url = text_to_speech_with_voice_selection(translated_text, to_lang)
            except Exception as tts_error:
                logger.warning(f"TTS failed, continuing without audio: {tts_error}")
                # Continue without audio - translation is still valuable
            
            # Log successful translation
            processing_time = (datetime.now() - start_time).total_seconds()
            log_session_analytics(session_id, "translation_success", {
                "from_lang": from_lang,
                "to_lang": to_lang,
                "original_length": len(original_text),
                "translated_length": len(translated_text),
                "processing_time": processing_time,
                "has_audio": audio_url is not None,
                "user": session.get('username')
            })
            
            logger.info(f"Translation completed in {processing_time:.2f}s")
            
            response_data = {
                "original_text": original_text,
                "translated_text": translated_text,
                "audio_url": audio_url,
                "session_id": session_id,
                "processing_time": processing_time,
                "languages": {
                    "from": LANGUAGE_MAPPING[from_lang]["name"],
                    "to": LANGUAGE_MAPPING[to_lang]["name"]
                }
            }
            
            return jsonify(response_data)
            
        finally:
            # Cleanup temporary file
            try:
                temp_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_filename}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup {temp_filename}: {cleanup_error}")
    
    except Exception as e:
        # Log error for monitoring
        log_session_analytics(session_id, "translation_error", {
            "error": str(e),
            "processing_time": (datetime.now() - start_time).total_seconds(),
            "user": session.get('username')
        })
        
        logger.error(f"Translation endpoint error: {e}")
        return jsonify({
            "error": "Translation service temporarily unavailable",
            "details": str(e) if app.debug else None
        }), 500

@app.route("/session/<session_id>/analytics", methods=["GET"])
def get_session_analytics(session_id):
    """Get session analytics for monitoring and improvement."""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
        
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session_data = sessions[session_id]
    analytics = {
        "session_id": session_id,
        "start_time": session_data["start_time"].isoformat(),
        "duration": (datetime.now() - session_data["start_time"]).total_seconds(),
        "message_count": session_data["message_count"],
        "languages_used": list(session_data["languages_used"]),
        "total_actions": len(session_data["actions"])
    }
    
    return jsonify(analytics)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
        "services": {
            "transcription": "AssemblyAI" if ASSEMBLY_AI_API_KEY else "Not configured",
            "translation": "Available",
            "tts": "ElevenLabs" if ELEVEN_LABS_API_KEY else "Not configured"
        },
        "users_count": len(load_users())
    })

@app.route("/languages", methods=["GET"])
def get_supported_languages():
    """Get list of supported languages."""
    return jsonify({
        "languages": {
            code: info["name"] for code, info in LANGUAGE_MAPPING.items()
        },
        "total_supported": len(LANGUAGE_MAPPING)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Initialize demo users for testing
def initialize_demo_users():
    """Initialize some demo users for testing"""
    demo_users = [
        {"username": "patient1", "password": "password123", "role": "patient"},
        {"username": "doctor1", "password": "password123", "role": "doctor"},
    ]
    
    for user_data in demo_users:
        add_user(user_data["username"], user_data["password"], user_data["role"])
    
    logger.info("Demo users initialized")

if __name__ == "__main__":
    # Ensure required directories exist
    STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize demo users
    initialize_demo_users()
    
    # Start the application
    logger.info("Starting MedTranslate Pro Healthcare Translation Service")
    logger.info(f"Supported languages: {list(LANGUAGE_MAPPING.keys())}")
    
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_ENV") == "development"
    )
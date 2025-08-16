# Add to requirements.txt:
# supabase==1.0.4

# Add to your app.py imports:
from supabase import create_client, Client

# Add to configuration section:
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Replace the user storage functions with:

def add_user(username, password, role):
    """Add a new user to Supabase database"""
    try:
        # Check if user exists
        existing_user = supabase.table('users').select("*").eq('username', username).execute()
        if existing_user.data:
            return False, "Username already exists"
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        return True, "User created successfully"
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False, "Registration failed"

def get_user(username):
    """Get user by username from Supabase"""
    try:
        result = supabase.table('users').select("*").eq('username', username).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None

def verify_user(username, password):
    """Verify user credentials"""
    user = get_user(username)
    if user and bcrypt.check_password_hash(user['password'], password):
        return user
    return None

# SQL to create users table in Supabase:
"""
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
"""
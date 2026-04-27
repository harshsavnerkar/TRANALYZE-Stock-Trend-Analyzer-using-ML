import pyrebase
import streamlit as st
import os
from dotenv import load_dotenv
import random
import time
import smtplib
from email.message import EmailMessage

# Load .env relative to this file's location
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# ─────────────────────────────────────────────────
# Firebase Configuration
# ─────────────────────────────────────────────────
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "")
}

# Verification
if not firebase_config["apiKey"] or "YOUR" in firebase_config["apiKey"]:
    st.error("⚠️ Firebase API Key missing. Please check your .env file.")
    st.stop()

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

# Email/SMTP Setup
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # This must be an App Password

def sanitize_key(key):
    """Firebase DB doesn't allow dots or @ in keys. Replace them."""
    return key.replace(".", "_").replace("@", "_")

def handle_auth_error(error):
    """Parse raw Firebase/Pyrebase error and return a clean message."""
    try:
        # The error is often stringified JSON containing [Errno 400...] { "error": { "message": "..." } }
        err_str = str(error)
        
        # Check common keys directly in string to avoid complex JSON parsing overhead
        if "EMAIL_EXISTS" in err_str:
            return "ALREADY REGISTERED: This email is already linked to an account."
        if "INVALID_PASSWORD" in err_str or "WEAK_PASSWORD" in err_str:
            return "INVALID PASSWORD: Password must be at least 6 characters."
        if "EMAIL_NOT_FOUND" in err_str or "USER_NOT_FOUND" in err_str:
            return "USER NOT FOUND: No account linked to this email."
        if "INVALID_LOGIN_CREDENTIALS" in err_str or "INVALID_EMAIL" in err_str:
             return "LOGIN FAILED: Incorrect email or password."
        if "TOO_MANY_ATTEMPTS_TRY_LATER" in err_str:
            return "SECURITY ALERT: Too many failed attempts. Please try again later."
            
        return "ERROR: " + err_str.split('"message": "')[-1].split('"')[0] if '"message": "' in err_str else "An unexpected error occurred."
    except:
        return "Authentication service temporarily unavailable."

def generate_otp(id_to_link, recipient_email):
    """Generate a random 6-digit OTP and send via Gmail SMTP."""
    otp = str(random.randint(100000, 999999))
    timestamp = time.time()
    
    # Sanitize the email address for DB storage
    safe_key = sanitize_key(id_to_link)
    
    # Store in Firebase
    db.child("otps").child(safe_key).set({
        "code": otp,
        "created_at": timestamp
    })
    
    # REAL DELIVERY VIA GMAIL
    try:
        if EMAIL_SENDER and EMAIL_PASSWORD:
            msg = EmailMessage()
            msg.set_content(f"Your TRANALYZE Intelligence Gate verification code is: {otp}\n\nThis code is valid for 5 minutes.")
            msg['Subject'] = f"TRANALYZE OTP: {otp}"
            msg['From'] = EMAIL_SENDER
            msg['To'] = recipient_email

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)
            print(f"Email Sent successfully to {recipient_email}")
    except Exception as e:
        print(f"FAILED TO SEND EMAIL: {str(e)}")
        
    print(f"DEBUG: Real OTP for {id_to_link} is {otp}")
    return otp

def verify_otp_logic(id_to_link, user_input):
    """Check if the user-input OTP matches the DB and hasn't expired."""
    safe_key = sanitize_key(id_to_link)
    stored_otp = db.child("otps").child(safe_key).get().val()
    
    if not stored_otp:
        return {"success": False, "error": "No OTP found."}
    
    # Check expiry (5 minutes = 300 seconds)
    if time.time() - stored_otp["created_at"] > 300:
        return {"success": False, "error": "OTP has expired."}
        
    if str(user_input) == str(stored_otp["code"]):
        return {"success": True}
    else:
        return {"success": False, "error": "Incorrect OTP."}

def save_user_watchlist(uid, watchlist_data):
    """Save the user's specific watchlist to Firebase."""
    try:
        db.child("users").child(uid).child("watchlist").set(watchlist_data)
        return True
    except:
        return False

def load_user_watchlist(uid):
    """Fetch the user's saved symbols from Firebase."""
    try:
        data = db.child("users").child(uid).child("watchlist").get().val()
        return data if data else []
    except:
        return []

def save_portfolio_position(uid, position_data):
    """Save a new trade/position to the user's specific portfolio collection."""
    try:
        # Use push() to generate a unique ID for each position
        db.child("users").child(uid).child("portfolio").push(position_data)
        return True
    except:
        return False

def load_user_portfolio(uid):
    """Fetch all positions (active and closed) for a user."""
    try:
        data = db.child("users").child(uid).child("portfolio").get().val()
        return data if data else {}
    except:
        return {}

def update_portfolio_position(uid, pos_id, update_data):
    """Update a specific position (e.g., closing it with a final price and status)."""
    try:
        db.child("users").child(uid).child("portfolio").child(pos_id).update(update_data)
        return True
    except:
        return False

def signup(email, password, phone, name):
    email = email.lower().strip()
    try:
        user = auth.create_user_with_email_and_password(email, password)
        data = {"name": name, "phone": phone, "email": email}
        db.child("users").child(user['localId']).set(data)
        return {"success": True, "user": user}
    except Exception as e:
        return {"success": False, "error": handle_auth_error(e)}

def login(email, password):
    email = email.lower().strip()
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return {"success": True, "user": user}
    except Exception as e:
        return {"success": False, "error": handle_auth_error(e)}

def reset_password(email):
    email = email.lower().strip()
    try:
        auth.send_password_reset_email(email)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": handle_auth_error(e)}

def get_user_data(uid):
    return db.child("users").child(uid).get().val()

def check_email_exists(email):
    """Refined identity scan based on actual DB structure."""
    search_email = email.lower().strip()
    
    # 1. Targeted DB Query
    try:
        # Use order_by_child for efficiency if it works, otherwise fallback to sweep
        users_query = db.child("users").order_by_child("email").equal_to(search_email).get()
        if users_query.val():
            # Match found via direct query
            for uid in users_query.val():
                return {"exists": True, "uid": uid}
        
        # Fallback Sweep (Manual check)
        all_users = db.child("users").get().val()
        if all_users:
            for uid, data in all_users.items():
                if data.get("email", "").lower().strip() == search_email:
                    return {"exists": True, "uid": uid}
    except Exception as e:
        print(f"DB Search Logic Error: {e}")
        
    # 2. Secure Auth Probing
    try:
        # If we can't find it in the DB, see if Firebase Auth knows it
        auth.sign_in_with_email_and_password(search_email, "DUMMY_pass_to_trigger_check!99")
    except Exception as e:
        err_str = str(e)
        if "INVALID_PASSWORD" in err_str:
            return {"exists": True, "uid": "recovered_via_auth"}
        # Some newer Firebase projects return generic INVALID_LOGIN_CREDENTIALS
        if "INVALID_LOGIN_CREDENTIALS" in err_str:
             # For security, we verify if it might be an existing user
             return {"exists": True, "uid": "recovered_via_auth_generic"}
            
    return {"exists": False}

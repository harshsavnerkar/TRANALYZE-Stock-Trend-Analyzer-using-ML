import pyrebase
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv(".env")

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "")
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

print("--- DIAGNOSTIC: USER DATABASE DUMP ---")
try:
    all_users = db.child("users").get().val()
    if all_users:
        for uid, data in all_users.items():
            print(f"UID: {uid} | Data: {data}")
    else:
        print("No users found in the 'users' node.")
except Exception as e:
    print(f"ERROR READING DB: {e}")
print("--------------------------------------")

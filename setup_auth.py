
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes required for Gmail and Calendar separately
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]

CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

CREDENTIALS_DIR = 'credentials'
GMAIL_CLIENT_SECRET = os.path.join(CREDENTIALS_DIR, 'client_secret_gmail.json')
CALENDAR_CLIENT_SECRET = os.path.join(CREDENTIALS_DIR, 'client_secret_calendar.json')
COMBINED_CLIENT_SECRET = os.path.join(CREDENTIALS_DIR, 'client_secret_for_gmail_and_calender.json')

GMAIL_TOKEN_FILE = os.path.join(CREDENTIALS_DIR, 'token_gmail.pickle')
CALENDAR_TOKEN_FILE = os.path.join(CREDENTIALS_DIR, 'token_calendar.pickle')

def get_client_secret_file(service_name: str) -> str:
    """Helper to determine the client secret path to use."""
    if service_name == 'gmail':
        if os.path.exists(GMAIL_CLIENT_SECRET):
            return GMAIL_CLIENT_SECRET
    elif service_name == 'calendar':
        if os.path.exists(CALENDAR_CLIENT_SECRET):
            return CALENDAR_CLIENT_SECRET
    return COMBINED_CLIENT_SECRET

def authenticate_service(name: str, secret_file: str, token_file: str, scopes: list) -> bool:
    print(f"\n--- Authenticating {name} ---")
    creds = None
    if os.path.exists(token_file):
        print(f"Found existing {name} token at {token_file}")
        with open(token_file, 'rb') as token:
            try:
                creds = pickle.load(token)
            except Exception:
                print("Token file is corrupt/invalid.")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, attempting refresh...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Refresh failed: {e}")
                creds = None
        
        if not creds:
            print(f"Starting new authentication flow for {name}...")
            if not os.path.exists(secret_file):
                print(f"❌ Error: Client secret file not found at {secret_file}")
                return False

            flow = InstalledAppFlow.from_client_secrets_file(secret_file, scopes)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            print(f"✅ Saved new {name} token to {token_file}")
    else:
        print(f"✅ {name} token is valid.")
    return True

if __name__ == '__main__':
    gmail_secret = get_client_secret_file('gmail')
    calendar_secret = get_client_secret_file('calendar')
    
    gmail_success = authenticate_service('Gmail', gmail_secret, GMAIL_TOKEN_FILE, GMAIL_SCOPES)
    calendar_success = authenticate_service('Calendar', calendar_secret, CALENDAR_TOKEN_FILE, CALENDAR_SCOPES)
    
    if gmail_success and calendar_success:
        print("\n🎉 Authentication Complete! You can now restart the bot.")
    else:
        print("\n⚠️ Authentication incomplete. Please check error messages above.")


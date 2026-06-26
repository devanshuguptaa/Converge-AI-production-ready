
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes required for the bot
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

CREDENTIALS_DIR = 'credentials'
CLIENT_SECRET_FILE = os.path.join(CREDENTIALS_DIR, 'client_secret_for_gmail_and_calender.json')
GMAIL_TOKEN_FILE = os.path.join(CREDENTIALS_DIR, 'token_gmail.pickle')
CALENDAR_TOKEN_FILE = os.path.join(CREDENTIALS_DIR, 'token_calendar.pickle')

def authenticate_gmail():
    print(f"\n--- Authenticating Gmail ---")
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        print(f"Found existing Gmail token at {GMAIL_TOKEN_FILE}")
        with open(GMAIL_TOKEN_FILE, 'rb') as token:
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
            print("Starting new authentication flow...")
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(f"❌ Error: Client secret file not found at {CLIENT_SECRET_FILE}")
                return

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(GMAIL_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            print(f"✅ Saved new Gmail token to {GMAIL_TOKEN_FILE}")
    else:
        print("✅ Gmail token is valid.")

    # We reuse the same token for calendar since scopes are combined in this script
    # But usually they might be separate. 
    # For simplicity, if we have one valid token with ALL scopes, we can copy it.
    # However, your original system had separate pickles. Let's just do the flow again or copy if scopes match.
    
    # Actually, simpler: Let's just authenticate ONCE with ALL scopes and save to BOTH files.
    # This simplifies things for the user.
    
    print(f"\n--- Updating Calendar Token ---")
    with open(CALENDAR_TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)
    print(f"✅ Saved Calendar token to {CALENDAR_TOKEN_FILE}")

if __name__ == '__main__':
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ Critical Error: {CLIENT_SECRET_FILE} not found.")
        print("Please ensure you copied the client_secret.json to the correct location.")
    else:
        authenticate_gmail()
        print("\n🎉 Authentication Complete! You can now restart the bot.")

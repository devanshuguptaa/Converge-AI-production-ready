
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(str(Path.cwd()))

try:
    print("1. Checking dependencies...")
    import googleapiclient
    import google_auth_oauthlib
    import google.auth
    print("✅ Google API dependencies installed")
except ImportError as e:
    print(f"❌ Dependency check failed: {e}")
    sys.exit(1)

try:
    print("\n2. Checking credentials files...")
    gmail_secret = Path("credentials/client_secret_gmail.json")
    calendar_secret = Path("credentials/client_secret_calendar.json")
    combined_secret = Path("credentials/client_secret_for_gmail_and_calender.json")
    
    gmail_found = gmail_secret.exists() or combined_secret.exists()
    calendar_found = calendar_secret.exists() or combined_secret.exists()
    
    if gmail_found:
        path_used = gmail_secret if gmail_secret.exists() else combined_secret
        print(f"✅ Gmail client secret found at {path_used}")
    else:
        print(f"❌ Gmail client secret NOT found (expected {gmail_secret} or {combined_secret})")
        
    if calendar_found:
        path_used = calendar_secret if calendar_secret.exists() else combined_secret
        print(f"✅ Calendar client secret found at {path_used}")
    else:
        print(f"❌ Calendar client secret NOT found (expected {calendar_secret} or {combined_secret})")
        
except Exception as e:
    print(f"❌ Error checking credentials: {e}")

try:
    print("\n3. Testing Email Tool Loading...")
    gmail_token = Path("credentials/token_gmail.pickle")
    calendar_token = Path("credentials/token_calendar.pickle")
    
    if not gmail_token.exists() or not calendar_token.exists():
        print("⚠️ Gmail or Calendar token pickle file not found in 'credentials/'.")
        print("👉 Please run 'python setup_auth.py' first to authenticate and generate the token files.")
    else:
        from src.mcp.email_calendar_integration import get_email_calendar_tools
        
        tools = get_email_calendar_tools()
        print(f"✅ Successfully loaded {len(tools)} tools!")
        print("Tool names:")
        for tool in tools:
            print(f"  - {tool.name}")
            
except Exception as e:
    print(f"❌ Failed to load email tools: {e}")
    # Print traceback
    import traceback
    traceback.print_exc()

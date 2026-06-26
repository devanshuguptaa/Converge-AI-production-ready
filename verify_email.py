
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
    print("\n2. Checking credentials file...")
    creds_path = Path("credentials/client_secret_for_gmail_and_calender.json")
    if creds_path.exists():
        print(f"✅ Credentials file found at {creds_path}")
    else:
        print(f"❌ Credentials file NOT found at {creds_path}")
        # Not fatal for tool loading test, but fatal for runtime
except Exception as e:
    print(f"❌ Error checking credentials: {e}")

try:
    print("\n3. Testing Email Tool Loading...")
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

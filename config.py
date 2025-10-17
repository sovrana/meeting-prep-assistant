"""
Configuration module for loading environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Vapi Configuration
VAPI_API_KEY = os.getenv('VAPI_API_KEY')
VAPI_PHONE_NUMBER_ID = os.getenv('VAPI_PHONE_NUMBER_ID')  # Optional - will auto-detect if not provided

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'meeting_prep.db')

# Validation
def validate_config():
    """Validate that required configuration is present."""
    missing = []

    if not VAPI_API_KEY:
        missing.append('VAPI_API_KEY')

    if not ANTHROPIC_API_KEY:
        missing.append('ANTHROPIC_API_KEY')

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please create a .env file based on .env.example and add your API keys."
        )

    return True

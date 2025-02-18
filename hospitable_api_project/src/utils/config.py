# src/utils/config.py
import os
from dotenv import load_dotenv

def load_config():
    # Load .env file if it exists
    load_dotenv()
    
    config = {
        'api_key': os.getenv('API_KEY'),
        'api_secret': os.getenv('API_SECRET'),
        'hospitable_secret': os.getenv('HOSPITABLE_API')
    }
    
    # Validate required environment variables
    missing_vars = [k for k, v in config.items() if v is None]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    return config
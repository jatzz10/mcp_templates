"""
Environment loading utilities

This module handles loading environment variables from .env files.
"""

from pathlib import Path


def load_environment(env_file: str = "mcp.env") -> bool:
    """
    Load environment variables from .env file
    
    Args:
        env_file: Name of the environment file to load
        
    Returns:
        bool: True if environment was loaded successfully, False otherwise
    """
    try:
        from dotenv import load_dotenv
        
        # Load .env file from the same directory as this script
        env_path = Path(__file__).parent.parent / env_file
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from: {env_path}")
            return True
        else:
            print(f"⚠️  Environment file not found: {env_path}")
            return False
            
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"⚠️  Error loading environment file: {e}")
        return False

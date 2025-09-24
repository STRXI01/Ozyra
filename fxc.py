"""
Configuration file for Telegram Auto Forwarder Bot
"""

class Config:
    # Bot credentials (required)
    API_ID: int = 25482744  # Replace with your actual API ID like 12345667 Directly without ""
    API_HASH: str = "e032d6e5c05a5d0bfe691480541d64f4"
    BOT_TOKEN: str = "7051635590:AAEtZg6PMVvaCJSIJHYmu69xbp4nlwSFUoA"
    
    # Target channel/group (required)
    TARGET_CHAT_ID: str = "@BillaNothing"  # Can be a group/channel ID
    
    # Directories
    DOWNLOADS_DIR: str = "./downloads"
    CACHE_FILE: str = "./ffiles.json"
    
    # Default settings
    DEFAULT_INTERVAL: int = 10  # seconds
    MAX_RETRY_ATTEMPTS: int = 2
    
    # Authorized users (as list of integers)
    AUTHORIZED_USERS: list = [5960968099, 1852362865]  # Replace with actual user IDs
    
    # File size limits (in MB)
    MAX_FILE_SIZE_MB: int = 2048
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_fields = [
            cls.API_ID, cls.API_HASH, cls.BOT_TOKEN, 
            cls.TARGET_CHAT_ID, cls.AUTHORIZED_USERS
        ]
        return all(field for field in required_fields)

from pydantic_settings import BaseSettings
from functools import lru_cache
import json
from typing import Optional

class Settings(BaseSettings):
    # MegaAPI
    MEGAAPI_TOKEN: str
    MEGAAPI_INSTANCE_ID: str
    MEGAAPI_HOST: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # LLM APIs
    MISTRAL_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    DEEPSEEK_API_KEY: str
    ANTHROPIC_API_KEY: str
    
    # MCP
    MCP_SERVERS: str
    
    # General
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        
    def get_mcp_servers(self):
        """Parse MCP_SERVERS string into a list of dictionaries"""
        try:
            return json.loads(self.MCP_SERVERS)
        except json.JSONDecodeError:
            return []

@lru_cache()
def get_settings():
    return Settings()
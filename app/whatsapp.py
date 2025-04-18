import requests
from .settings import get_settings
import re

settings = get_settings()

class WhatsAppClient:
    def __init__(self):
        self.base_url = f"https://{settings.MEGAAPI_HOST}"
        self.headers = {
            "Authorization": f"Bearer {settings.MEGAAPI_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def format_message_for_whatsapp(self, message: str) -> str:
        """Formata a mensagem para WhatsApp mantendo emojis e formatação básica"""
        # Mantém emojis como estão
        
        # Converte markdown para formatação WhatsApp
        formatted = message
        # Negrito: **texto** -> *texto*
        formatted = re.sub(r'\*\*(.*?)\*\*', r'*\1*', formatted)
        # Itálico: _texto_ (mantém como está, já é padrão WhatsApp)
        # Listas: - item -> • item
        formatted = re.sub(r'^\s*-\s', '• ', formatted, flags=re.MULTILINE)
        # Numeração: 1. item (mantém como está)
        
        return formatted
    
    async def send_message(self, phone: str, message: str):
        """Envia uma mensagem via WhatsApp"""
        try:
            # Formata a mensagem preservando emojis e formatação
            formatted_message = self.format_message_for_whatsapp(message)
            
            url = f"{self.base_url}/message/sendText/{settings.MEGAAPI_INSTANCE_ID}"
            data = {
                "phone": phone,
                "message": formatted_message
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao enviar mensagem: {str(e)}")
            raise
    
    def process_webhook(self, data: dict):
        """Processa os dados recebidos do webhook"""
        try:
            if data.get("type") == "message":
                return {
                    "phone": data.get("from"),
                    "message": data.get("text"),
                    "timestamp": data.get("timestamp")
                }
            return None
        except Exception as e:
            print(f"Erro ao processar webhook: {str(e)}")
            raise

whatsapp_client = WhatsAppClient() 
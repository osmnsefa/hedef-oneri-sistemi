import os
import logging
from groq import Groq
from src.config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        api_key = Config.GROQ_API_KEY
        if not api_key:
            logger.error("GROQ_API_KEY bulunamadı! Lütfen .env dosyasını kontrol edin.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        
    def generate_response(self, system_prompt, user_prompt, temperature=0.7):
        if not self.client:
            return "⚠️ Hata: Groq API Key eksik. Lütfen .env dosyasını yapılandırın."

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model=Config.MODEL_NAME,
                temperature=temperature,
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API Hatası: {str(e)}")
            return f"⚠️ Groq API Hatası: {str(e)}"

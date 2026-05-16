import os
import logging
from groq import Groq
from src.config import Config

logger = logging.getLogger(__name__)

import streamlit as st

@st.cache_resource
def _get_groq_client(api_key):
    return Groq(api_key=api_key)

class LLMClient:
    def __init__(self):
        api_key = Config.GROQ_API_KEY
        if not api_key:
            logger.error("GROQ_API_KEY bulunamadı! Lütfen .env dosyasını kontrol edin.")
            self.client = None
        else:
            self.client = _get_groq_client(api_key)
        
    def generate_response(self, system_prompt, user_prompt, temperature=0.7, json_mode=False):
        if not self.client:
            return "⚠️ Hata: Groq API Key eksik. Lütfen .env dosyasını yapılandırın."

        try:
            request_params = {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                "model": Config.MODEL_NAME,
                "temperature": temperature,
            }

            if json_mode:
                request_params["response_format"] = {"type": "json_object"}

            chat_completion = self.client.chat.completions.create(**request_params)
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API Hatası: {str(e)}")
            return f"⚠️ Groq API Hatası: {str(e)}"

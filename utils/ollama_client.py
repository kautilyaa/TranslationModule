import os
import requests
import logging
import json
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with Ollama API for OCR and translation."""
    
    def __init__(self):
        """Initialize Ollama client with configuration"""
        # Core configuration
        self.ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.deepl_api_key = os.environ.get("DEEPL_API_KEY")
        
        # Model configuration
        self.ocr_model = os.environ.get("OLLAMA_OCR_MODEL", "llava")
        self.translation_model = os.environ.get("OLLAMA_TRANSLATION_MODEL", "mistral")
        
        # Feature flags
        self.use_openai_fallback = self.openai_api_key is not None
        self.enable_local_ollama = self._parse_boolean_env("ENABLE_LOCAL_OLLAMA", False)
        
        # Settings for model parameters
        self.temperature = float(os.environ.get("OLLAMA_TEMPERATURE", "0.3"))
        self.top_p = float(os.environ.get("OLLAMA_TOP_P", "0.9"))
        self.max_tokens = int(os.environ.get("OLLAMA_MAX_TOKENS", "1000"))
        
        logger.info(f"Initialized Ollama client with OCR model: {self.ocr_model}, Translation model: {self.translation_model}")
        logger.info(f"Local Ollama {'enabled' if self.enable_local_ollama else 'disabled'}")
        if self.use_openai_fallback:
            logger.info("OpenAI fallback is enabled")
        if self.deepl_api_key:
            logger.info("DeepL API key is configured")
            
    def _parse_boolean_env(self, env_var: str, default: bool) -> bool:
        """Parse boolean environment variables safely"""
        val = os.environ.get(env_var, str(default)).lower()
        return val in ("true", "1", "yes", "y", "t")
        
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama API is available."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"Ollama API is not available: {e}")
            return False
            
    def process_image(self, image_path: str) -> str:
        """
        Process image with Ollama vision model for OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        if not self._check_ollama_availability():
            if self.use_openai_fallback:
                return self._process_image_with_openai(image_path)
            else:
                raise Exception("Ollama API is not available and no fallback configured")
        
        try:
            import base64
            
            # Read and encode the image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            base64_image = base64.b64encode(image_data).decode("utf-8")
            
            # Prepare the request payload
            payload = {
                "model": self.ocr_model,
                "prompt": "Extract all text from this image. Return only the extracted text without any commentary or explanation.",
                "images": [base64_image],
                "stream": False
            }
            
            # Make the API request
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}, {response.text}")
                if self.use_openai_fallback:
                    return self._process_image_with_openai(image_path)
                else:
                    raise Exception(f"Failed to process image with Ollama: {response.text}")
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Error processing image with Ollama: {e}")
            if self.use_openai_fallback:
                return self._process_image_with_openai(image_path)
            else:
                raise
    
    def _process_image_with_openai(self, image_path: str) -> str:
        """
        Process image using OpenAI's Vision API as fallback.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        if not self.openai_api_key:
            raise Exception("OpenAI API key not provided for fallback")
        
        try:
            import base64
            
            # Read and encode the image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            base64_image = base64.b64encode(image_data).decode("utf-8")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Return only the extracted text without any commentary."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code}, {response.text}")
                raise Exception(f"Failed to process image with OpenAI: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Error processing image with OpenAI: {e}")
            raise
    
    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text using Ollama model.
        
        Args:
            text: Text to translate
            target_language: Target language code or name
            
        Returns:
            Translated text
        """
        if not self._check_ollama_availability():
            if self.use_openai_fallback:
                return self._translate_with_openai(text, target_language)
            else:
                raise Exception("Ollama API is not available and no fallback configured")
        
        try:
            # Prepare the request payload
            prompt = f"Translate the following text to {target_language}:\n\n{text}\n\nTranslation:"
            
            payload = {
                "model": self.translation_model,
                "prompt": prompt,
                "stream": False
            }
            
            # Make the API request
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}, {response.text}")
                if self.use_openai_fallback:
                    return self._translate_with_openai(text, target_language)
                else:
                    raise Exception(f"Failed to translate with Ollama: {response.text}")
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Error translating with Ollama: {e}")
            if self.use_openai_fallback:
                return self._translate_with_openai(text, target_language)
            else:
                raise
    
    def _translate_with_openai(self, text: str, target_language: str) -> str:
        """
        Translate text using OpenAI API as fallback.
        
        Args:
            text: Text to translate
            target_language: Target language code or name
            
        Returns:
            Translated text
        """
        if not self.openai_api_key:
            raise Exception("OpenAI API key not provided for fallback")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a translator. Translate the user's text to {target_language}. Only respond with the translation, no explanations."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.3
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code}, {response.text}")
                raise Exception(f"Failed to translate with OpenAI: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Error translating with OpenAI: {e}")
            raise

import logging
import os
from typing import Dict, Optional, Tuple, List, Union
from deep_translator import GoogleTranslator, LingueeTranslator, MyMemoryTranslator
from deep_translator import PonsTranslator, DeeplTranslator  # DeeplTranslator is the correct import

logger = logging.getLogger(__name__)

# Language codes mapping (ISO 639-1)
LANGUAGE_CODES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'ko': 'Korean',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'fi': 'Finnish',
    'tr': 'Turkish',
    'pl': 'Polish',
    'cs': 'Czech',
    'da': 'Danish',
    'he': 'Hebrew',
    'hu': 'Hungarian',
    'no': 'Norwegian',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'uk': 'Ukrainian',
    'ro': 'Romanian',
    'fa': 'Persian',
    'el': 'Greek',
    'bg': 'Bulgarian'
}

# Translation providers
TRANSLATION_PROVIDERS = {
    'ollama': 'Ollama (Local AI)',
    'openai': 'OpenAI',
    'google': 'Google Translate',
    'deepl': 'DeepL',
    'mymemory': 'MyMemory',
    'linguee': 'Linguee',
    'pons': 'Pons'
}

# Provider-specific language support
# Some providers don't support all languages
PROVIDER_LANGUAGE_SUPPORT = {
    'pons': ['en', 'de', 'fr', 'es', 'it', 'pt', 'ru'],
    'linguee': ['en', 'de', 'fr', 'es', 'it', 'pt', 'ja', 'zh', 'ru', 'nl', 'sv', 'pl', 'da'],
    'deepl': ['en', 'de', 'fr', 'es', 'it', 'pt', 'ru', 'ja', 'zh', 'nl', 'pl']
}

def translate_text(text: str, target_language: str, ollama_client, provider: str = 'ollama') -> str:
    """
    Translate text to the target language using selected provider.
    
    Args:
        text: The text to translate
        target_language: The language code or name to translate to
        ollama_client: Instance of OllamaClient (for Ollama/OpenAI)
        provider: The translation provider to use
        
    Returns:
        The translated text
    """
    try:
        # Normalize target language
        target_language = _normalize_language_code(target_language)
        
        # Get language name for better prompting
        language_name = LANGUAGE_CODES.get(target_language, target_language)
        
        # Log translation request
        logger.info(f"Translating text ({len(text)} chars) to {language_name} using {provider}")
        
        # Check if provider supports this language
        if provider in PROVIDER_LANGUAGE_SUPPORT:
            if target_language not in PROVIDER_LANGUAGE_SUPPORT[provider]:
                logger.warning(f"{provider} doesn't support {language_name}, falling back to Google Translate")
                provider = 'google'
        
        # Perform translation based on provider
        if provider == 'ollama':
            translated_text = ollama_client.translate(text, language_name)
        elif provider == 'openai':
            translated_text = ollama_client._translate_with_openai(text, language_name)
        elif provider == 'google':
            translator = GoogleTranslator(source='auto', target=target_language)
            translated_text = translator.translate(text)
        elif provider == 'deepl':
            # DeepL requires an API key
            deepl_api_key = os.environ.get('DEEPL_API_KEY')
            if not deepl_api_key:
                logger.warning("DeepL API key not found, falling back to Google Translate")
                translator = GoogleTranslator(source='auto', target=target_language)
                translated_text = translator.translate(text)
            else:
                translator = DeeplTranslator(api_key=deepl_api_key, source='auto', target=target_language)
                translated_text = translator.translate(text)
        elif provider == 'mymemory':
            # MyMemory has daily limits but works without API key
            translator = MyMemoryTranslator(source='auto', target=target_language)
            translated_text = translator.translate(text)
        elif provider == 'linguee':
            # Linguee has limitations on length
            if len(text) > 500:
                logger.warning("Text too long for Linguee (>500 chars), falling back to Google Translate")
                translator = GoogleTranslator(source='auto', target=target_language)
                translated_text = translator.translate(text)
            else:
                translator = LingueeTranslator(source='auto', target=target_language)
                translated_text = translator.translate(text)
        elif provider == 'pons':
            # Pons has severe limitations on length
            if len(text) > 200:
                logger.warning("Text too long for Pons (>200 chars), falling back to Google Translate")
                translator = GoogleTranslator(source='auto', target=target_language)
                translated_text = translator.translate(text)
            else:
                translator = PonsTranslator(source='auto', target=target_language)
                translated_text = translator.translate(text)
        else:
            # Default to Google Translate as fallback
            translator = GoogleTranslator(source='auto', target=target_language)
            translated_text = translator.translate(text)
        
        # Make sure we return a string (some translators might return different types)
        if translated_text is None:
            return ""
        if isinstance(translated_text, list):
            return " ".join(translated_text)
        
        return str(translated_text).strip()
        
    except Exception as e:
        logger.error(f"Translation error with {provider}: {e}")
        # If the selected provider fails, try Google Translate as fallback
        if provider != 'google':
            logger.info(f"Falling back to Google Translate after {provider} failed")
            try:
                translator = GoogleTranslator(source='auto', target=target_language)
                return translator.translate(text).strip()
            except Exception as e2:
                logger.error(f"Google Translate fallback also failed: {e2}")
                raise
        else:
            raise

def get_supported_languages(provider: str = '') -> Dict[str, str]:
    """
    Get dictionary of supported languages, filtered by provider if specified.
    
    Args:
        provider: Optional filter by translation provider
    
    Returns:
        Dictionary of language codes and names
    """
    if not provider or provider not in PROVIDER_LANGUAGE_SUPPORT:
        return LANGUAGE_CODES
    
    # Filter languages by provider support
    supported_langs = {code: name for code, name in LANGUAGE_CODES.items() 
                      if code in PROVIDER_LANGUAGE_SUPPORT[provider]}
    return supported_langs

def get_providers() -> Dict[str, str]:
    """
    Get dictionary of available translation providers.
    
    Returns:
        Dictionary of provider IDs and display names
    """
    return TRANSLATION_PROVIDERS

def _normalize_language_code(lang_code: str) -> str:
    """
    Normalize language code or name to a standard code.
    
    Args:
        lang_code: Language code or name
        
    Returns:
        Normalized language code
    """
    # If it's already a valid code, return it
    if lang_code.lower() in LANGUAGE_CODES:
        return lang_code.lower()
    
    # Check if it's a language name
    for code, name in LANGUAGE_CODES.items():
        if name.lower() == lang_code.lower():
            return code
    
    # If no match, return as is
    return lang_code.lower()

def detect_language(text: str, ollama_client) -> Tuple[str, float]:
    """
    Detect the language of the provided text.
    
    Args:
        text: The text to analyze
        ollama_client: Instance of OllamaClient
        
    Returns:
        Tuple containing (language_code, confidence)
    """
    try:
        # Try using DeepTranslator methods for detection
        try:
            # Google Translate doesn't have direct language detection in deep_translator
            # Use alternative approach
            
            # Try translating with auto-detect and inspect result
            translator = GoogleTranslator(source='auto', target='en')
            # Get detected language by translating a short sample
            sample = text[:100]  # Use just a short sample for efficiency
            _ = translator.translate(sample)
            detected_source = translator.source
            
            # Check if detected code is in our supported languages
            if detected_source in LANGUAGE_CODES:
                return detected_source, 0.95  # Very high confidence
            
            # Normalize Chinese variants
            if detected_source == 'zh':
                return 'zh-CN', 0.95
                
            return detected_source, 0.8  # Good confidence for other detected languages
            
        except Exception as e:
            logger.warning(f"Google language detection failed: {e}, falling back to Ollama")
            
        # Fall back to Ollama-based detection
        prompt = f"Identify the language of the following text. Respond with only the ISO 639-1 language code and nothing else:\n\n{text[:200]}"
        
        # Get language prediction from Ollama
        response = ollama_client.translate(prompt, "English")
        
        # Extract language code from response
        lang_code = response.strip().lower()
        
        # Check if response is a valid language code
        if lang_code in LANGUAGE_CODES:
            return lang_code, 0.9  # High confidence if exact match
        
        # Try to map to a valid language code
        for code in LANGUAGE_CODES:
            if code in lang_code or LANGUAGE_CODES[code].lower() in lang_code.lower():
                return code, 0.7  # Medium confidence for partial match
        
        return "unknown", 0.0
        
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return "unknown", 0.0

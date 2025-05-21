import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import tempfile
from utils.ollama_client import OllamaClient
from utils.ocr import process_image
from utils.translator import translate_text

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
TEMP_FOLDER = tempfile.gettempdir()

# Initialize Ollama client
ollama_client = OllamaClient()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(TEMP_FOLDER, filename)
        file.save(filepath)
        
        try:
            extracted_text = process_image(filepath, ollama_client)
            os.remove(filepath)  # Clean up temp file
            return jsonify({'text': extracted_text})
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)  # Ensure temp file is cleaned up
            return jsonify({'error': f'OCR processing failed: {str(e)}'}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    if not data or 'text' not in data or 'target_language' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    text = data['text']
    target_language = data['target_language']
    provider = data.get('provider', 'ollama')  # Default to Ollama if not specified
    
    if not text or not target_language:
        return jsonify({'error': 'Text and target language cannot be empty'}), 400
    
    try:
        translated_text = translate_text(text, target_language, ollama_client, provider)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        logger.error(f"Translation error with provider {provider}: {e}")
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    from utils.translator import get_supported_languages
    
    provider = request.args.get('provider', '')
    languages = get_supported_languages(provider)
    return jsonify(languages)

@app.route('/api/providers', methods=['GET'])
def get_providers():
    from utils.translator import get_providers
    
    providers = get_providers()
    return jsonify(providers)

@app.route('/api/config/ollama', methods=['GET', 'POST'])
def configure_ollama():
    if request.method == 'GET':
        # Return current Ollama configuration
        config = {
            'ollama_base_url': ollama_client.ollama_base_url,
            'ocr_model': ollama_client.ocr_model,
            'translation_model': ollama_client.translation_model,
            'enable_local_ollama': ollama_client.enable_local_ollama,
            'temperature': ollama_client.temperature,
            'top_p': ollama_client.top_p,
            'max_tokens': ollama_client.max_tokens
        }
        return jsonify(config)
    else:
        # Update Ollama configuration
        data = request.json
        if not data:
            return jsonify({'error': 'No configuration data provided'}), 400
        
        try:
            # Update configuration
            if 'ollama_base_url' in data:
                ollama_client.ollama_base_url = data['ollama_base_url']
            
            if 'ocr_model' in data:
                ollama_client.ocr_model = data['ocr_model']
                
            if 'translation_model' in data:
                ollama_client.translation_model = data['translation_model']
                
            if 'enable_local_ollama' in data:
                ollama_client.enable_local_ollama = bool(data['enable_local_ollama'])
                
            if 'temperature' in data:
                ollama_client.temperature = float(data['temperature'])
                
            if 'top_p' in data:
                ollama_client.top_p = float(data['top_p'])
                
            if 'max_tokens' in data:
                ollama_client.max_tokens = int(data['max_tokens'])
            
            # Log changes
            logger.info(f"Updated Ollama configuration: OCR model: {ollama_client.ocr_model}, " 
                      f"Translation model: {ollama_client.translation_model}, "
                      f"Local Ollama: {'enabled' if ollama_client.enable_local_ollama else 'disabled'}")
            
            return jsonify({'message': 'Configuration updated successfully'})
            
        except Exception as e:
            logger.error(f"Error updating Ollama configuration: {e}")
            return jsonify({'error': f'Configuration update failed: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

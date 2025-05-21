document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const extractedTextArea = document.getElementById('extracted-text');
    const translationForm = document.getElementById('translation-form');
    const sourceTextArea = document.getElementById('source-text');
    const translatedTextArea = document.getElementById('translated-text');
    const languageSelect = document.getElementById('language-select');
    const providerSelect = document.getElementById('provider-select');
    const uploadSpinner = document.getElementById('upload-spinner');
    const translateSpinner = document.getElementById('translate-spinner');
    const ocrAlert = document.getElementById('ocr-alert');
    const translateAlert = document.getElementById('translate-alert');
    const copyExtractedBtn = document.getElementById('copy-extracted');
    const copyTranslatedBtn = document.getElementById('copy-translated');
    const useExtractedBtn = document.getElementById('use-extracted');
    
    // Settings elements
    const saveSettingsBtn = document.getElementById('save-settings');
    const enableLocalOllama = document.getElementById('enable-local-ollama');
    const ollamaBaseUrl = document.getElementById('ollama-base-url');
    const ocrModel = document.getElementById('ocr-model');
    const translationModel = document.getElementById('translation-model');
    const temperature = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    const topP = document.getElementById('top-p');
    const topPValue = document.getElementById('top-p-value');
    const maxTokens = document.getElementById('max-tokens');
    const openaiApiKey = document.getElementById('openai-api-key');
    const deeplApiKey = document.getElementById('deepl-api-key');
    const ollamaSettingsAlert = document.getElementById('ollama-settings-alert');
    const apiKeysAlert = document.getElementById('api-keys-alert');
    
    // Fetch data
    fetchLanguages();
    fetchProviders();
    fetchOllamaConfig();
    
    // Event listeners
    uploadForm.addEventListener('submit', handleImageUpload);
    translationForm.addEventListener('submit', handleTranslation);
    copyExtractedBtn.addEventListener('click', () => copyToClipboard(extractedTextArea));
    copyTranslatedBtn.addEventListener('click', () => copyToClipboard(translatedTextArea));
    useExtractedBtn.addEventListener('click', useExtractedText);
    
    // Provider change event - update language options
    providerSelect.addEventListener('change', () => {
        fetchLanguages(providerSelect.value);
    });
    
    // Settings event listeners
    saveSettingsBtn.addEventListener('click', saveSettings);
    temperature.addEventListener('input', () => {
        temperatureValue.textContent = temperature.value;
    });
    topP.addEventListener('input', () => {
        topPValue.textContent = topP.value;
    });
    
    // Handle file upload and OCR
    function handleImageUpload(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showAlert(ocrAlert, 'Please select a file to upload', 'danger');
            return;
        }
        
        // Check file type
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            showAlert(ocrAlert, 'Please upload a PNG, JPG, or PDF file', 'danger');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Show loading spinner
        uploadSpinner.classList.remove('d-none');
        extractedTextArea.value = '';
        hideAlert(ocrAlert);
        
        fetch('/api/ocr', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'OCR processing failed');
                });
            }
            return response.json();
        })
        .then(data => {
            extractedTextArea.value = data.text;
            showAlert(ocrAlert, 'Text extracted successfully!', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert(ocrAlert, error.message, 'danger');
        })
        .finally(() => {
            uploadSpinner.classList.add('d-none');
        });
    }
    
    // Handle text translation
    function handleTranslation(e) {
        e.preventDefault();
        
        const text = sourceTextArea.value.trim();
        const targetLanguage = languageSelect.value;
        const provider = providerSelect.value;
        
        if (!text) {
            showAlert(translateAlert, 'Please enter text to translate', 'danger');
            return;
        }
        
        // Show loading spinner
        translateSpinner.classList.remove('d-none');
        translatedTextArea.value = '';
        hideAlert(translateAlert);
        
        fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                target_language: targetLanguage,
                provider: provider
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Translation failed');
                });
            }
            return response.json();
        })
        .then(data => {
            translatedTextArea.value = data.translated_text;
            showAlert(translateAlert, 'Text translated successfully!', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert(translateAlert, error.message, 'danger');
        })
        .finally(() => {
            translateSpinner.classList.add('d-none');
        });
    }
    
    // Fetch supported languages
    function fetchLanguages(provider = '') {
        let url = '/api/languages';
        if (provider) {
            url += `?provider=${provider}`;
        }
        
        fetch(url)
        .then(response => response.json())
        .then(languages => {
            languageSelect.innerHTML = '';
            Object.entries(languages).forEach(([code, name]) => {
                const option = document.createElement('option');
                option.value = code;
                option.textContent = name;
                languageSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching languages:', error);
        });
    }
    
    // Fetch available translation providers
    function fetchProviders() {
        fetch('/api/providers')
        .then(response => response.json())
        .then(providers => {
            providerSelect.innerHTML = '';
            Object.entries(providers).forEach(([id, name]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = name;
                if (id === 'ollama') {
                    option.selected = true;
                }
                providerSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching providers:', error);
        });
    }
    
    // Fetch Ollama configuration
    function fetchOllamaConfig() {
        fetch('/api/config/ollama')
        .then(response => response.json())
        .then(config => {
            // Populate form fields with current configuration
            enableLocalOllama.checked = config.enable_local_ollama;
            ollamaBaseUrl.value = config.ollama_base_url;
            ocrModel.value = config.ocr_model;
            translationModel.value = config.translation_model;
            temperature.value = config.temperature;
            temperatureValue.textContent = config.temperature;
            topP.value = config.top_p;
            topPValue.textContent = config.top_p;
            maxTokens.value = config.max_tokens;
        })
        .catch(error => {
            console.error('Error fetching Ollama config:', error);
            showAlert(ollamaSettingsAlert, 'Failed to load Ollama configuration', 'danger');
        });
    }
    
    // Save settings
    function saveSettings() {
        // Save Ollama settings
        const ollamaConfig = {
            enable_local_ollama: enableLocalOllama.checked,
            ollama_base_url: ollamaBaseUrl.value,
            ocr_model: ocrModel.value,
            translation_model: translationModel.value,
            temperature: parseFloat(temperature.value),
            top_p: parseFloat(topP.value),
            max_tokens: parseInt(maxTokens.value)
        };
        
        fetch('/api/config/ollama', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ollamaConfig)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            showAlert(ollamaSettingsAlert, 'Ollama settings saved successfully!', 'success');
        })
        .catch(error => {
            console.error('Error saving Ollama settings:', error);
            showAlert(ollamaSettingsAlert, error.message, 'danger');
        });
        
        // Handle API key update via environment variables
        // Note: In a production environment, this would be handled through a proper secure method
        // For now, we'll just show a message that API keys would be saved
        if (openaiApiKey.value || deeplApiKey.value) {
            showAlert(apiKeysAlert, 'API keys would be securely saved in a production environment.', 'info');
        }
    }
    
    // Helper functions
    function showAlert(element, message, type) {
        element.textContent = message;
        element.className = `alert alert-${type}`;
        element.classList.remove('d-none');
    }
    
    function hideAlert(element) {
        element.classList.add('d-none');
    }
    
    function copyToClipboard(textArea) {
        if (!textArea.value) return;
        
        textArea.select();
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
        
        // Show temporary success message
        const btn = textArea === extractedTextArea ? copyExtractedBtn : copyTranslatedBtn;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    }
    
    function useExtractedText() {
        if (extractedTextArea.value) {
            sourceTextArea.value = extractedTextArea.value;
            // Scroll to translation section
            document.getElementById('translation-section').scrollIntoView({ behavior: 'smooth' });
        }
    }
});

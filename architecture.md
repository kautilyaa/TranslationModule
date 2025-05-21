# RAG Translator with OCR - Architecture

This document outlines the detailed architecture of the RAG Translator with OCR application.

## System Components

```mermaid
graph TD
    subgraph "Client Layer"
        Browser[Web Browser]
        Browser -->|HTTP/HTTPS| WebApp
    end

    subgraph "Application Layer"
        WebApp[Flask Web Application]
        WebApp -->|File Upload| OCRProcessor
        WebApp -->|Text| TranslationEngine
        WebApp -->|Configuration| ConfigManager
    end

    subgraph "Processing Layer"
        OCRProcessor[OCR Processing]
        TranslationEngine[Translation Engine]
        ConfigManager[Configuration Manager]
        
        OCRProcessor -->|Image Processing| Tesseract[Tesseract OCR]
        OCRProcessor -->|PDF Conversion| Poppler[Poppler Utils]
        OCRProcessor -->|Vision AI| AIModels
        
        TranslationEngine -->|Language Detection| LanguageDetector
        TranslationEngine -->|Text Translation| Providers
    end

    subgraph "AI Models & Services"
        AIModels[AI Vision Models]
        AIModels -->|Local| Ollama[Ollama Models]
        AIModels -->|Cloud| OpenAI[OpenAI Vision]
        
        Providers[Translation Providers]
        Providers -->|Local AI| OllamaTranslation[Ollama]
        Providers -->|API| GoogleTranslate[Google Translate]
        Providers -->|API| DeepL[DeepL]
        Providers -->|API| MyMemory[MyMemory]
        Providers -->|API| Linguee[Linguee]
        Providers -->|API| Pons[Pons]
        Providers -->|API| OpenAITranslation[OpenAI]
        
        LanguageDetector[Language Detection]
        LanguageDetector -->|API| GoogleDetect[Google Detection]
        LanguageDetector -->|Local| OllamaDetect[Ollama Detection]
    end
```

## Data Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser as Web Browser
    participant WebApp as Flask Application
    participant OCR as OCR Processor
    participant Trans as Translation Engine
    participant AI as AI Models
    participant ExtAPI as External APIs

    User->>Browser: Upload Image/PDF
    Browser->>WebApp: POST /api/ocr
    WebApp->>OCR: Process file
    OCR->>AI: Extract text (if Ollama available)
    AI-->>OCR: Return extracted text
    alt Ollama not available
        OCR->>ExtAPI: Process with OpenAI (if configured)
        ExtAPI-->>OCR: Return extracted text
    end
    OCR-->>WebApp: Return extracted text
    WebApp-->>Browser: Display text to user
    
    User->>Browser: Request translation
    Browser->>WebApp: POST /api/translate
    WebApp->>Trans: Translate text
    alt Using Ollama
        Trans->>AI: Process translation
        AI-->>Trans: Return translated text
    else Using external provider
        Trans->>ExtAPI: Call translation API
        ExtAPI-->>Trans: Return translated text
    end
    Trans-->>WebApp: Return translation
    WebApp-->>Browser: Display translation to user
    
    User->>Browser: Configure settings
    Browser->>WebApp: POST /api/config/ollama
    WebApp->>WebApp: Update configuration
    WebApp-->>Browser: Confirm settings updated
```

## Component Details

### Client Layer
- **Web Browser**: The user interface built with HTML, CSS (Bootstrap), and JavaScript

### Application Layer
- **Flask Web Application**: Core web server handling HTTP requests
- **Gunicorn**: WSGI HTTP server for deployment

### Processing Layer
- **OCR Processing**: Extracts text from images and PDFs
  - Uses Tesseract, Poppler, and AI vision models
- **Translation Engine**: Handles text translation using multiple providers
- **Configuration Manager**: Handles application settings and API keys

### AI Models & External Services
- **Ollama**: Local AI models for OCR and translation
- **OpenAI**: Cloud-based models for OCR and translation (fallback)
- **Translation Providers**: Multiple services for text translation
  - Google Translate, DeepL, MyMemory, Linguee, Pons

## System Requirements

```mermaid
flowchart TD
    subgraph "Software Requirements"
        Python[Python 3.11+]
        Flask[Flask Framework]
        Tesseract[Tesseract OCR]
        Poppler[Poppler Utils]
        Ollama[Ollama Local Models]
    end
    
    subgraph "Hardware Recommendations"
        CPU[CPU: 4+ cores]
        RAM[RAM: 8GB+ minimum]
        Storage[Storage: 10GB+ for models]
        GPU[GPU: Optional for better Ollama performance]
    end
    
    subgraph "Network Requirements"
        Internet[Internet Connection]
        Ports[Port 5000 for web app]
        OllamaPort[Port 11434 for Ollama]
    end
```

## Deployment Architecture

```mermaid
flowchart LR
    subgraph "Docker Environment"
        WebApp[Web Application Container]
        Ollama[Ollama Container]
        
        WebApp -->|HTTP API| Ollama
    end
    
    Client[Web Browser] -->|HTTP/5000| WebApp
    Admin[Administrator] -->|HTTP/11434| Ollama
```
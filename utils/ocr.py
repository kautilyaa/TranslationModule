import os
import logging
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from typing import List, Optional
import tempfile

logger = logging.getLogger(__name__)

def process_image(file_path: str, ollama_client) -> str:
    """
    Process an image or PDF file to extract text using OCR.
    
    This function handles both image files (JPEG, PNG) and PDF files.
    It uses pytesseract for preprocessing and enhancement, then Ollama for actual OCR.
    
    Args:
        file_path: Path to the image or PDF file
        ollama_client: Instance of OllamaClient to use for OCR
        
    Returns:
        str: Extracted text from the image
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # Handle PDF files
        if file_extension == '.pdf':
            return process_pdf(file_path, ollama_client)
        
        # Handle image files
        return process_single_image(file_path, ollama_client)
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        raise
        
def process_pdf(pdf_path: str, ollama_client) -> str:
    """
    Extract text from a PDF file by converting pages to images and performing OCR.
    
    Args:
        pdf_path: Path to the PDF file
        ollama_client: Instance of OllamaClient to use for OCR
        
    Returns:
        str: Extracted text from all pages of the PDF
    """
    try:
        # Create a temporary directory for storing image files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            all_text = []
            
            # Process each page
            for i, image in enumerate(images):
                # Save image temporarily
                img_path = os.path.join(temp_dir, f'page_{i}.jpg')
                image.save(img_path, 'JPEG')
                
                # Process the image and extract text
                page_text = process_single_image(img_path, ollama_client)
                all_text.append(page_text)
                
                # Clean up temporary image file
                os.remove(img_path)
            
            # Combine text from all pages
            return "\n\n".join(all_text)
    
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        raise

def process_single_image(image_path: str, ollama_client) -> str:
    """
    Process a single image file to extract text using OCR.
    
    This function performs preprocessing to enhance image quality,
    then uses Ollama for the actual OCR.
    
    Args:
        image_path: Path to the image file
        ollama_client: Instance of OllamaClient to use for OCR
        
    Returns:
        str: Extracted text from the image
    """
    try:
        # Open and preprocess the image
        image = Image.open(image_path)
        
        # Convert to RGB if image has alpha channel
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # Perform preprocessing to improve OCR accuracy
        # - Resize if needed
        # - Enhance contrast
        # - Apply mild filtering for noise reduction
        
        # If image is very small or very large, resize to a reasonable size
        max_dimension = max(image.width, image.height)
        if max_dimension > 3000:
            scale_factor = 3000 / max_dimension
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Save preprocessed image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            preprocessed_path = tmp_file.name
            image.save(preprocessed_path, 'JPEG', quality=95)
        
        try:
            # Use Ollama for OCR
            extracted_text = ollama_client.process_image(preprocessed_path)
            
            # If Ollama returns empty or too short result, fallback to Tesseract
            if not extracted_text or len(extracted_text) < 10:
                logger.info("Ollama OCR result too short, falling back to Tesseract")
                extracted_text = pytesseract.image_to_string(image)
            
            return extracted_text.strip()
        
        finally:
            # Clean up temporary file
            os.unlink(preprocessed_path)
    
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        raise

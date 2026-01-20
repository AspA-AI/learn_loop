"""
Document processing utilities for chunking and preparing documents for vector storage.
"""
import logging
import PyPDF2
import io
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from plain text file"""
    try:
        return file_content.decode('utf-8').strip()
    except UnicodeDecodeError:
        try:
            return file_content.decode('latin-1').strip()
        except Exception as e:
            logger.error(f"Error decoding text file: {e}")
            raise ValueError(f"Failed to decode text file: {str(e)}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks with overlap.
    Uses token-aware chunking (approximate).
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # Simple character-based chunking (can be improved with tiktoken for token-aware)
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < text_length:
            # Look for sentence endings near the end
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.7:  # Only break if we're past 70% of chunk
                chunk = text[start:start + break_point + 1]
                start = start + break_point + 1 - overlap
            else:
                start = end - overlap
        else:
            start = end
        
        if chunk.strip():
            chunks.append(chunk.strip())
    
    return chunks

def process_document(file_content: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Process a document (PDF or text) and return chunks with metadata.
    Returns list of chunks, each with content and metadata.
    """
    file_ext = Path(file_name).suffix.lower()
    
    # Extract text based on file type
    if file_ext == '.pdf':
        text = extract_text_from_pdf(file_content)
    elif file_ext in ['.txt', '.md']:
        text = extract_text_from_txt(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Supported: .pdf, .txt, .md")
    
    if not text or len(text.strip()) == 0:
        raise ValueError("Document appears to be empty or could not extract text")
    
    # Chunk the text
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    
    if not chunks:
        raise ValueError("No chunks created from document")
    
    # Create chunk metadata
    chunk_objects = []
    for i, chunk in enumerate(chunks):
        chunk_objects.append({
            "content": chunk,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "source_file": file_name
        })
    
    logger.info(f"Processed {file_name}: {len(chunks)} chunks created")
    return chunk_objects


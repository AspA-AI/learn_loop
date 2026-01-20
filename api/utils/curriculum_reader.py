"""
Utility to read curriculum files for children.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.document_processor import extract_text_from_pdf, extract_text_from_txt

logger = logging.getLogger(__name__)

def read_curriculum_files(curriculum_files: List[Dict[str, Any]]) -> Optional[str]:
    """
    Read all curriculum files for a child and return combined text content.
    Returns None if no files or if all files fail to read.
    """
    if not curriculum_files:
        return None
    
    combined_content = []
    
    for file_info in curriculum_files:
        storage_path = file_info.get("storage_path")
        file_name = file_info.get("file_name")
        
        if not storage_path:
            logger.warning(f"Curriculum file {file_name} has no storage_path, skipping")
            continue
        
        try:
            # Read file from local storage
            file_path = Path(storage_path)
            if not file_path.exists():
                logger.warning(f"Curriculum file not found: {file_path}")
                continue
            
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Extract text based on file type
            file_ext = file_path.suffix.lower()
            if file_ext == '.pdf':
                text = extract_text_from_pdf(file_content)
            elif file_ext in ['.txt', '.md']:
                text = extract_text_from_txt(file_content)
            else:
                logger.warning(f"Unsupported curriculum file type: {file_ext} for {file_name}")
                continue
            
            if text and text.strip():
                combined_content.append(f"[Curriculum: {file_name}]\n{text.strip()}")
                logger.info(f"Successfully read curriculum file: {file_name} ({len(text)} chars)")
            else:
                logger.warning(f"Curriculum file {file_name} appears to be empty")
                
        except Exception as e:
            logger.error(f"Error reading curriculum file {file_name}: {e}", exc_info=True)
            continue
    
    if combined_content:
        return "\n\n---\n\n".join(combined_content)
    
    return None


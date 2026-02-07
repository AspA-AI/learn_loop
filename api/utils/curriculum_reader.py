"""
Utility to read curriculum files for children.
Supports both Supabase Storage (cloud) and local filesystem (fallback).
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.document_processor import extract_text_from_pdf, extract_text_from_txt

logger = logging.getLogger(__name__)

# Import supabase service for cloud storage access
try:
    from services.supabase_service import supabase_service
except ImportError:
    supabase_service = None
    logger.warning("Supabase service not available for curriculum reading")

def read_curriculum_files(curriculum_files: List[Dict[str, Any]]) -> Optional[str]:
    """
    Read all curriculum files for a child and return combined text content.
    Returns None if no files or if all files fail to read.
    """
    if not curriculum_files:
        logger.info("📖 [CURRICULUM READER] No curriculum files provided")
        return None
    
    logger.info(f"📖 [CURRICULUM READER] Attempting to read {len(curriculum_files)} curriculum files")
    combined_content = []
    
    for file_info in curriculum_files:
        storage_path = file_info.get("storage_path")
        file_name = file_info.get("file_name")
        
        logger.info(f"📖 [CURRICULUM READER] Processing file: {file_name} (path: {storage_path})")
        
        if not storage_path:
            logger.warning(f"⚠️ [CURRICULUM READER] Curriculum file {file_name} has no storage_path, skipping")
            continue
        
        try:
            file_content: Optional[bytes] = None
            
            # Check if storage_path indicates Supabase Storage (format: "supabase://bucket/path")
            if storage_path.startswith("supabase://"):
                # Extract bucket and path
                parts = storage_path.replace("supabase://", "").split("/", 1)
                if len(parts) == 2:
                    bucket_name, file_path_in_bucket = parts
                    try:
                        if supabase_service:
                            file_content = supabase_service.get_file_from_storage(bucket_name, file_path_in_bucket)
                            logger.info(f"✅ [CURRICULUM READER] Downloaded from Supabase Storage: {bucket_name}/{file_path_in_bucket}")
                        else:
                            logger.warning(f"⚠️ [CURRICULUM READER] Supabase service not available, cannot download from storage")
                    except Exception as storage_err:
                        logger.warning(f"⚠️ [CURRICULUM READER] Failed to download from Supabase Storage: {storage_err}")
                        # Fall through to try local filesystem as fallback
            
            # If not from Supabase Storage or download failed, try local filesystem
            if file_content is None:
                # Read file from local storage (fallback or legacy format)
                # storage_path is typically stored as a relative path like "curriculum/{parent_id}/{file_name}".
                # To avoid issues with different working directories (local dev vs deployment),
                # we try a small set of candidate resolutions.
                raw_path = Path(storage_path)
                api_root = Path(__file__).resolve().parents[2]  # .../learn_loop/api
                repo_root = api_root.parent  # .../learn_loop

                candidates: List[Path] = []
                if raw_path.is_absolute():
                    candidates.append(raw_path)
                else:
                    candidates.append(raw_path)  # relative to cwd (legacy)
                    candidates.append(api_root / raw_path)  # relative to api/
                    candidates.append(repo_root / raw_path)  # relative to learn_loop/
                    # Also try /app/ paths for Railway deployment
                    candidates.append(Path("/app") / raw_path)
                    candidates.append(Path("/app/api") / raw_path)

                file_path: Optional[Path] = None
                for c in candidates:
                    logger.info(f"📖 [CURRICULUM READER] Checking candidate path: {c} (absolute: {c.absolute()})")
                    if c.exists():
                        file_path = c
                        break

                if not file_path:
                    logger.warning(f"⚠️ [CURRICULUM READER] Curriculum file not found for {file_name}. Tried: {[str(p) for p in candidates]}")
                    continue
                
                # Read file content from local filesystem
                with open(file_path, "rb") as f:
                    file_content = f.read()
            
            if not file_content:
                logger.warning(f"⚠️ [CURRICULUM READER] No file content retrieved for {file_name}")
                continue
            
            # Extract text based on file type
            # Determine file extension from filename or storage_path
            file_ext = Path(file_name).suffix.lower() if file_name else ".pdf"
            if file_ext == '.pdf':
                text = extract_text_from_pdf(file_content)
            elif file_ext in ['.txt', '.md']:
                text = extract_text_from_txt(file_content)
            else:
                logger.warning(f"Unsupported curriculum file type: {file_ext} for {file_name}")
                continue
            
            if text and text.strip():
                combined_content.append(f"[Curriculum: {file_name}]\n{text.strip()}")
                logger.info(f"✅ [CURRICULUM READER] Successfully read curriculum file: {file_name} ({len(text)} chars)")
            else:
                logger.warning(f"⚠️ [CURRICULUM READER] Curriculum file {file_name} appears to be empty")
                
        except Exception as e:
            logger.error(f"❌ [CURRICULUM READER] Error reading curriculum file {file_name}: {e}", exc_info=True)
            continue
    
    if combined_content:
        result = "\n\n---\n\n".join(combined_content)
        logger.info(f"✅ [CURRICULUM READER] Combined {len(combined_content)} curriculum files into {len(result)} chars")
        return result
    
    logger.warning(f"⚠️ [CURRICULUM READER] No curriculum content could be read from {len(curriculum_files)} files")
    return None


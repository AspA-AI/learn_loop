"""
Migration script to move existing target_topic data from children table to child_topics table.
Run this once after creating the child_topics table to migrate existing data.
"""
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.supabase_service import supabase_service
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_child_topics():
    """Clean all data from child_topics table"""
    if not supabase_service.client:
        logger.error("Supabase client not initialized. Check your .env file.")
        return
    
    try:
        logger.info("Cleaning child_topics table...")
            # Get all topics first
        all_topics = supabase_service.client.table("child_topics").select("id").execute()
        
        if all_topics.data:
            # Delete all rows from child_topics (using a more efficient approach)
            # Delete by selecting all IDs and deleting them
            topic_ids = [topic["id"] for topic in all_topics.data]
            for topic_id in topic_ids:
                supabase_service.client.table("child_topics").delete().eq("id", topic_id).execute()
            logger.info(f"✓ Cleaned {len(all_topics.data)} topics from child_topics table.")
        else:
            logger.info("✓ child_topics table is already empty.")
    except Exception as e:
        logger.error(f"Error cleaning child_topics table: {e}")
        raise

def migrate_topics():
    """Migrate all target_topic values from children table to child_topics table"""
    if not supabase_service.client:
        logger.error("Supabase client not initialized. Check your .env file.")
        return
    
    try:
        # First, clean the child_topics table
        clean_child_topics()
        
        # Get all children with target_topic
        response = supabase_service.client.table("children").select("id, target_topic").not_.is_("target_topic", "null").execute()
        children_with_topics = response.data
        
        if not children_with_topics:
            logger.info("No children with target_topic found. Nothing to migrate.")
            return
        
        logger.info(f"Found {len(children_with_topics)} children with target_topic. Starting migration...")
        
        migrated_count = 0
        skipped_count = 0
        
        for child in children_with_topics:
            child_id = child["id"]
            target_topic = child["target_topic"]
            
            # Check if child has any topics in child_topics (after cleaning, should be empty)
            all_topics = supabase_service.client.table("child_topics").select("*").eq("child_id", child_id).execute()
            
            # Set as active if this is the first topic for this child
            set_as_active = len(all_topics.data) == 0
            
            try:
                supabase_service.add_child_topic(child_id, target_topic, subject="General", set_as_active=set_as_active)
                logger.info(f"✓ Migrated topic '{target_topic}' for child {child_id} (active: {set_as_active})")
                migrated_count += 1
            except Exception as e:
                logger.error(f"✗ Failed to migrate topic '{target_topic}' for child {child_id}: {e}")
        
        logger.info(f"\nMigration complete!")
        logger.info(f"  - Migrated: {migrated_count} topics")
        logger.info(f"  - Skipped: {skipped_count} topics")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Starting topic migration from children.target_topic to child_topics table...")
    migrate_topics()


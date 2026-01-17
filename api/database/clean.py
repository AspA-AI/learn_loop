"""
Script to clean all data from database tables while keeping the schema.
This deletes all rows from all tables but does not drop the tables themselves.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.supabase_service import supabase_service
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database():
    """Delete all data from all tables"""
    if not supabase_service.client:
        logger.error("Supabase client not initialized. Check your .env file.")
        return False
    
    try:
        logger.info("Cleaning database...")
        
        # Delete in order to respect foreign key constraints
        tables = [
            "interactions",
            "sessions", 
            "child_topics",
            "child_curriculum",
            "curriculum_documents",
            "children"
        ]
        
        deleted_counts = {}
        
        for table in tables:
            try:
                # Get count before deletion
                count_response = supabase_service.client.table(table).select("id", count="exact").execute()
                count = count_response.count if hasattr(count_response, 'count') else 0
                
                if count > 0:
                    # Delete all rows (using a workaround since Supabase doesn't support DELETE without WHERE)
                    # We'll delete by selecting all IDs and deleting them one by one
                    all_rows = supabase_service.client.table(table).select("id").execute()
                    if all_rows.data:
                        for row in all_rows.data:
                            supabase_service.client.table(table).delete().eq("id", row["id"]).execute()
                        deleted_counts[table] = len(all_rows.data)
                        logger.info(f"  ✓ Deleted {len(all_rows.data)} rows from {table}")
                    else:
                        deleted_counts[table] = 0
                        logger.info(f"  ✓ {table} is already empty")
                else:
                    deleted_counts[table] = 0
                    logger.info(f"  ✓ {table} is already empty")
            except Exception as e:
                logger.error(f"  ✗ Error cleaning {table}: {e}")
                deleted_counts[table] = 0
        
        total_deleted = sum(deleted_counts.values())
        logger.info(f"\n✓ Database cleaning complete!")
        logger.info(f"  Total rows deleted: {total_deleted}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database cleaning failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    import sys
    
    # Ask for confirmation
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        confirm = True
    else:
        response = input("⚠️  This will delete ALL data from the database. Are you sure? [y/N]: ")
        confirm = response.lower() in ['y', 'yes']
    
    if confirm:
        success = clean_database()
        sys.exit(0 if success else 1)
    else:
        logger.info("Operation cancelled.")
        sys.exit(0)



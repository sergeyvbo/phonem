import os
import time
import asyncio
from app.core.config import settings

async def cleanup_weekly():
    """
    Background task that runs once a week to clean up any orphaned files.
    """
    WEEK_IN_SECONDS = 7 * 24 * 60 * 60
    while True:
        print("[CLEANUP] Starting weekly cleanup...")
        now = time.time()
        
        directories = [settings.INPUT_DIR, settings.OUTPUT_DIR]
        files_deleted = 0
        
        for directory in directories:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # Keep files for at least a week if they are orphaned
                if os.path.isfile(file_path):
                    if now - os.path.getmtime(file_path) > WEEK_IN_SECONDS:
                        try:
                            os.remove(file_path)
                            files_deleted += 1
                        except Exception as e:
                            print(f"[CLEANUP] Error deleting {file_path}: {e}")
        
        print(f"[CLEANUP] Weekly cleanup complete. Deleted {files_deleted} files.")
        # Wait for 7 days
        await asyncio.sleep(WEEK_IN_SECONDS)

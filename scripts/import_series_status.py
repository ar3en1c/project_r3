#!/usr/bin/env python3
"""
Script to import series status, season count, and episode count from a JSONL.gz file
into a PostgreSQL database using the Series model structure.

Features:
- Progress bar with tqdm
- Error logging to file
- Resume capability (tracks processed IDs)
- Database connection retry logic
- Batch processing for efficiency
- Uses python-decouple for environment variables

Requirements:
- psycopg2 (pip install psycopg2-binary)
- tqdm (pip install tqdm)
- python-decouple (pip install python-decouple)
- Python 3.6+

Usage:
1. Install requirements: pip install psycopg2-binary tqdm python-decouple
2. Create .env file with database settings (see below)
3. Run: python import_series_status.py
"""

import gzip
import json
import psycopg2
from psycopg2 import sql, OperationalError
from psycopg2.extras import execute_batch
import os
from decouple import config
from tqdm import tqdm
import logging
from time import sleep
import platform

# Determine the correct path separator for the OS
SEP = os.path.sep

# Base directory is where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path configuration - using absolute paths
INPUT_FILE = os.path.join(BASE_DIR, "series_status.jsonl.gz")
LOG_FILE = os.path.join(BASE_DIR, "import_series_status.log")
PROCESSED_IDS_FILE = os.path.join(BASE_DIR, "processed_ids.txt")

# Create log directory if it doesn't exist
os.makedirs(BASE_DIR, exist_ok=True)

# Batch size for database operations
BATCH_SIZE = 1000

# Maximum retries for database connection
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection settings from .env file
DB_NAME = config('DB_NAME')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')

def get_db_connection():
    """Create and return a database connection with retry logic."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            return conn
        except OperationalError as e:
            retries += 1
            logger.warning(f"Database connection failed (attempt {retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Could not connect to database.")
                raise

def load_processed_ids():
    """Load already processed TVDB IDs from file."""
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    
    with open(PROCESSED_IDS_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_ids(processed_ids):
    """Save processed TVDB IDs to file."""
    with open(PROCESSED_IDS_FILE, 'w') as f:
        for tvdb_id in sorted(processed_ids):
            f.write(f"{tvdb_id}\n")

def get_total_lines(file_path):
    """Count total lines in the gzipped file for progress bar."""
    with gzip.open(file_path, 'rb') as f:
        return sum(1 for _ in f)

def process_file():
    """Process the JSONL.gz file and update the database."""
    conn = None
    try:
        # Verify input file exists
        if not os.path.exists(INPUT_FILE):
            logger.error(f"Input file not found: {INPUT_FILE}")
            return
            
        # Load already processed IDs
        processed_ids = load_processed_ids()
        logger.info(f"Loaded {len(processed_ids)} already processed IDs")
        
        # Get total lines for progress bar
        total_lines = get_total_lines(INPUT_FILE)
        logger.info(f"Total records to process: {total_lines}")
        
        # Prepare the update query
        update_query = sql.SQL("""
            UPDATE series
            SET status = %s, season_count = %s, episode_count = %s
            WHERE tvdb_id = %s
        """)
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Process the file with progress bar
        batch = []
        new_processed_ids = set(processed_ids)
        processed_count = 0
        updated_count = 0
        
        with gzip.open(INPUT_FILE, 'rt', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing records"):
                try:
                    data = json.loads(line)
                    tvdb_id = data['id']
                    
                    # Skip already processed records
                    if tvdb_id in new_processed_ids:
                        continue
                    
                    status = data.get('status', '')
                    season_count = data.get('season_count', 0)
                    episode_count = data.get('episode_count', 0)
                    
                    batch.append((status, season_count, episode_count, tvdb_id))
                    new_processed_ids.add(tvdb_id)
                    processed_count += 1
                    
                    # Process batch when it reaches batch size
                    if len(batch) >= BATCH_SIZE:
                        execute_batch(cursor, update_query, batch)
                        updated_count += cursor.rowcount
                        conn.commit()
                        batch = []
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing line: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing record {tvdb_id}: {e}")
                    continue
        
        # Process any remaining records in the final batch
        if batch:
            execute_batch(cursor, update_query, batch)
            updated_count += cursor.rowcount
            conn.commit()
        
        # Save processed IDs
        save_processed_ids(new_processed_ids)
        
        logger.info(f"\nImport completed successfully!")
        logger.info(f"Total records processed: {processed_count}")
        logger.info(f"Total series updated: {updated_count}")
        logger.info(f"Total unique IDs processed: {len(new_processed_ids)}")
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting series status import...")
    process_file()
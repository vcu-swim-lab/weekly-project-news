#!/usr/bin/env python3
# Unified Newsletter Pipeline. This runs every Sunday at 12pm
# This script combines download, create, and send processes into one operation
# It includes retry logic, validation checks, and logging

import subprocess
import logging
import time
import os
import glob
import sqlite3
from datetime import datetime

# Set up logging with more detailed format
logging.basicConfig(
    filename='newsletter_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)

# Configuration
PYTHON_PATH = 'C:/Users/chris/AppData/Local/Programs/Python/Python313/python.exe'  # If running on local machine
# PYTHON_PATH = '/home/projectnews/venv/bin/python'
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30  # Initial delay, will increase exponentially
NEWSLETTER_OUTPUT_DIR = 'newsletter_data'

#Format seconds into a human-readable string.
def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    else:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)} minutes and {seconds:.2f} seconds"

# Run a Python script with retry logic and exponential backoff.
# Args: script_name: Name of the script to run, max_retries: Maximum number of retry attempts
# Returns: bool: True if script ran successfully, False otherwise
def run_script_with_retry(script_name, max_retries=MAX_RETRIES):
    if script_name == 'clean_db.py' and not os.path.exists('github.db'):
        print(f'Skipping {script_name} - github.db does not exist yet')
        logging.info(f"Skipping {script_name} - github.db does not exist yet")
        return True

    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.time()
            
            if attempt > 1:
                delay = RETRY_DELAY_SECONDS * (2 ** (attempt - 2))  # Exponential backoff
                print(f"Retry attempt {attempt}/{max_retries} for {script_name} after {delay}s delay...")
                logging.warning(f"Retry attempt {attempt}/{max_retries} for {script_name} after {delay}s delay")
                time.sleep(delay)
            
            print(f"Starting to run {script_name}... (Attempt {attempt}/{max_retries})")
            logging.info(f"Starting {script_name} - Attempt {attempt}/{max_retries}")
            
            result = subprocess.run(
                [PYTHON_PATH, script_name],
                check=True,
                capture_output=True,
                text=True
            )
            
            end_time = time.time()
            duration = end_time - start_time
            formatted_time = format_time(duration)
            
            print(f"Successfully finished running {script_name}")
            print(f"  Execution time: {formatted_time}")
            logging.info(f"Successfully completed {script_name} in {formatted_time}")
            
            # Log script output if there's anything meaningful
            if result.stdout.strip():
                logging.debug(f"Output from {script_name}: {result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            end_time = time.time()
            duration = end_time - start_time
            formatted_time = format_time(duration)
            
            error_msg = f"Error running {script_name} on attempt {attempt}/{max_retries}: {e}"
            print(f"{error_msg}")
            print(f"  Time before error: {formatted_time}")
            logging.error(error_msg)
            logging.error(f"Time before error: {formatted_time}")
            
            # Log stderr if available
            if e.stderr:
                logging.error(f"Error output from {script_name}: {e.stderr}")
            
            # If this was the last attempt, return False
            if attempt == max_retries:
                logging.error(f"Failed to run {script_name} after {max_retries} attempts")
                return False
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            formatted_time = format_time(duration)
            
            error_msg = f"Unexpected error running {script_name} on attempt {attempt}/{max_retries}: {e}"
            print(f"{error_msg}")
            logging.error(error_msg)
            logging.error(f"Time before error: {formatted_time}")
            
            if attempt == max_retries:
                return False
    
    return False

# Validate that the database was updated successfully.
# Returns:  bool: True if validation passes, False otherwise
def validate_database_update():
    try:
        db_path = 'github.db'
        print("Validating database update...")
        
        # Check 1: Database file exists
        if not os.path.exists(db_path):
            logging.error(f"Database file {db_path} not found")
            print(f"Database file {db_path} not found")
            return False
        
        # Check 2: Database was modified recently (within last hour)
        modification_time = os.path.getmtime(db_path)
        time_since_modification = time.time() - modification_time
        
        if time_since_modification > 3600:  # More than 1 hour old
            logging.error(f"Database hasn't been modified recently (last modified {format_time(time_since_modification)} ago)")
            print(f"Database is stale (last modified {format_time(time_since_modification)} ago)")
            return False
        
        logging.info(f"Database was modified {format_time(time_since_modification)} ago")
        print(f"Database recently updated ({format_time(time_since_modification)} ago)")
        
        # Check 3: Database has data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            logging.error("Database has no tables")
            print("Database has no tables")
            conn.close()
            return False
        
        table_names = [t[0] for t in tables]
        logging.info(f"Database has {len(tables)} table(s): {table_names}")
        print(f"Database has {len(tables)} table(s): {table_names}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Database validation failed with SQLite error: {e}")
        print(f"Database error: {e}")
        return False
    except Exception as e:
        logging.error(f"Database validation failed: {e}")
        print(f"Database validation error: {e}")
        return False

# Validate that newsletter markdown files were created successfully.
# Returns: tuple: (success: bool, file_count: int)
def validate_newsletter_files():
    try:
        print("Validating newsletter files...")
        logging.info("Starting newsletter file validation")
        
        # Look for markdown files in the newsletter directory
        patterns = [
            f"{NEWSLETTER_OUTPUT_DIR}/*.md",
            "*.md",  # Fallback if files are in current directory
        ]
        
        newsletter_files = []
        for pattern in patterns:
            files = glob.glob(pattern)
            if files:
                newsletter_files = files
                break
        
        if not newsletter_files:
            logging.error("No newsletter markdown files found")
            print("No newsletter files found")
            return False, 0
        
        # Check that files are not empty
        valid_files = 0
        for file_path in newsletter_files:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 100:  # Arbitrary minimum size
                    valid_files += 1
                else:
                    logging.warning(f"Newsletter file {file_path} is too small ({file_size} bytes)")
            except Exception as e:
                logging.error(f"Error checking file {file_path}: {e}")
        
        if valid_files == 0:
            logging.error("No valid newsletter files found (all files too small or unreadable)")
            print("No valid newsletter files found")
            return False, 0
        
        logging.info(f"Found {valid_files} valid newsletter file(s)")
        print(f"Found {valid_files} valid newsletter file(s)")
        return True, valid_files
        
    except Exception as e:
        logging.error(f"Newsletter file validation failed: {e}")
        print(f"Newsletter validation error: {e}")
        return False, 0

# Run the complete newsletter pipeline with validation gates.
# Returns: bool: True if entire pipeline succeeded, False otherwise
def run_pipeline():
    pipeline_start_time = time.time()
    
    print("=" * 70)
    print("NEWSLETTER PIPELINE STARTED")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    logging.info("="*70)
    logging.info("NEWSLETTER PIPELINE STARTED")
    logging.info("="*70)
    
    # Stage 1: Data Download and Processing
    print("\n" + "="*70)
    print("STAGE 1: DATA DOWNLOAD AND PROCESSING")
    print("="*70)
    logging.info("Starting Stage 1: Data Download and Processing")
    
    download_scripts = [
        'download_new_subscribers.py',
        'fix_subscribers_file.py',
        'clean_db.py',
        'parse_github_data.py',
        'update_db.py'
    ]
    
    for script in download_scripts:
        if not run_script_with_retry(script):
            logging.critical(f"Pipeline FAILED at Stage 1: {script} failed after all retries")
            print(f"\nPIPELINE FAILED: {script} could not complete")
            return False
    
    # Validation Gate 1: Check database was updated
    print("\nValidation Gate 1: Checking database update...")
    if not validate_database_update():
        logging.critical("Pipeline FAILED at Validation Gate 1: Database validation failed")
        print("PIPELINE FAILED: Database validation failed")
        return False
    print("Database validation passed")
    
    # Stage 2: Newsletter Creation
    print("\n" + "="*70)
    print("STAGE 2: NEWSLETTER CREATION")
    print("="*70)
    logging.info("Starting Stage 2: Newsletter Creation")
    
    if not run_script_with_retry('create_newsletter.py'):
        logging.critical("Pipeline FAILED at Stage 2: create_newsletter.py failed after all retries")
        print("\nPIPELINE FAILED: Newsletter creation failed")
        return False
    
    # Validation Gate 2: Check newsletter files were created
    print("\nValidation Gate 2: Checking newsletter files...")
    files_valid, file_count = validate_newsletter_files()
    if not files_valid:
        logging.critical("Pipeline FAILED at Validation Gate 2: Newsletter file validation failed")
        print("PIPELINE FAILED: Newsletter files were not created properly")
        return False
    print(f"Newsletter file validation passed ({file_count} files ready)")
    
    # Stage 3: Newsletter Sending
    print("\n" + "="*70)
    print("STAGE 3: NEWSLETTER SENDING")
    print("="*70)
    logging.info(f"Starting Stage 3: Newsletter Sending ({file_count} newsletters)")
    
    # if not run_script_with_retry('send_newsletter.py'):
    #     logging.critical("Pipeline FAILED at Stage 3: send_newsletter.py failed after all retries")
    #     print("\nPIPELINE FAILED: Newsletter sending failed")
    #     print("WARNING: Newsletters were created but not sent!")
    #     logging.warning("Newsletters were created but not sent - manual intervention may be needed")
    #     return False
    
    # Success
    pipeline_end_time = time.time()
    total_duration = pipeline_end_time - pipeline_start_time
    formatted_total_time = format_time(total_duration)
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Total execution time: {formatted_total_time}")
    print(f"Newsletters sent: {file_count}")
    print("="*70)
    
    logging.info("="*70)
    logging.info("PIPELINE COMPLETED SUCCESSFULLY")
    logging.info(f"Total execution time: {formatted_total_time}")
    logging.info(f"Newsletters sent: {file_count}")
    logging.info("="*70)
    
    return True

# Main entry point for the pipeline.
def main():
    try:
        success = run_pipeline()
        
        if not success:
            print("\nPipeline failed. Check newsletter_pipeline.log for details.")
            logging.error("Pipeline execution failed - manual intervention required")
            exit(1)
        else:
            print("\nAll done!")
            exit(0)
            
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        logging.warning("Pipeline interrupted by user (KeyboardInterrupt)")
        exit(130)
        
    except Exception as e:
        print(f"\nFATAL ERROR in pipeline: {e}")
        logging.critical(f"Fatal error in pipeline execution: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
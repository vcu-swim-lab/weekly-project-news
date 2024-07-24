import subprocess
import logging
from datetime import datetime
import time
import os

# Set up logging
logging.basicConfig(filename='newsletter_preparation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    else:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)} minutes and {seconds:.2f} seconds"
    
def remove_file(file_name):
    try:
        os.remove(file_name)
        print(f"Successfully removed {file_name}")
        logging.info(f"Successfully removed {file_name}")
    except FileNotFoundError:
        print(f"{file_name} not found, skipping removal")
        logging.info(f"{file_name} not found, skipping removal")
    except Exception as e:
        print(f"Error removing {file_name}: {e}")
        logging.error(f"Error removing {file_name}: {e}")
        raise

def run_script(script_name):
    try:
        start_time = time.time()
        print(f"Starting to run {script_name}...")

        # if running on server
        subprocess.run(['/home/projectnews/venv/bin/python', script_name], check=True)

        # if running on local machine
        # subprocess.run(['/usr/local/bin/python3', script_name], check=True)

        end_time = time.time()
        duration = end_time - start_time
        formatted_time = format_time(duration)
        print(f"Successfully finished running {script_name}")
        print(f"Execution time for {script_name}: {formatted_time}")
        logging.info(f"Successfully ran {script_name}")
        logging.info(f"Execution time for {script_name}: {formatted_time}")
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        duration = end_time - start_time
        formatted_time = format_time(duration)
        print(f"Error running {script_name}: {e}")
        print(f"Time before error for {script_name}: {formatted_time}")
        logging.error(f"Error running {script_name}: {e}")
        logging.error(f"Time before error for {script_name}: {formatted_time}")
        raise

def main():
    start_time = time.time()
    logging.info("Starting newsletter preparation process")

    remove_file('github.db')
    
    # scripts = [
    #     'download_new_subscribers.py',
    #     'fix_subscribers_file.py',
    #     'clean_db.py',
    #     'parse_github_data.py',
    #     'update_db.py',
    #     'clean_db.py',
    # ]

    scripts = [
        'download_new_subscribers.py',
        'fix_subscribers_file.py',
        'parse_github_data.py',
    ]

    for script in scripts:
        run_script(script)

    end_time = time.time()
    total_duration = end_time - start_time
    formatted_total_time = format_time(total_duration)

    print("Newsletter preparation process completed")
    print(f"Total execution time: {formatted_total_time}")
    logging.info("Newsletter preparation process completed")
    logging.info(f"Total execution time: {formatted_total_time}")
    logging.info("-" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred in the main process: {e}")
        logging.error(f"An error occurred in the main process: {e}")
        logging.error("-" * 50)

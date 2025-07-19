#!/usr/bin/env python3
"""
Wayback Machine Scraper
Scrapes websites from the Wayback Machine using wayback-machine-downloader
for two different dates specified in a CSV file.
"""

import argparse
import os
import subprocess
import sys
import json
import logging
import time
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# CSV Column Constants - Modify these to match your CSV column names
WEBSITE_URL_COLUMN = 'URL'
DEAL_DATE_COLUMN = 'Deal Date'

# Time period parameters (in months)
MONTHS_BEFORE_DEAL = 6
MONTHS_AFTER_DEAL = 12

# State file name
STATE_FILE_NAME = 'wayback_scraper_state.json'

# Logging configuration
MAIN_LOG_FILE = 'wayback_scraper.log'

# Timeout in seconds
TIMEOUT = 900  # 15 minutes


def setup_logging(output_dir):
    """
    Setup logging configuration for both console and file output.
    """
    # Create logs directory
    logs_dir = os.path.join(output_dir, 'logs')
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    # Main log file path
    main_log_path = os.path.join(logs_dir, MAIN_LOG_FILE)
    
    # Configure logging for main script only
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler (main script logs only)
            logging.FileHandler(main_log_path, mode='a', encoding='utf-8')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Main log file: {main_log_path}")
    return logger


def create_download_logger(download_folder, url, date):
    """
    Create a specific logger for each download operation.
    """
    log_file = os.path.join(download_folder, 'download.log')
    
    # Create file handler for this specific download
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(f'download_{url}_{date}')
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent propagation to main logger
    logger.addHandler(file_handler)
    
    return logger, log_file


def load_state(state_file_path):
    """
    Load the state from JSON file.
    Returns empty dict if file doesn't exist.
    """
    if os.path.exists(state_file_path):
        try:
            with open(state_file_path, 'r') as f:
                state = json.load(f)
                logging.info(f"Loaded state from {state_file_path}")
                return state
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Warning: Could not load state file {state_file_path}: {e}")
            logging.info("Starting fresh...")
    return {}


def save_state(state, state_file_path):
    """
    Save the state to JSON file.
    """
    try:
        with open(state_file_path, 'w') as f:
            json.dump(state, f, indent=2)
        logging.info(f"State saved to {state_file_path}")
    except IOError as e:
        logging.warning(f"Warning: Could not save state file {state_file_path}: {e}")


def is_download_completed(state, website_url, date, folder_name):
    """
    Check if a specific download has been completed.
    """
    url_key = website_url.strip()
    if url_key not in state:
        return False
    
    downloads = state[url_key].get('downloads', {})
    download_key = f"{date}_{folder_name}"
    return downloads.get(download_key, {}).get('completed', False)


def mark_download_completed(state, website_url, date, folder_name, success=True):
    """
    Mark a download as completed in the state.
    """
    url_key = website_url.strip()
    if url_key not in state:
        state[url_key] = {'downloads': {}}
    
    if 'downloads' not in state[url_key]:
        state[url_key]['downloads'] = {}
    
    download_key = f"{date}_{folder_name}"
    state[url_key]['downloads'][download_key] = {
        'completed': success,
        'timestamp': datetime.now().isoformat(),
        'folder': folder_name
    }


def get_resume_stats(state, df):
    """
    Get statistics about what can be resumed.
    """
    total_downloads = len(df) * 2  # Each row has 2 downloads
    completed_downloads = 0
    
    for _, row in df.iterrows():
        website_url = str(row[WEBSITE_URL_COLUMN]).strip()
        deal_date = str(row[DEAL_DATE_COLUMN]).strip()
        
        first_date, second_date = calculate_download_dates(deal_date)
        if first_date is None or second_date is None:
            continue
            
        sanitized_name = sanitize_folder_name(website_url)
        first_date_folder = f"{sanitized_name}_up_to_{first_date}"
        second_date_folder = f"{sanitized_name}_up_to_{second_date}"
        
        if is_download_completed(state, website_url, first_date, first_date_folder):
            completed_downloads += 1
        if is_download_completed(state, website_url, second_date, second_date_folder):
            completed_downloads += 1
    
    return completed_downloads, total_downloads


def sanitize_folder_name(url):
    """
    Sanitize URL to create a valid folder name.
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    # Remove invalid characters for folder names
    sanitized = "".join(c for c in domain if c.isalnum() or c in ('-', '_', '.'))
    return sanitized


def parse_deal_date(deal_date_str):
    """
    Parse deal date string to datetime object.
    Handles format like "2016-09-30 00:00:00"
    """
    try:
        # Remove time part if present and parse date
        date_part = deal_date_str.split()[0]
        return datetime.strptime(date_part, '%Y-%m-%d')
    except (ValueError, AttributeError) as e:
        logging.warning(f"Could not parse deal date '{deal_date_str}': {e}")
        return None


def calculate_download_dates(deal_date_str):
    """
    Calculate first date (6 months before deal) and second date (1 year after deal).
    Returns tuple of (first_date, second_date) as YYYYMMDD strings.
    """
    deal_date = parse_deal_date(deal_date_str)
    if deal_date is None:
        return None, None
    
    # Calculate 6 months before deal date
    first_date = deal_date - relativedelta(months=MONTHS_BEFORE_DEAL)
    
    # Calculate 1 year after deal date
    second_date = deal_date + relativedelta(months=MONTHS_AFTER_DEAL)
    
    return first_date.strftime('%Y%m%d'), second_date.strftime('%Y%m%d')


def run_wayback_downloader(url, date, output_folder, state, state_file_path):
    """
    Run wayback-machine-downloader with specified parameters.
    """
    folder_name = os.path.basename(output_folder)
    
    # Check if already completed
    if is_download_completed(state, url, date, folder_name):
        logging.info(f"Skipping {url} (up to {date}) - already completed")
        return True
    
    logging.info(f"Downloading {url} up to {date} into {output_folder}")
    
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Create download-specific logger
    download_logger, log_file = create_download_logger(output_folder, url, date)
    
    # Prepare wayback-machine-downloader command
    cmd = [
        "/build/bin/wayback_machine_downloader",
        url,
        "--to", date,
        "--directory", output_folder,
        "-o", r"/(\.(html|htm)$|\/[^\.]*\/?$)/",
        # "-x", r"/\.(jpg|jpeg|png|gif|css|js|svg|ico|woff|ttf|mp4|webp)$/",
        "-c", "2",
    ]
    
    success = False
    start_time = time.time()
    
    try:
        # Log the command that will be run
        download_logger.info(f"Starting download for {url} up to {date}")
        download_logger.info(f"Command: {' '.join(cmd)}")
        download_logger.info(f"Output folder: {output_folder}")
        download_logger.info(f"Log file: {log_file}")
        download_logger.info("-" * 80)
        
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )

        # Log successful completion
        download_logger.info("Download completed successfully")
        if result.stdout:
            download_logger.info(f"Command output:\n{result.stdout}")
        
        success = True
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Error downloading {url} (up to {date}): {e}"
        download_logger.error(error_msg)
        if e.stderr:
            download_logger.error(f"Error details:\n{e.stderr}")
        if e.stdout:
            download_logger.info(f"Command output:\n{e.stdout}")
        logging.error(error_msg)
        
    except subprocess.TimeoutExpired:
        error_msg = f"Timeout downloading {url} (up to {date})"
        download_logger.error(error_msg)
        logging.error(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error downloading {url} (up to {date}): {e}"
        download_logger.error(error_msg)
        logging.error(error_msg)
    
    finally:
        # Calculate and log timing information
        end_time = time.time()
        duration = end_time - start_time
        duration_minutes = duration / 60
        duration_seconds = duration % 60
        
        # Log timing to main log
        if success:
            logging.info(f"Successfully downloaded {url} (up to {date})")
        else:
            logging.error(f"Failed to download {url} (up to {date})")
        
        logging.info(f"Duration: {int(duration_minutes)}m {duration_seconds:.1f}s")
        logging.info(f"Download log saved to: {log_file}")
        
        # Always log completion status to download logger
        download_logger.info(f"Download process finished for {url} (up to {date})")
        download_logger.info(f"Success: {success}")
        download_logger.info(f"Duration: {int(duration_minutes)}m {duration_seconds:.1f}s")
        download_logger.info("-" * 80)
        
        # Remove the download logger handler to avoid memory leaks
        for handler in download_logger.handlers[:]:
            handler.close()
            download_logger.removeHandler(handler)
    
    # Mark as completed (or failed) and save state
    mark_download_completed(state, url, date, folder_name, success)
    save_state(state, state_file_path)
    
    return success


def process_csv(csv_file, output_base_dir, state_file_path):
    """
    Process the CSV file and download websites for each row.
    """
    logging.info(f"Processing CSV file: {csv_file}")
    
    # Always load existing state (resume mode is default)
    state = load_state(state_file_path)
    
    try:
        # Read CSV file with semicolon delimiter
        df = pd.read_csv(csv_file, sep=';')
        
        # Check if CSV has the expected columns
        required_columns = [WEBSITE_URL_COLUMN, DEAL_DATE_COLUMN]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logging.error(f"Error: CSV file is missing required columns: {missing_columns}")
            logging.error(f"Expected columns: {required_columns}")
            logging.error(f"Found columns: {list(df.columns)}")
            return False
        
        logging.info(f"Found {len(df)} websites to process")
        
        # Show resume statistics if state exists
        if state:
            completed, total = get_resume_stats(state, df)
            logging.info(f"Resume statistics: {completed}/{total} downloads already completed")
            logging.info(f"Remaining: {total - completed} downloads")
        else:
            logging.info(f"Starting fresh - no previous state found")
        
        # Process each row
        for row_num, (index, row) in enumerate(df.iterrows(), 1):
            website_url = str(row[WEBSITE_URL_COLUMN]).strip()
            deal_date = str(row[DEAL_DATE_COLUMN]).strip()
            
            # Calculate download dates
            first_date, second_date = calculate_download_dates(deal_date)
            if first_date is None or second_date is None:
                logging.warning(f"Skipping row {row_num} - invalid deal date: {deal_date}")
                continue
            
            logging.info(f"\n--- Processing row {row_num}/{len(df)} ---")
            logging.info(f"Website: {website_url}")
            logging.info(f"Deal date: {deal_date}")
            logging.info(f"First date ({MONTHS_BEFORE_DEAL} months before): {first_date}")
            logging.info(f"Second date ({MONTHS_AFTER_DEAL} months after): {second_date}")
            
            # Create sanitized folder name
            sanitized_name = sanitize_folder_name(website_url)
            
            # Create output folders
            first_date_folder = os.path.join(output_base_dir, f"{sanitized_name}_up_to_{first_date}")
            second_date_folder = os.path.join(output_base_dir, f"{sanitized_name}_up_to_{second_date}")
            
            # Download for first date
            run_wayback_downloader(website_url, first_date, first_date_folder, state, state_file_path)
            
            # Download for second date
            run_wayback_downloader(website_url, second_date, second_date_folder, state, state_file_path)
            
        logging.info(f"\n Finished processing all {len(df)} websites")
        
        # Final state save
        save_state(state, state_file_path)
        return True
        
    except FileNotFoundError:
        logging.error(f"Error: CSV file '{csv_file}' not found")
        return False
    except pd.errors.EmptyDataError:
        logging.error(f"Error: CSV file '{csv_file}' is empty")
        return False
    except Exception as e:
        logging.error(f"Error processing CSV file: {e}")
        return False


def main():
    """
    Main function to parse arguments and start the scraping process.
    """
    parser = argparse.ArgumentParser(
        description="Scrape websites from Wayback Machine for two different dates"
    )
    parser.add_argument(
        "csv_file",
        help="Path to CSV file with columns: URL, Deal Date (semicolon-separated)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="downloads",
        help="Output directory for downloaded websites (default: downloads)"
    )
    parser.add_argument(
        "--state-file",
        "-s",
        help="Path to state file (default: <output_dir>/wayback_scraper_state.json)"
    )
    
    args = parser.parse_args()
    
    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' does not exist")
        sys.exit(1)
    
    # Create output directory
    output_dir = os.path.abspath(args.output)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Set state file path
    state_file_path = args.state_file or os.path.join(output_dir, STATE_FILE_NAME)
    
    # Setup logging
    logger = setup_logging(output_dir)
    
    logger.info("=" * 50)
    logger.info("Wayback Machine Scraper")
    logger.info(f"CSV file: {args.csv_file}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"State file: {state_file_path}")
    logger.info(f"Time periods: {MONTHS_BEFORE_DEAL} months before, {MONTHS_AFTER_DEAL} months after deal date")
    logger.info(f"Resume mode: ALWAYS ON (automatic)")
    logger.info("=" * 50)
    
    # Process the CSV file
    success = process_csv(args.csv_file, output_dir, state_file_path)
    
    if success:
        logger.info(f"\nAll downloads completed. Check the '{output_dir}' directory for results.")
        logger.info(f"State file saved at: {state_file_path}")
        logger.info(f"Main log file saved at: {os.path.join(output_dir, 'logs', MAIN_LOG_FILE)}")
        sys.exit(0)
    else:
        logger.error(f"\nScript completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main() 
# Wayback Machine Scraper

A powerful tool for downloading historical versions of websites from the Internet Archive's Wayback Machine. This scraper processes a CSV file containing URLs and deal dates, then downloads website snapshots from two specific time periods for each URL.

## Features

- **Batch Processing**: Process multiple URLs from a CSV file
- **Time-based Downloads**: Automatically calculates two download dates for each URL:
  - 6 months before the deal date
  - 12 months after the deal date
- **Resume Capability**: Can resume interrupted downloads using state tracking
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Docker Support**: Easy deployment using Docker containers
- **Progress Tracking**: State file to track completed downloads

## Prerequisites

- Docker and Docker Compose
- A CSV file with your URLs and deal dates

## Quick Start

1. **Prepare your data file**:
   Create a `data.csv` file with the following format:
   ```csv
   URL,Deal Date
   https://example.com,2016-09-30
   https://another-site.com,2017-03-15
   ```

2. **Run the scraper**:
   ```bash
   ./run.sh
   ```

3. **Check results**:
   Your downloaded websites will be available in the `downloads/` directory.

## CSV Format

Your CSV file must contain these columns:
- `URL`: The website URL to scrape
- `Deal Date`: The reference date in YYYY-MM-DD format

Example:
```csv
URL,Deal Date
https://example.com,2016-09-30 00:00:00
https://company.com,2017-03-15 00:00:00
```

## How It Works

For each URL in your CSV file, the scraper will:

1. **Calculate download dates**:
   - First date: 6 months before the deal date
   - Second date: 12 months after the deal date

2. **Download website snapshots**:
   - Uses the `wayback-machine-downloader` tool
   - Downloads HTML files and main pages
   - Skips media files (images, CSS, JS) for faster downloads

3. **Organize results**:
   - Creates separate folders for each URL and date
   - Naming format: `{domain}_up_to_{YYYYMMDD}`

## Directory Structure

After running the scraper, your `downloads/` directory will look like:
```
downloads/
├── example_com_up_to_20160330/
│   ├── download.log
│   └── [downloaded files]
├── example_com_up_to_20170930/
│   ├── download.log
│   └── [downloaded files]
└── logs/
    └── wayback_scraper.log
```

## Configuration

### Time Periods
You can modify the time periods in `wayback_scraper.py`:
```python
MONTHS_BEFORE_DEAL = 6  # Months before deal date
MONTHS_AFTER_DEAL = 12  # Months after deal date
```

### CSV Column Names
If your CSV uses different column names, update these constants:
```python
WEBSITE_URL_COLUMN = 'URL'
DEAL_DATE_COLUMN = 'Deal Date'
```

## Advanced Usage

### Manual Docker Commands

Build the image:
```bash
docker-compose build
```

Run the scraper:
```bash
docker-compose up
```

### Direct Python Usage

If you prefer to run without Docker:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install wayback-machine-downloader (Ruby gem)

3. Run the script:
   ```bash
   python3 wayback_scraper.py data.csv --output downloads
   ```

## Command Line Options

```bash
python3 wayback_scraper.py <csv_file> [options]

Options:
  --output DIR     Output directory for downloads (default: downloads)
  --resume         Resume from previous state
  --help           Show help message
```

## State Management

The scraper maintains a state file (`wayback_scraper_state.json`) that tracks:
- Completed downloads
- Download timestamps
- Folder locations

This allows you to:
- Resume interrupted downloads
- Skip already completed downloads
- Track progress across multiple runs

## Logging

The scraper provides comprehensive logging:
- **Main log**: `downloads/logs/wayback_scraper.log`
- **Download logs**: Individual logs in each download folder
- **Console output**: Real-time progress updates

## Troubleshooting

### Common Issues

1. **Docker not running**:
   ```bash
   # Start Docker Desktop or Docker daemon
   sudo systemctl start docker  # Linux
   ```

2. **CSV file not found**:
   - Ensure `data.csv` exists in the project root
   - Check file permissions

3. **Download timeouts**:
   - The scraper has a 15-minute timeout per download
   - Large websites may take longer
   - Check logs for specific errors

4. **Resume downloads**:
   ```bash
   # The scraper automatically resumes from state file
   # To force fresh start, delete wayback_scraper_state.json
   ```

### Debug Mode

For detailed debugging, check the logs:
```bash
# View main log
tail -f downloads/logs/wayback_scraper.log

# View specific download log
tail -f downloads/example_com_up_to_20160330/download.log
```

## Performance Tips

- **Large datasets**: Process in smaller batches
- **Network issues**: The scraper will retry failed downloads
- **Storage**: Ensure sufficient disk space for downloads
- **Memory**: Monitor Docker container memory usage

## Limitations

- Downloads are limited to HTML files and main pages
- Media files (images, CSS, JS) are excluded for performance
- Wayback Machine availability may vary by URL and date
- Rate limiting may apply for large-scale scraping

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Open an issue on the repository

---

**Note**: This tool is designed for research and archival purposes. Please respect the Internet Archive's terms of service and robots.txt files when scraping websites.
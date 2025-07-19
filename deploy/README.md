# Wayback Scraper - Quick Start

A simple tool to download historical website snapshots from the Internet Archive's Wayback Machine.

## Prerequisites

- Docker and Docker Compose installed
- GitHub Container Registry access (the image should be publicly available)

## Quick Setup

1. **Prepare your data file**:
   Create a `data.csv` file with your URLs and deal dates:
   ```csv
   URL,Deal Date
   https://example.com,2016-09-30
   https://another-site.com,2017-03-15
   ```

2. **Run the scraper**:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

3. **Check results**:
   Your downloaded websites will be in the `downloads/` directory.

## What it does

For each URL in your CSV file, the scraper downloads website snapshots from:
- 6 months before the deal date
- 12 months after the deal date

## File Structure

```
wayback_scraper/
├── docker-compose.yml  # Runs the containerized scraper
├── run.sh             # Setup and execution script
├── README.md          # This file
├── data.csv           # Your URLs and dates (create this)
└── downloads/         # Downloaded websites (created automatically)
```

## Troubleshooting

- **Docker not running**: Start Docker Desktop or Docker daemon
- **Permission denied**: Run `chmod +x run.sh` to make the script executable
- **Image not found**: Ensure the Docker image is available in GitHub Container Registry

## Support

Check the logs in `downloads/logs/` for detailed information about the scraping process. 
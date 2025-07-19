#!/bin/bash

# Wayback Scraper Runner Script
# This script sets up and runs the Wayback Scraper using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Wayback Scraper Setup and Runner${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

# Check if data.csv exists
if [ ! -f "data.csv" ]; then
    echo -e "${YELLOW}⚠️  data.csv not found.${NC}"
    echo -e "${YELLOW}📝 Please create a data.csv file with your URLs and deal dates, then run this script again.${NC}"
    exit 1
fi

# Create downloads directory if it doesn't exist
if [ ! -d "downloads" ]; then
    echo -e "${GREEN}📁 Creating downloads directory...${NC}"
    mkdir -p downloads
fi

# Pull the latest image
echo -e "${GREEN}📥 Pulling latest Docker image...${NC}"
docker compose pull

# Run the scraper
echo -e "${GREEN}🏃 Starting Wayback Scraper...${NC}"
echo -e "${YELLOW}📋 Processing URLs from data.csv...${NC}"
echo -e "${YELLOW}📁 Downloads will be saved to ./downloads/ directory${NC}"
echo -e "${YELLOW}📝 Logs will be available in ./downloads/logs/ directory${NC}"
echo ""

# Run docker-compose
docker compose up --abort-on-container-exit

# Check if the container completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Wayback Scraper completed successfully!${NC}"
    echo -e "${GREEN}📁 Check the downloads/ directory for your scraped websites.${NC}"
    echo -e "${GREEN}📝 Check downloads/logs/ for detailed logs.${NC}"
else
    echo ""
    echo -e "${RED}❌ Wayback Scraper encountered an error.${NC}"
    echo -e "${YELLOW}📝 Check the logs above for details.${NC}"
    exit 1
fi 
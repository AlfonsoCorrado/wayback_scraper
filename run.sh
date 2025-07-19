#!/bin/bash

# Wayback Scraper - Easy Run Script
# This script makes it easy to run the Wayback Machine scraper

set -e

echo "🚀 Wayback Scraper - Starting up..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running or not accessible"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check if data.csv exists
if [ ! -f "data.csv" ]; then
    echo "❌ Error: data.csv file not found!"
    echo ""
    echo "📋 Please create a data.csv file with your URLs and deal dates."
    echo "You can use data_example.csv as a template."
    echo ""
    echo "Required format:"
    echo "URL;Deal Date"
    echo "https://example.com;2016-09-30"
    echo ""
    exit 1
fi

# Check if the Docker image exists
if ! docker image inspect wayback-scraper:latest > /dev/null 2>&1; then
    echo "❌ Error: Docker image 'wayback-scraper:latest' not found!"
    echo ""
    echo "📥 Please run the load script first:"
    echo "   ./load_image.sh"
    echo ""
    exit 1
fi

# Create downloads directory if it doesn't exist
mkdir -p downloads

echo "✅ All checks passed!"
echo "📊 Processing data from: data.csv"
echo "📁 Results will be saved to: downloads/"
echo ""

# Run the scraper
echo "🔄 Starting the scraper..."
if command -v docker-compose &> /dev/null; then
    docker-compose up --build
else
    docker compose up --build
fi

echo ""
echo "✅ Scraping completed!"
echo "📁 Check the 'downloads' folder for your results" 
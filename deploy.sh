#!/bin/bash

# Deploy Script for Wayback Scraper
# This script builds the Docker image, pushes it to Docker Hub,
# and creates/pushes the artifact to GitHub releases

set -e  # Exit on any error

# Configuration
IMAGE_NAME="wayback-scraper"
DOCKERHUB_USERNAME="alfonsocorrado"  # Replace with your Docker Hub username
REGISTRY="docker.io"
FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
ARTIFACT_FOLDER="wayback_scraper"  # Changed from "artifact" to "wayback_scraper"

# Version configuration
VERSION=${1:-"1.0.0"}  # Use first argument or default to 1.0.0
TAG="v${VERSION}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting deployment process for ${IMAGE_NAME} v${VERSION}${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Please install Git.${NC}"
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not in a git repository. Please run this script from the project root.${NC}"
    exit 1
fi

# Update submodules
echo -e "${GREEN}🔄 Updating submodules...${NC}"
git submodule update --init --recursive
git submodule update --remote --merge
echo -e "${GREEN}✅ Submodules updated successfully${NC}"

# Check if user is logged in to Docker Hub
echo -e "${YELLOW}📝 Note: Make sure you're logged into Docker Hub with: docker login${NC}"

# Step 1: Build the Docker image
echo -e "${GREEN}🔨 Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:latest .
docker build -t ${IMAGE_NAME}:${VERSION} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Step 2: Tag and push to Docker Hub
echo -e "${GREEN}🏷️  Tagging image for Docker Hub...${NC}"
docker tag ${IMAGE_NAME}:latest ${FULL_IMAGE_NAME}:latest
docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}:${VERSION}

echo -e "${GREEN}📤 Pushing image to Docker Hub...${NC}"
if docker push ${FULL_IMAGE_NAME}:latest && docker push ${FULL_IMAGE_NAME}:${VERSION}; then
    echo -e "${GREEN}✅ Image pushed successfully to ${FULL_IMAGE_NAME}:latest and ${FULL_IMAGE_NAME}:${VERSION}${NC}"
else
    echo -e "${RED}❌ Push failed${NC}"
    echo -e "${YELLOW}💡 If you see authentication errors, run: docker login${NC}"
    echo -e "${YELLOW}💡 Make sure you have permission to push to ${FULL_IMAGE_NAME}${NC}"
    exit 1
fi

# Step 3: Create artifact folder and copy files
echo -e "${GREEN}📝 Creating artifact folder...${NC}"
rm -rf ${ARTIFACT_FOLDER}  # Remove existing folder if it exists
mkdir -p ${ARTIFACT_FOLDER}

# Copy necessary files to artifact folder
echo -e "${GREEN}📋 Copying files to artifact...${NC}"
cp deploy/docker-compose.yml ${ARTIFACT_FOLDER}/
cp deploy/run.sh ${ARTIFACT_FOLDER}/
cp deploy/README.md ${ARTIFACT_FOLDER}/

# Update artifact docker-compose.yml with correct image name and version
echo -e "${GREEN}📝 Updating artifact with correct image name...${NC}"
# Replace the image name with the correct Docker Hub username and version
sed -i.bak "s|image: wayback-scraper|image: ${DOCKERHUB_USERNAME}/wayback-scraper:${VERSION}|g" ${ARTIFACT_FOLDER}/docker-compose.yml
rm -f ${ARTIFACT_FOLDER}/docker-compose.yml.bak
echo -e "${GREEN}✅ Updated artifact docker-compose.yml${NC}"

# Step 4: Create GitHub Release with artifact
echo -e "${GREEN}📦 Creating GitHub Release with artifact...${NC}"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) not found. Installing artifact locally...${NC}"
    echo -e "${YELLOW}📝 To create GitHub Release, install GitHub CLI: https://cli.github.com/${NC}"
    
    # Create local zip file
    echo -e "${GREEN}📦 Creating local artifact zip...${NC}"
    zip -r ${ARTIFACT_FOLDER}-v${VERSION}.zip ${ARTIFACT_FOLDER}/
    echo -e "${GREEN}✅ Created ${ARTIFACT_FOLDER}-v${VERSION}.zip${NC}"
    echo -e "${YELLOW}📝 You can manually upload this zip to GitHub Releases${NC}"
else
    # Create zip file
    echo -e "${GREEN}📦 Creating artifact zip...${NC}"
    zip -r ${ARTIFACT_FOLDER}-v${VERSION}.zip ${ARTIFACT_FOLDER}/
    
    # Create git tag
    echo -e "${GREEN}🏷️  Creating git tag...${NC}"
    git tag ${TAG}
    git push origin ${TAG}
    
    # Create GitHub Release
    echo -e "${GREEN}📤 Creating GitHub Release...${NC}"
    gh release create ${TAG} \
        --title "Wayback Scraper v${VERSION}" \
        --notes "Ready-to-use artifact for Wayback Scraper v${VERSION}

## What's included:
- docker-compose.yml (runs the containerized scraper)
- run.sh (setup and execution script)
- README.md (quick start guide)

## Quick Start:
1. Download and extract this zip
2. Create a data.csv file with your URLs and deal dates
3. Run: ./run.sh

## Image:
- Docker image: ${FULL_IMAGE_NAME}:${VERSION}" \
        ${ARTIFACT_FOLDER}-v${VERSION}.zip
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ GitHub Release created successfully!${NC}"
        echo -e "${YELLOW}📦 Download URL: https://github.com/${DOCKERHUB_USERNAME}/wayback_scraper/releases/latest${NC}"
    else
        echo -e "${RED}❌ Failed to create GitHub Release${NC}"
        echo -e "${YELLOW}📝 Created local zip file: ${ARTIFACT_FOLDER}-v${VERSION}.zip${NC}"
    fi
fi

# Clean up artifact folder
echo -e "${GREEN}🧹 Cleaning up artifact folder...${NC}"
rm -rf ${ARTIFACT_FOLDER}

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${YELLOW}📋 Image URLs: ${FULL_IMAGE_NAME}:latest and ${FULL_IMAGE_NAME}:${VERSION}${NC}"
echo -e "${YELLOW}📦 Artifact available as downloadable zip${NC}"
echo -e "${YELLOW}🌐 GitHub Release created with artifact${NC}" 
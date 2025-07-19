FROM ruby:3.4.4-alpine
USER root

WORKDIR /build

# Install SOCKS5 support
RUN apk add --no-cache socksify

# Copy wayback-machine-downloader files
COPY wayback-machine-downloader/ /build/

RUN bundle config set jobs "$(nproc)" \
    && bundle config set without 'development test' \
    && bundle install

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Set up application directory
WORKDIR /app

# Copy only the necessary Python files
COPY requirements.txt .
COPY wayback_scraper.py .

# Install Python dependencies with --break-system-packages flag to override PEP 668 protection
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Create downloads directory
RUN mkdir -p downloads


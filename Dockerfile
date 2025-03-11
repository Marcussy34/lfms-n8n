# Use the latest n8n base image
FROM n8nio/n8n:latest

# Switch to root user to install packages
USER root

# Install required packages
RUN apk add --no-cache \
    tesseract-ocr \
    poppler-utils \
    tesseract-ocr-data-eng \
    && mkdir -p /usr/share/tessdata \
    && wget -O /usr/share/tessdata/msa.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/msa.traineddata

# Switch back to the default n8n user
USER node 
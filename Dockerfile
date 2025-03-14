# Use the latest n8n base image
FROM n8nio/n8n:latest

# Switch to root user to install packages
USER root

# Install required packages
RUN apk add --no-cache \
    tesseract-ocr \
    poppler-utils \
    tesseract-ocr-data-eng \
    python3 \
    py3-pip \
    # Add build dependencies for Python packages
    build-base \
    python3-dev \
    && mkdir -p /usr/share/tessdata \
    && wget -O /usr/share/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata \
    && wget -O /usr/share/tessdata/msa.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/msa.traineddata

# Create a virtual environment and install Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/pip install --no-cache-dir spacy regex
RUN /opt/venv/bin/python -m spacy download en_core_web_sm

# Switch back to the default n8n user
USER node

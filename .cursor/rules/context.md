# Bank Document Information Extraction Project

## Overview

This project implements a Named Entity Recognition (NER) system for extracting structured information from bank documents using spaCy. The core component is a Python script (`extract_entities.py`) that processes text files and extracts various fields including bank names, monetary amounts, property details, and location information.

## System Components

### Core Files

- `extract_entities.py`: Main Python script for entity extraction
- `requirements.txt`: Python dependencies (spaCy, regex)
- `README.md`: Project documentation

### Configuration

- `.gitignore`: Modified to include `extract_entities.py` and `requirements.txt`

## Functionality

### Entity Extraction

The system extracts the following types of information:

- Bank name
- Monetary amounts (earnest_deposit, deposit, amount, mrta_amount, balance)
- Formatted amounts (\_print_as and \_in_word variants)
- Address information
- Property details (HSD_No, PTD_No, Parcel_No, etc.)
- Location information (district, state, sub_district, land_office, tenure)
- Title information (title, description, type, category)
- Company information

### Database Schema Alignment

- Most fields required by the database schema are directly extracted
- `price_print_as` and `price_in_word` fields need to be mapped from existing `amount_print_as` and `amount_in_word` fields

## Deployment

### Docker Environment

- Configured to run with n8n
- Supports different hardware setups (Nvidia GPU, AMD GPU, or CPU)
- Includes OCR capabilities via tesseract-ocr
- Includes PDF processing via poppler-utils

### File Structure

- Shared directory mounted at `/data/shared` in the container
- All files for processing should be placed in this directory

## Workflow

1. Obtain PDF documents
2. Convert PDFs to text using OCR (tesseract)
3. Process text with the NER script
4. Handle the extracted JSON data

### Processing Options

- Process individual files
- Process all text files in a directory
- Read from standard input
- Output results as JSON

## Usage Examples

### Process all text files in a directory:

```
/opt/venv/bin/python /data/shared/extract_entities.py /data/shared /data/shared/output.json
```

### Process a specific file:

```
/opt/venv/bin/python /data/shared/extract_entities.py /data/shared/input.txt /data/shared/output.json
```

### Complete workflow example:

1. Use a **Read Binary File** or **HTTP Request** node to obtain a PDF document
2. Save the PDF to `/data/shared/document.pdf` with a **Write Binary File** node
3. Run OCR on the PDF using Tesseract:
   ```
   tesseract /data/shared/document.pdf /data/shared/input -l eng
   ```
4. Execute the NER extraction:
   ```
   /opt/venv/bin/python /data/shared/extract_entities.py /data/shared/input.txt /data/shared/output.json
   ```
5. Read the output JSON file with a **Read Binary File** node
6. Parse the extracted data with a **JSON Parse** node
7. Process the data as needed (e.g., insert into a database)

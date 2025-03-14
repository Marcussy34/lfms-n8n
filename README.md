# Bank Document Information Extraction

This project provides tools for extracting structured information from bank documents using Named Entity Recognition (NER) and pattern matching with spaCy.

## Features

✅ **PDF Processing** - Using `poppler-utils` for PDF manipulation
✅ **OCR Capabilities** - Using `tesseract-ocr` for text extraction from images
✅ **NER Extraction** - Using `spaCy` for entity recognition and pattern matching
✅ **Multi-language Support** - Including English and Malaysian (MSA) language support

## Extracted Entities

The system extracts the following types of information:

- Bank name
- Monetary amounts (earnest_deposit, deposit, amount, mrta_amount, balance)
- Formatted amounts (\_print_as and \_in_word variants)
- Address information
- Property details (HSD_No, PTD_No, Parcel_No, etc.)
- Location information (district, state, sub_district, land_office, tenure)
- Title information (title, description, type, category)
- Company information

## Setup

### Using Docker

The project is set up to run in a Docker environment with n8n:

```bash
# For Nvidia GPU users
docker compose --profile gpu-nvidia up

# For AMD GPU users
docker compose --profile gpu-amd up

# For CPU users
docker compose --profile cpu up
```

The first build will take longer as it installs the OCR, PDF processing tools, and Python dependencies.

### Manual Setup

If you want to run the extraction script directly:

1. Install the required dependencies:

```bash
pip install -r shared/requirements.txt
python -m spacy download en_core_web_sm
```

## Usage

### In n8n Workflow

Use the Execute Command node with this command to process all text files in the shared directory:

```
/opt/venv/bin/python /data/shared/extract_entities.py /data/shared /data/shared/output.json
```

For processing a specific file:

```
/opt/venv/bin/python /data/shared/extract_entities.py /data/shared/input.txt /data/shared/output.json
```

### Direct Script Usage

#### Process a single document:

```bash
python extract_entities.py path/to/document.txt
```

The extraction results will be printed as JSON to the console.

#### Process a single document and save results to a file:

```bash
python extract_entities.py path/to/document.txt output.json
```

#### Process all .txt documents in a directory:

```bash
python extract_entities.py path/to/directory/ output.json
```

### Complete Workflow Example

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

## Customization

You can customize the extraction patterns by editing the regular expressions in the script. Each entity type has its own extraction function that can be modified independently.

## Accessing Local Files

The shared folder is mounted to the n8n container and allows n8n to access files on disk. This folder within the n8n container is located at `/data/shared` -- this is the path you'll need to use in nodes that interact with the local filesystem.

## Available OCR Tools

- **pdftoppm**: Convert PDF files to images
- **tesseract**: Extract text from images with OCR
- **Supported Languages**:
  - English (default)
  - Malaysian (MSA)
  - Additional languages can be added by modifying the Dockerfile

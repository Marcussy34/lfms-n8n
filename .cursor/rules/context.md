# Project Status Summary

We've set up a Named Entity Recognition (NER) system for extracting structured information from bank documents using spaCy. The system consists of a Python script (extract_entities.py) that processes text files and extracts fields like bank names, monetary amounts, property details, and location information. We've modified the script to exclude processing of requirements.txt and updated the .gitignore file to include both extract_entities.py and requirements.txt for version control. We've also consolidated documentation by merging README_NER.md into the main README.md, removing generic content about the n8n starter kit and focusing solely on the NER functionality.

The extraction script successfully extracts most fields required by the database schema, including bank information, monetary amounts (with formatted versions), property details, location information, and title information. The only fields in the schema not directly extracted are price_print_as and price_in_word, which may need to be mapped from the existing amount_print_as and amount_in_word fields. The script is designed to process either individual files or all text files in a directory, outputting results as JSON. It also includes functionality to read from standard input, making it flexible for integration with n8n workflows.

The system is configured to run in a Docker environment with n8n, with commands provided for different hardware setups (Nvidia GPU, AMD GPU, or CPU). The Docker setup includes OCR capabilities via tesseract-ocr and PDF processing via poppler-utils, allowing for a complete document processing pipeline. The shared directory is mounted at /data/shared in the container, which is where files should be placed for processing.

## Workflow

1. Obtain PDF documents through webhook
2. Convert PDFs to PNG images using pdftoppm
3. Extract text from PNG images using OCR (tesseract)
4. Process extracted text with the NER script
5. Output the extracted data as JSON

### Processing Options

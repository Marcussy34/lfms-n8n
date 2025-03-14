# NER Document Extraction with spaCy

This script uses Named Entity Recognition (NER) and pattern matching to extract structured information from bank documents.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage

### Process a single document:

```bash
python extract_entities.py path/to/document.txt
```

The extraction results will be printed as JSON to the console.

### Process a single document and save results to a file:

```bash
python extract_entities.py path/to/document.txt output.json
```

### Process all .txt documents in a directory:

```bash
python extract_entities.py path/to/directory/ output.json
```

## Extracted Entities

The script extracts the following types of information:

- Bank name
- Monetary amounts (earnest_deposit, deposit, amount, mrta_amount, balance)
- Formatted amounts (_\_print_as and _\_in_word variants)
- Address information
- Property details (HSD_No, PTD_No, Parcel_No, etc.)
- Location information (district, state, sub_district, land_office, tenure)
- Title information (title, description, type, category)

## Customization

You can customize the extraction patterns by editing the regular expressions in the script. Each entity type has its own extraction function that can be modified independently.

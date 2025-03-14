import spacy
import re
import json
import os
import sys
from pathlib import Path

# Load spaCy model - using the en_core_web_sm model for pattern matching
def load_spacy_model():
    try:
        nlp = spacy.load("en_core_web_sm")
        print("SpaCy model loaded successfully")
        return nlp
    except OSError:
        # If model not found, download it
        print("Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_sm")
        try:
            nlp = spacy.load("en_core_web_sm")
            print("SpaCy model downloaded and loaded successfully")
            return nlp
        except Exception as e:
            print(f"Error loading spaCy model: {e}")
            sys.exit(1)

def clean_text(text):
    """Clean up OCR noise in the text"""
    # Remove common OCR artifacts
    text = re.sub(r'CamScanner', '', text)
    # Replace common OCR errors
    text = re.sub(r'\u2018', "'", text)  # Replace left single quotation mark
    text = re.sub(r'\u2019', "'", text)  # Replace right single quotation mark
    text = re.sub(r'\u201c', '"', text)  # Replace left double quotation mark
    text = re.sub(r'\u201d', '"', text)  # Replace right double quotation mark
    # Replace non-standard hyphens and dashes
    text = re.sub(r'[\u2010-\u2015]', '-', text)
    # Replace OCR errors in numbers - use a function to handle the replacements
    text = re.sub(r'(\d)[oO](\d)', lambda m: m.group(1) + '0' + m.group(2), text)
    # Fix common OCR errors in bank-specific text
    text = re.sub(r'Temtoanst', 'Term Loan', text)
    text = re.sub(r'trest', 'interest', text)
    text = re.sub(r'Bark\'s', 'Bank\'s', text)
    # Fix common OCR errors in decimal points
    text = re.sub(r'(\d+)[,\'](\d+)[-:](\d+)', r'\1\2.\3', text)  # Convert 7000,006:00 to 7000006.00
    text = re.sub(r'(\d+)[-:](\d+)', r'\1.\2', text)  # Convert 7000-00 to 7000.00
    # Clean up messy line spacing but preserve some structure
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def extract_bank_name(text):
    """Extract bank name from the text"""
    # Common bank names pattern
    bank_patterns = [
        r"United Overseas Bank \(Malaysia\) Bhd",
        r"United Overseas Bank",
        r"UOB Bank",
        r"UOB",
        r"Maybank",
        r"CIMB Bank",
        r"HSBC Bank",
        r"RHB Bank",
        r"Public Bank Berhad",
        r"Public Bank",
        r"AmBank",
        # Add more bank names as needed
    ]
    
    for pattern in bank_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

def extract_amounts(text):
    """Extract various amounts from the text"""
    result = {}
    
    # First try UOB-specific format extraction
    uob_amounts = extract_amount_from_uob_format(text)
    if uob_amounts:
        result.update(uob_amounts)
    
    # Pattern for monetary amounts
    amount_patterns = {
        "earnest_deposit": r"[Ee]arnest\s+[Dd]eposit\s+(?:[Oo]f\s+)?(?:RM|MYR|Ringgit Malaysia)?\s*([\d,]+\.?\d{0,2})",
        "deposit": r"[Dd]eposit\s+(?:[Oo]f\s+)?(?:RM|MYR|Ringgit Malaysia)?\s*([\d,]+\.?\d{0,2})",
        "amount": r"[Aa]mount\s+(?:[Oo]f\s+)?(?:RM|MYR|Ringgit Malaysia)?\s*([\d,]+\.?\d{0,2})",
        "mrta_amount": r"MRTA\s+[Aa]mount\s+(?:[Oo]f\s+)?(?:RM|MYR|Ringgit Malaysia)?\s*([\d,]+\.?\d{0,2})",
        "balance": r"[Bb]alance\s+(?:[Oo]f\s+)?(?:RM|MYR|Ringgit Malaysia)?\s*([\d,]+\.?\d{0,2})"
    }
    
    # Extract raw amount values
    for field, pattern in amount_patterns.items():
        match = re.search(pattern, text)
        if match:
            try:
                # Remove commas and convert to float
                amount_str = match.group(1).replace(',', '')
                # Add .00 if no decimal points
                if '.' not in amount_str:
                    amount_str += '.00'
                amount_value = float(amount_str)
                
                # Only update if not already set by UOB specific extraction
                if field not in result:
                    result[field] = amount_value
                    result[f"{field}_print_as"] = f"RM {match.group(1)}"
                    result[f"{field}_in_word"] = f"Ringgit Malaysia {match.group(1)} only"
            except (ValueError, TypeError) as e:
                print(f"Error converting amount for {field}: {e}")
    
    # If still no amount found, try the general extraction approaches
    if "amount" not in result:
        try:
            # First approach - look for the facility section that has limits and descriptions
            facilities_section = re.search(r"Approved\s+Limit\s+(?:Banking\s+Facilities)?.*?TOTAL", text, re.DOTALL)
            
            if facilities_section:
                section_text = facilities_section.group(0)
                
                # Look for Term Loan amounts - UOB format usually has a specific layout
                term_loan_matches = re.findall(r"([\d,\.]+)\s*(?:Term\s+Loan|TL)", section_text, re.IGNORECASE)
                
                if term_loan_matches and len(term_loan_matches) > 0 and "amount" not in result:
                    amount_str = term_loan_matches[0].replace(',', '')
                    if '.' not in amount_str:
                        amount_str += '.00'
                        
                    try:
                        amount_value = float(amount_str)
                        result["amount"] = amount_value
                        result["amount_print_as"] = f"RM {term_loan_matches[0]}"
                        result["amount_in_word"] = f"Ringgit Malaysia {term_loan_matches[0]} only"
                    except (ValueError, TypeError) as e:
                        print(f"Error converting term loan amount: {e}")
                
                # Look for total facility amount
                total_match = re.search(r"TOTAL\s+([\d,\.]+)", section_text, re.IGNORECASE)
                if total_match and "amount" not in result:
                    total_str = total_match.group(1).replace(',', '')
                    if '.' not in total_str:
                        total_str += '.00'
                        
                    try:
                        total_value = float(total_str)
                        result["amount"] = total_value
                        result["amount_print_as"] = f"RM {total_match.group(1)}"
                        result["amount_in_word"] = f"Ringgit Malaysia {total_match.group(1)} only"
                    except (ValueError, TypeError) as e:
                        print(f"Error converting total amount: {e}")
        
            # Second approach - extract amounts with Term Loan description
            if "amount" not in result:
                # Look for patterns like "7,000,000.00 Term Loan (TL)"
                term_loan_pattern = r"(?:RM)?\s*([\d,]+(?:\.?\d{0,2}))\s*(?:Term\s+Loan|TL)"
                term_loan_match = re.search(term_loan_pattern, text, re.IGNORECASE)
                
                if term_loan_match:
                    try:
                        amount_str = term_loan_match.group(1).replace(',', '')
                        if '.' not in amount_str:
                            amount_str += '.00'
                        amount_value = float(amount_str)
                        result["amount"] = amount_value
                        result["amount_print_as"] = f"RM {term_loan_match.group(1)}"
                        result["amount_in_word"] = f"Ringgit Malaysia {term_loan_match.group(1)} only"
                    except (ValueError, TypeError) as e:
                        print(f"Error converting term loan amount: {e}")
            
            # Third approach - extract from specific UOB format with quotes and colons
            if "amount" not in result:
                # UOB format with quotes and colons - like 7000,006:00" Term Loan
                special_pattern = r"[\"\']*(?:RM)?\s*([\d,]+)[\"\']*[\.\:][\"\']*(\d{2})[\"\']*\s*(?:Term\s+Loan|TL)"
                special_match = re.search(special_pattern, text)
                
                if special_match:
                    try:
                        # Combine the parts like "7000,006" and "00" into "7000006.00"
                        amount_str = special_match.group(1).replace(',', '') + '.' + special_match.group(2)
                        amount_value = float(amount_str)
                        result["amount"] = amount_value
                        result["amount_print_as"] = f"RM {special_match.group(1)}.{special_match.group(2)}"
                        result["amount_in_word"] = f"Ringgit Malaysia {special_match.group(1)}.{special_match.group(2)} only"
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error converting special format amount: {e}")
        
        except Exception as e:
            print(f"Error in amount extraction: {e}")
    
    return result

def extract_address(text):
    """Extract address information"""
    # Patterns for address extraction
    address_patterns = [
        r"(?:located at|situate at|address[^\n]+)([^\n]+)",
        r"(?:No\.\s*\d+[^,\n]+,[^,\n]+,[^,\n]+\d{5})",
        r"(?:property at|situate at|located at)[^\n]*?([^\n]+(?:Road|Street|Avenue|Lane|Drive|Boulevard|Heights)[^\n]*)",
        # UOB-specific patterns
        r"Level\s+\d+,\s+[^,\n]+,\s+[^,\n]+,\s+[^,\n]+\d{5}",
        r"Level\s+\d+,\s+UOB\s+Plaza\s+\d\s+(?:Kuala\s+Lumpur)?\s*No\.\s*\d+[^,\n]+,[^,\n]*\d{5}"
    ]
    
    for pattern in address_patterns:
        address_match = re.search(pattern, text, re.IGNORECASE)
        if address_match:
            address = address_match.group(1).strip() if len(address_match.groups()) > 0 else address_match.group(0).strip()
            # Clean up address by removing common OCR errors
            address = re.sub(r'[\u2018\u2019\u201c\u201d]', '', address)
            return address
    
    # Try to extract specific UOB address from multiple lines
    lines = text.split('\n')
    address_lines = []
    address_started = False
    
    for line in lines:
        if re.search(r"Level\s+\d+.*UOB\s+Plaza", line):
            address_started = True
            address_lines.append(line.strip())
        elif address_started and re.search(r"^\s*No\.\s*\d+|^\s*\d{5}", line):
            address_lines.append(line.strip())
        elif address_started and len(address_lines) > 0 and re.search(r"\d{5}", line):
            address_lines.append(line.strip())
            break
    
    if address_lines:
        return " ".join(address_lines)
    
    return None

def extract_property_details(text):
    """Extract property details like HSD_No, PTD_No, etc."""
    result = {}
    
    # Patterns for property identifiers
    property_patterns = {
        "HSD_No": r"HSD\s*No\.?\s*[:-]?\s*(\w+)",
        "PTD_No": r"PTD\s*No\.?\s*[:-]?\s*(\w+)",
        "Parcel_No": r"Parcel\s*No\.?\s*[:-]?\s*(\w+)",
        "Unit_No": r"Unit\s*No\.?\s*[:-]?\s*(\w+)",
        "Storey_No": r"Storey\s*No\.?\s*[:-]?\s*(\w+)",
        "Car_Park_No": r"Car\s*Park\s*No\.?\s*[:-]?\s*(\w+)",
        "residential_area": r"[Rr]esidential\s+[Aa]rea\s*[:-]?\s*([^,\.\n]+)"
    }
    
    for field, pattern in property_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()
    
    return result

def extract_location_info(text):
    """Extract location information like district, state, etc."""
    result = {}
    
    # Patterns for location identifiers
    location_patterns = {
        "district": r"[Dd]istrict\s*[Oo]f\s*([^,\.\n]+)",
        "state": r"[Ss]tate\s*[Oo]f\s*([^,\.\n]+)",
        "sub_district": r"[Ss]ub[\-\s][Dd]istrict\s*[Oo]f\s*([^,\.\n]+)",
        "land_office": r"[Ll]and\s*[Oo]ffice\s*[Oo]f\s*([^,\.\n]+)",
        "tenure": r"[Tt]enure\s*[:-]?\s*([^,\.\n]+)"
    }
    
    for field, pattern in location_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()
    
    # Try to extract state from UOB address
    state_match = re.search(r"(\d{5})\s+([^,\.\n]+),\s+Malaysia", text)
    if state_match and "state" not in result:
        result["state"] = state_match.group(2).strip()
    
    return result

def extract_title_info(text):
    """Extract title information such as title, description, type, category"""
    result = {}
    
    # Patterns for title information
    title_patterns = {
        "title": r"[Tt]itle\s*[:-]?\s*([^,\.\n]+)",
        "description": r"[Dd]escription\s*[:-]?\s*([^,\.\n]+)",
        "type": r"[Pp]roperty\s+[Tt]ype\s*[:-]?\s*([^,\.\n]+)",
        "category": r"[Cc]ategory\s*[:-]?\s*([^,\.\n]+)",
        "title_description": r"[Tt]itle\s+[Dd]escription\s*[:-]?\s*([^,\.\n]+)"
    }
    
    for field, pattern in title_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()
    
    # Extract information from the Subject line which often contains description
    subject_match = re.search(r"Subject\s*:\s*([^\.]+)", text)
    if subject_match and "description" not in result:
        result["description"] = subject_match.group(1).strip()
    
    return result

def extract_company_info(text):
    """Extract company information"""
    result = {}
    
    # Extract company registration number
    reg_match = re.search(r"(?:Company|Registration|Co|Reg)\.?\s*No\.?[:\s]*(\d+[-\s]*\d+(?:[-\s]*[A-Z])?)", text)
    if reg_match:
        result["company_reg_no"] = reg_match.group(1).strip()
    
    # Extract company name for UOB documents
    company_match = re.search(r"([A-Za-z\s]+)\s+(?:Sdn\.?\s*Bhd|Berhad)\.?\s*\((\d+)\)", text)
    if company_match:
        result["company_name"] = f"{company_match.group(1).strip()} Sdn Bhd ({company_match.group(2).strip()})"
    
    return result

def extract_amount_from_uob_format(text):
    """Extract loan amounts from UOB's specific format"""
    result = {}
    
    try:
        # Extract Term Loan amount from the UOB specific format
        # Look for the specific format from UOB Bank-01: "7000,006:00" Temtoanst(TL)
        term_loan_match = re.search(r"[\"\']?([\d,]+)[,\']?([\d]+)[:\"\']-?([\d]+)[\"\']?\s*(?:Term\s+Loan|Temtoanst|TL)", text)
        if term_loan_match:
            try:
                # Combine the parts like "7000", "006", "00" into "7000006.00"
                amount_str = term_loan_match.group(1).replace(',', '') + term_loan_match.group(2) + '.' + term_loan_match.group(3)
                amount_value = float(amount_str)
                result["amount"] = amount_value
                result["amount_print_as"] = f"RM {term_loan_match.group(1)},{term_loan_match.group(2)}.{term_loan_match.group(3)}"
                result["amount_in_word"] = f"Ringgit Malaysia {term_loan_match.group(1)},{term_loan_match.group(2)}.{term_loan_match.group(3)} only"
                return result
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error converting UOB specific format: {e}")
        
        # Try another pattern for Term Loan 2
        term_loan2_match = re.search(r"([\d]+)([\d]{3})([\d]{3})[-:]([\d]+)\s*(?:Term\s+Loan\s+2|TL2)", text)
        if term_loan2_match:
            try:
                # Combine the parts like "5", "000", "000", "00" into "5000000.00"
                amount_str = term_loan2_match.group(1) + term_loan2_match.group(2) + term_loan2_match.group(3) + '.' + term_loan2_match.group(4)
                amount_value = float(amount_str)
                result["amount"] = amount_value
                result["amount_print_as"] = f"RM {term_loan2_match.group(1)},{term_loan2_match.group(2)},{term_loan2_match.group(3)}.{term_loan2_match.group(4)}"
                result["amount_in_word"] = f"Ringgit Malaysia {term_loan2_match.group(1)},{term_loan2_match.group(2)},{term_loan2_match.group(3)}.{term_loan2_match.group(4)} only"
                return result
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error converting Term Loan 2 format: {e}")
        
        # Try total pattern
        total_match = re.search(r"([\d])([\d]{3})([\d]{3})([\d]{3})\s*TOTAL", text)
        if total_match:
            try:
                # Combine the parts like "1", "425", "000", "000" into "1425000000"
                amount_str = total_match.group(1) + total_match.group(2) + total_match.group(3) + total_match.group(4)
                amount_value = float(amount_str)
                result["amount"] = amount_value
                result["amount_print_as"] = f"RM {total_match.group(1)},{total_match.group(2)},{total_match.group(3)},{total_match.group(4)}.00"
                result["amount_in_word"] = f"Ringgit Malaysia {total_match.group(1)},{total_match.group(2)},{total_match.group(3)},{total_match.group(4)}.00 only"
                return result
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error converting Total format: {e}")
        
    except Exception as e:
        print(f"Error in UOB format extraction: {e}")
    
    return result

def process_document(file_path):
    """Process a document file and extract all required entities"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}
    
    # Load spaCy model
    nlp = load_spacy_model()
    
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Create a dictionary to store all extracted entities
    results = {}
    
    # Save cleaned text for debugging
    results["_cleaned_text"] = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
    
    # Use spaCy for basic text processing
    doc = nlp(cleaned_text)
    
    # Extract various entities
    results["bank_name"] = extract_bank_name(cleaned_text)
    
    # Extract amounts and their variations
    amount_results = extract_amounts(cleaned_text)
    results.update(amount_results)
    
    # Extract address
    address = extract_address(cleaned_text)
    if address:
        results["address"] = address
    
    # Extract property details
    property_details = extract_property_details(cleaned_text)
    results.update(property_details)
    
    # Extract location information
    location_info = extract_location_info(cleaned_text)
    results.update(location_info)
    
    # Extract title information
    title_info = extract_title_info(cleaned_text)
    results.update(title_info)
    
    # Extract company information
    company_info = extract_company_info(cleaned_text)
    results.update(company_info)
    
    # Use spaCy NER for additional entity extraction
    for ent in doc.ents:
        if ent.label_ == "ORG" and "bank_name" not in results:
            results["bank_name"] = ent.text
        elif ent.label_ == "GPE" and "state" not in results:  # Geographic/Political Entity
            results["state"] = ent.text
    
    # Remove cleaned text in final output if not in debug mode
    if not os.environ.get('DEBUG'):
        results.pop('_cleaned_text', None)
    
    return results

def process_all_documents(directory, output_file=None):
    """Process all text documents in a directory"""
    results = {}
    
    for file_name in os.listdir(directory):
        if file_name.endswith('.txt'):
            file_path = os.path.join(directory, file_name)
            print(f"Processing {file_path}...")
            doc_results = process_document(file_path)
            results[file_name] = doc_results
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    
    return results

def main():
    """Main function to process the documents"""
    if len(sys.argv) < 2:
        print("Usage: python extract_entities.py <document_path_or_directory> [output_file]")
        print("  document_path_or_directory: Path to a single document or directory containing documents")
        print("  output_file: Optional path to save results as JSON")
        print("\nOptions:")
        print("  Set DEBUG=1 environment variable to include cleaned text in output")
        print("  Use '-' as document_path to read from standard input")
        return
    
    path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if path == '-':
        # Read from standard input
        print("Reading from standard input...")
        text = sys.stdin.read()
        results = process_text(text)
    elif os.path.isdir(path):
        print(f"Processing all .txt files in directory: {path}")
        results = process_all_documents(path, output_file)
        # If output_file is provided, results are already saved in process_all_documents
        if output_file:
            return
    elif os.path.exists(path):
        results = process_document(path)
    else:
        # If the specific file doesn't exist but the directory does, process all files in the directory
        dir_path = os.path.dirname(path)
        if os.path.isdir(dir_path):
            print(f"File {path} not found. Processing all .txt files in directory: {dir_path}")
            results = process_all_documents(dir_path, output_file)
            # If output_file is provided, results are already saved in process_all_documents
            if output_file:
                return
        else:
            print(f"Error: Path {path} does not exist")
            return
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    else:
        # Output the results as JSON to stdout
        print(json.dumps(results, indent=2))

def process_text(text):
    """Process text directly instead of reading from a file"""
    # Load spaCy model
    nlp = load_spacy_model()
    
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Create a dictionary to store all extracted entities
    results = {}
    
    # Save cleaned text for debugging
    results["_cleaned_text"] = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
    
    # Use spaCy for basic text processing
    doc = nlp(cleaned_text)
    
    # Extract various entities
    results["bank_name"] = extract_bank_name(cleaned_text)
    
    # Extract amounts and their variations
    amount_results = extract_amounts(cleaned_text)
    results.update(amount_results)
    
    # Extract address
    address = extract_address(cleaned_text)
    if address:
        results["address"] = address
    
    # Extract property details
    property_details = extract_property_details(cleaned_text)
    results.update(property_details)
    
    # Extract location information
    location_info = extract_location_info(cleaned_text)
    results.update(location_info)
    
    # Extract title information
    title_info = extract_title_info(cleaned_text)
    results.update(title_info)
    
    # Extract company information
    company_info = extract_company_info(cleaned_text)
    results.update(company_info)
    
    # Use spaCy NER for additional entity extraction
    for ent in doc.ents:
        if ent.label_ == "ORG" and "bank_name" not in results:
            results["bank_name"] = ent.text
        elif ent.label_ == "GPE" and "state" not in results:  # Geographic/Political Entity
            results["state"] = ent.text
    
    # Remove cleaned text in final output if not in debug mode
    if not os.environ.get('DEBUG'):
        results.pop('_cleaned_text', None)
    
    return results

if __name__ == "__main__":
    main() 
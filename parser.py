#!/usr/bin/env python3

import os
import re
import argparse
import pandas as pd
from bs4 import BeautifulSoup

def extract_eps_value(text):
    """
    Extracts and formats an EPS value from a string.
    Handles negative values in parentheses, formats to two decimal places,
    and ensures the value is plausible (e.g., between -25 and 25).
    """
    text = text.strip()
    value = None
    
    # Handle negative values in parentheses, e.g., (1.23) -> -1.23
    if text.startswith('(') and text.endswith(')'):
        try:
            value = -float(text[1:-1])
        except ValueError:
            return None
    # Handle regular positive or negative numbers
    else:
        try:
            # Remove currency symbols and commas for robust parsing
            text = text.replace('$', '').replace(',', '')
            value = float(text)
        except ValueError:
            return None

    # Sanity check for bounds and format the output
    if value is not None and -25 <= value <= 25:
        return "{:.2f}".format(value)
    else:
        return None

def find_eps_in_file(file_path):
    """
    Finds the highest-priority EPS value and the term that was matched in an HTML file.
    Returns a tuple of (value, term).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # --- Primary Search: Targeted Table Scan ---
        found_values = []
        
        # 1. Using the new comprehensive list of synonyms
        eps_terms = [
            # Core EPS Terms
            'earnings per basic share', 'basic earnings per share',
            'earnings per common share - basic', 'earnings per share - basic',
            'basic earnings per common share', 'earnings per common share',
            'earnings per share', 'eps',
            # Income-Based Variations
            'basic income per share', 'basic net income per share',
            'net income per share - basic', 'net income per common share - basic',
            'income per common share', 'net income per common share', 'income per share',
            'net income per share',
            # Profit-Based Variations
            'basic profit per share', 'profit per share',
            # Loss-Based Variations
            'basic loss per share', 'basic net loss per share',
            'net loss per common share - basic', 'loss per share', 'net loss per share',
            'net loss per common share', 'basic and diluted loss per share',
            # Combined Earnings/Loss Variations
            'earnings (loss) per basic share', 'earnings (loss) per share',
            'earnings (loss) per common share', 'net income (loss) per share',
            'net income (loss) per common share',
            # "Attributable to" Variations
            'earnings per share attributable to common stockholders',
            'net income attributable to common stockholders per common share',
            'net income per share available to common stockholders'
        ]
        
        table_headers = [
            'consolidated statements of operations',
            'consolidated statements of income',
            'consolidated statements of comprehensive income',
            'condensed consolidated statements of operations'
        ]

        # 2. Identify relevant financial tables based on headers
        target_tables = []
        for header_text in table_headers:
            # Find tags that are likely to be headers for the financial statements
            headers = soup.find_all(lambda tag: tag.name in ['p', 'b', 'strong', 'div'] and header_text in tag.get_text().lower())
            for header in headers:
                # Find the table immediately following the header
                table = header.find_next('table')
                if table:
                    target_tables.append(table)
        
        # 3. Search for EPS values ONLY within the identified tables
        if target_tables:
            for table in target_tables:
                rows = table.find_all('tr')
                for i, row in enumerate(rows):
                    row_text_lower = row.get_text().lower()
                    
                    # Find which term is in the row (our potential header row)
                    matched_term = None
                    for term in eps_terms:
                        if term in row_text_lower:
                            matched_term = term
                            break
                    
                    if matched_term:
                        # First, try to find the value in the same row as the term.
                        cells = row.find_all(['td', 'th'])
                        value_found_in_header_row = False
                        for cell in cells:
                            value = extract_eps_value(cell.get_text().strip())
                            if value is not None:
                                is_basic = 'basic' in row_text_lower
                                is_gaap = 'gaap' in row_text_lower or 'unadjusted' in row_text_lower
                                is_loss = 'loss' in row_text_lower or 'net loss' in row_text_lower
                                if is_loss and not value.startswith('-'):
                                    value = '-' + value
                                found_values.append({'value': value, 'term': matched_term, 'is_basic': is_basic, 'is_gaap': is_gaap})
                                value_found_in_header_row = True
                                break # Found value in this row, no need to check other cells
                        
                        # If no value was in the header row, search subsections in subsequent rows.
                        if not value_found_in_header_row:
                            # Look ahead up to 4 rows for the first numerical value.
                            for next_row in rows[i+1 : i+5]:
                                subsection_value_found = False
                                next_row_text_lower = next_row.get_text().lower()
                                next_cells = next_row.find_all(['td', 'th'])
                                for cell in next_cells:
                                    value = extract_eps_value(cell.get_text().strip())
                                    if value is not None:
                                        # This is the first numerical value in a subsequent row.
                                        is_basic = 'basic' in next_row_text_lower
                                        is_gaap = 'gaap' in next_row_text_lower or 'unadjusted' in next_row_text_lower
                                        is_loss = 'loss' in next_row_text_lower or 'net loss' in next_row_text_lower
                                        if is_loss and not value.startswith('-'):
                                            value = '-' + value
                                        
                                        # Use the original term from the header row.
                                        found_values.append({'value': value, 'term': matched_term, 'is_basic': is_basic, 'is_gaap': is_gaap})
                                        subsection_value_found = True
                                        break # Stop after finding the first value in the row.
                                
                                if subsection_value_found:
                                    break # Stop looking ahead after finding a value in a subsection row.
        
        # 4. Prioritize and return the best value and term found in tables
        if found_values:
            basic_values = [v for v in found_values if v['is_basic']]
            if basic_values: found_values = basic_values
            gaap_values = [v for v in found_values if v['is_gaap']]
            if gaap_values: found_values = gaap_values
            best_result = found_values[0]
            return best_result['value'], best_result['term']

        # --- Fallback Search 1: If nothing in tables, search entire text with specific terms ---
        all_text = soup.get_text()
        for term in eps_terms:
            try:
                # Use finditer to find all occurrences of the term, as whole words
                matches = re.finditer(r'\b' + re.escape(term) + r'\b', all_text, re.IGNORECASE)
                for match in matches:
                    # Look in a window of characters after the term for a number
                    context = all_text[match.end():match.end() + 100]
                    
                    # Regex to find numbers, including parenthesized negatives
                    number_match = re.search(r'\(?\s*\$?\s*(\d{1,3}(,\d{3})*|\d+)(\.\d{1,2})?\s*\)?', context)
                    
                    if number_match:
                        value = extract_eps_value(number_match.group(0))
                        if value is not None:
                            # As soon as we find a plausible value in the fallback, return it.
                            return value, term
            except re.error:
                # Ignore regex errors from complex terms and continue
                continue

        # --- Fallback Search 2: Broader "per share" Variations ---
        fallback_terms = [
            'per share', 'per basic share', 'per common share', 'per diluted share', 'per common stock'
        ]
        for term in fallback_terms:
            matches = re.finditer(term, all_text, re.IGNORECASE)
            for match in matches:
                context = all_text[match.end():match.end() + 50]
                number_match = re.search(r'\(?\s*\$?\s*(\d{1,3}(,\d{3})*|\d+)(\.\d{1,2})?\s*\)?', context)
                if number_match:
                    value = extract_eps_value(number_match.group(0))
                    if value is not None:
                        return value, term

        # --- No Value Found ---
        return None, None
        
    except Exception as e:
        return None, None

def process_directory(input_dir, output_file):
    """
    Processes all HTML files in a directory and writes the extracted EPS data to a CSV file.
    """
    results = []
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(input_dir, filename)
            eps_value, eps_term = find_eps_in_file(file_path)
            
            results.append({
                'filename': filename,
                'EPS': eps_value if eps_value is not None else 'NONE',
                'EPS_Term': eps_term if eps_term is not None else 'NONE'
            })
    
    # Create a pandas DataFrame and save it to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"Results written to {output_file}")

def main():
    """
    Main function to set up argument parsing and start the processing.
    """
    parser = argparse.ArgumentParser(description="Parse EDGAR 10-Q filings for companies' quarterly EPS.")
    parser.add_argument('input_dir', help='Input directory path containing HTML filings.')
    parser.add_argument('output_file', help='Output file path for the resulting CSV file.')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist.")
        return
    
    process_directory(args.input_dir, args.output_file)

if __name__ == '__main__':
    main() 
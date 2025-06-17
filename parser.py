#!/usr/bin/env python3

import os
import re
import argparse
import pandas as pd
from bs4 import BeautifulSoup

def clean_text(text):
    """Clean and normalize text for better pattern matching."""
    # Replace non-breaking spaces and normalize spaces
    text = text.replace('\xa0', ' ').replace('\n', ' ')
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_eps_value(text):
    # Remove any non-numeric characters except decimal points, minus signs, and parentheses
    text = text.strip()
    
    # Skip if the text looks like a year (e.g., 2020, 2019)
    if re.match(r'^[12]\d{3}$', text):
        return None
    
    # Handle values in parentheses (negative numbers)
    if text.startswith('(') and text.endswith(')'):
        try:
            # Remove parentheses and convert to float
            value = float(text[1:-1])
            # Skip if the value looks like a year
            if 1900 <= value <= 2100:
                return None
            return -value  # Make it negative
        except ValueError:
            return None
            
    # Handle regular numbers
    try:
        # Remove any currency symbols and commas
        text = text.replace('$', '').replace(',', '')
        value = float(text)
        # Skip if the value looks like a year
        if 1900 <= value <= 2100:
            return None
        return value
    except ValueError:
        return None

def find_eps_in_table(soup):
    """
    Look for EPS values in HTML tables.
    Returns the first valid EPS value found.
    """
    # Common EPS-related headers
    eps_headers = [
        'earnings per share', 'eps', 'basic eps', 'diluted eps',
        'loss per share', 'income per share', 'net income per share'
    ]
    
    for table in soup.find_all('table'):
        # Get all headers
        headers = []
        for th in table.find_all('th'):
            headers.append(th.get_text().lower().strip())
        
        # Check if any header contains EPS-related text
        has_eps_header = any(any(eps_term in header for eps_term in eps_headers) for header in headers)
        
        if has_eps_header:
            # Look for the first non-empty cell in the table
            for cell in table.find_all(['td', 'th']):
                text = cell.get_text().strip()
                if text and text != '.':
                    value = extract_eps_value(text)
                    if value is not None:
                        return value
    
    return None

def find_eps_in_text(text):
    # Clean and normalize the text
    text = clean_text(text)
    
    # Define patterns in order of priority
    patterns = [
        # Basic EPS patterns with more specific context
        r'basic\s+earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'basic\s+EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        
        # GAAP EPS patterns with more specific context
        r'gaap\s+earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'gaap\s+EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        
        # Unadjusted EPS patterns with more specific context
        r'unadjusted\s+earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'unadjusted\s+EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        
        # General EPS patterns with more specific context
        r'earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        
        # Loss per share patterns with more specific context
        r'loss\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'net\s+loss\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        
        # Diluted EPS patterns with more specific context
        r'diluted\s+earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'diluted\s+EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        
        # Adjusted/non-GAAP EPS patterns with more specific context
        r'adjusted\s+earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'adjusted\s+EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'non-gaap\s+earnings\s+per\s+share.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)',
        r'non-gaap\s+EPS.*?(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)'
    ]
    
    # Try each pattern
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = extract_eps_value(match.group(1))
            if value is not None:
                return value
                
    # If no pattern matches, try to find numbers near EPS-related terms
    eps_terms = ['eps', 'earnings per share', 'loss per share']
    for term in eps_terms:
        if term.lower() in text.lower():
            # Look for numbers within 50 characters before or after the term
            term_pos = text.lower().find(term.lower())
            context = text[max(0, term_pos - 50):min(len(text), term_pos + 50)]
            numbers = re.findall(r'(\$?\s*[\(]?\d+\.?\d*[\)]?)(?!\s*per\s+share)', context)
            for num in numbers:
                value = extract_eps_value(num)
                if value is not None:
                    return value
                    
    return None

def parse_html_file(file_path):
    """
    Parse an HTML file and extract EPS information.
    Returns the EPS value or None if not found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # First try to find EPS in tables
        eps_value = find_eps_in_table(soup)
        if eps_value is not None:
            return eps_value
        
        # If not found in tables, try the text content
        text = soup.get_text()
        eps_value = find_eps_in_text(text)
        return eps_value
    
    except Exception as e:
        print("Error processing {}: {}".format(file_path, str(e)))
        return None

def process_directory(input_dir, output_file):
    """
    Process all HTML files in the input directory and write results to CSV.
    """
    results = []
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(input_dir, filename)
            eps_value = parse_html_file(file_path)
            
            # Convert None to "NONE" string and ensure float values
            if eps_value is None:
                eps_value = "NONE"
            else:
                # Ensure the value is a float
                eps_value = float(eps_value)
            
            results.append({
                'filename': filename,
                'EPS': eps_value
            })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print("Results written to {}".format(output_file))

def main():
    parser = argparse.ArgumentParser(description='Parse EDGAR 10-Q filings for EPS data')
    parser.add_argument('input_dir', help='Input directory containing HTML filings')
    parser.add_argument('output_file', help='Output CSV file path')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print("Error: Input directory '{}' does not exist".format(args.input_dir))
        return
    
    process_directory(args.input_dir, args.output_file)

if __name__ == '__main__':
    main() 
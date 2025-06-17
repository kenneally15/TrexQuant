# Trexquant Data Engineer Project

Author: Kevin Kenneally  
Date: June 15, 2025

## Project Overview
This project parses EDGAR 10-Q filings to extract Earnings Per Share (EPS) data. The parser processes HTML files from SEC EDGAR filings and outputs the results in a CSV format.

## Features
- Extracts EPS values from HTML filings
- Handles various EPS formats and labels:
  - Basic EPS
  - GAAP EPS
  - Unadjusted EPS
  - General EPS
  - Loss per share
  - Diluted EPS
  - Adjusted/non-GAAP EPS
- Processes negative values (represented in parentheses)
- Ignores year values and other non-EPS numbers
- Outputs results in CSV format with "NONE" for missing values

## Requirements
- Python 3.x
- Required packages (see requirements.txt):
  - beautifulsoup4==4.12.2
  - pandas==2.1.0

## Usage
```bash
python parser.py <input_directory> <output_file>
```

### Arguments
- `input_directory`: Path to the directory containing HTML filings
- `output_file`: Path where the CSV output will be saved

### Example
```bash
python parser.py Training_Filings output.csv
```

## Output Format
The script generates a CSV file with two columns:
- `filename`: Name of the processed HTML file
- `EPS`: Extracted EPS value (or "NONE" if not found)

## Implementation Details
The parser uses several strategies to extract EPS values:
1. Searches for EPS values in HTML tables first
2. Falls back to text content if no table values are found
3. Uses regex patterns to identify EPS-related text
4. Prioritizes basic EPS over diluted EPS
5. Handles various number formats (including negative values in parentheses)
6. Filters out year values and other non-EPS numbers

## Error Handling
- Files that cannot be processed are logged with error messages
- Missing or invalid EPS values are marked as "NONE" in the output
- The script continues processing remaining files even if some files fail




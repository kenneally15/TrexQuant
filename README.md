# EDGAR 10-Q EPS Parser

This script, `parser.py`, is designed to parse quarterly EPS (Earnings Per Share) data from 10-Q filings from the U.S. Securities and Exchange Commission (SEC). It processes a directory of HTML files, extracts the most relevant EPS value from each, and compiles the results into a single CSV file.

## Features

- Extracts EPS data from financial tables within HTML filings.
- Prioritizes `basic` and `GAAP` (unadjusted) EPS values.
- Implements a multi-stage search strategy:
    1.  **Targeted Table Search:** First, it identifies financial tables (e.g., "Consolidated Statements of Operations") and searches for EPS values within them, including handling data in subsections.
    2.  **Full-Text Fallback:** If no value is found in the tables, it performs a fallback search through the entire document text using a comprehensive list of EPS-related terms.
- Handles negative values, which are often denoted with parentheses.
- Outputs a clean, three-column CSV file with the `filename`, the extracted `EPS`, and the specific `EPS_Term` that was matched.

## Setup and Installation

### Prerequisites
- Python 3.6+

### Environment Setup

1.  **Create a Virtual Environment:**
    It is highly recommended to run the script in a virtual environment to manage dependencies and avoid conflicts with system-wide packages.

    ```bash
    python3 -m venv venv
    ```

2.  **Activate the Virtual Environment:**

    -   On **macOS and Linux**:
        ```bash
        source venv/bin/activate
        ```
    -   On **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    Once the virtual environment is active, install the required packages from the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from the command line, providing the input directory containing the HTML filings and the desired path for the output CSV file.

```bash
python parser.py <input_dir> <output_file>
```

### Arguments

-   `<input_dir>`: The path to the directory containing the `.html` 10-Q filing files.
-   `<output_file>`: The path where the output CSV file will be saved (e.g., `output.csv`).

### Example

If your filings are in a directory named `Training_Filings`, you can run the script with the following command:

```bash
python parser.py Training_Filings results.csv
```

This will process all HTML files in the `Training_Filings` directory and create a file named `results.csv` with the extracted data.

## Known Limitations and Future Improvements

While the parser is robust, it does not handle every possible edge case found in the wild. Given more time, the parser could be expanded to handle more complex scenarios.

For instance, in file `0000895419-20-000042.html`, the correct EPS value is missed due to two primary challenges:

1.  **Complex Table Structures:** The table breaks down the primary "Basic and diluted loss per share" into further nested subsections like "Continuing operations attributable to controlling interest" and "Net loss attributable to controlling interest." The current logic does not traverse this deeply nested structure to link the value back to the parent EPS term.
2.  **Context-Dependent Fallback Search:** The fallback text search also fails. The relevant sentence is, *"GAAP net loss from continuing operations attributable to controlling interest for the third quarter was $61.6 million, or $0.57 per diluted share,"*. The parser's current context window is not wide enough to correctly associate the `$0.57` value with a primary EPS term across such a lengthy and complex phrase.

Future enhancements could focus on building a more sophisticated model for parsing highly nested tables and for understanding the wider context in free-text sentences.




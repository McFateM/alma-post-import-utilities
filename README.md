# alma-post-import-utilities
Flet app to assist with Alma management after import.

## Features

### CSV MMS ID Updater
The first view provides functionality to:
- Open a local CSV file
- Query Alma API for each row with a valid `originating_system_id` and empty `mms_id`
- Update the CSV with the corresponding MMS ID from Alma

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### CSV MMS ID Updater Instructions:
1. Enter your Alma API key in the provided field
2. Click "Select CSV File" to choose your CSV file
3. Ensure your CSV has these columns:
   - `originating_system_id`: The system ID to search for in Alma
   - `mms_id`: The field that will be updated (empty values will be filled)
4. Click "Process CSV" to start updating the MMS IDs
5. The application will update your CSV file in place

## CSV File Format

Your CSV file should have at least these two columns:
- `originating_system_id`: The originating system identifier used to query Alma
- `mms_id`: The MMS ID field (empty values will be populated)

Example CSV:
```csv
originating_system_id,mms_id,title
12345,,"Example Title 1"
67890,,"Example Title 2"
```

After processing:
```csv
originating_system_id,mms_id,title
12345,991234567890,"Example Title 1"
67890,991234567891,"Example Title 2"
```

## Alma API Configuration

You need an Alma API key with read access to bibliographic records. The application uses the Alma bibs API to search for records by `other_system_id`.

## Requirements

- Python 3.7+
- Flet 0.23.0+
- requests 2.31.0+

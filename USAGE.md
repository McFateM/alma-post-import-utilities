# Usage Examples

## Running the Application

### Basic Usage
```bash
python main.py
```

This will launch the Flet application in a window.

### Application Flow

1. **Enter API Key**: When the application starts, you'll see a text field to enter your Alma API key. The password field can be revealed if needed.

2. **Select CSV File**: Click the "Select CSV File" button to open a file picker dialog. Only CSV files will be shown.

3. **Process CSV**: Once both the API key and CSV file are selected, the "Process CSV" button becomes enabled. Click it to start processing.

4. **Monitor Progress**: The application will show real-time progress updates as it processes each row.

5. **Review Results**: After processing completes, you'll see a summary showing:
   - Updated: Number of rows where MMS ID was successfully retrieved and added
   - Skipped: Rows that already had an MMS ID or were missing originating_system_id
   - Not found: Rows where the originating_system_id didn't match any records in Alma

## CSV File Requirements

Your CSV file must include these columns (in any order):
- `originating_system_id`: The identifier to search for in Alma
- `mms_id`: The field where MMS IDs will be written (empty values will be filled)

Additional columns are preserved as-is.

### Example CSV Before Processing

```csv
originating_system_id,mms_id,title,author
oai:digital.library.edu:12345,,"Digital Collection Item 1","Smith, John"
oai:digital.library.edu:67890,,"Digital Collection Item 2","Doe, Jane"
oai:digital.library.edu:11111,991234567890,"Already Has MMS ID","Johnson, Bob"
oai:digital.library.edu:22222,,"Digital Collection Item 4","Brown, Alice"
```

### Example CSV After Processing

```csv
originating_system_id,mms_id,title,author
oai:digital.library.edu:12345,991234567891,"Digital Collection Item 1","Smith, John"
oai:digital.library.edu:67890,991234567892,"Digital Collection Item 2","Doe, Jane"
oai:digital.library.edu:11111,991234567890,"Already Has MMS ID","Johnson, Bob"
oai:digital.library.edu:22222,991234567893,"Digital Collection Item 4","Brown, Alice"
```

## API Key Setup

1. Log into your Ex Libris Developer Network account
2. Navigate to your API keys
3. Create or use an existing API key with "Bibs" read permissions
4. Copy the API key
5. Paste it into the application

## Troubleshooting

### "Error: CSV must have 'originating_system_id' and 'mms_id' columns"
- Check that your CSV has both required column headers
- Column names are case-sensitive

### "API error: 401"
- Your API key is invalid or expired
- Check that you've copied the entire API key

### "API error: 403"
- Your API key doesn't have the required permissions
- Ensure the key has read access to bibliographic records

### No MMS IDs found
- Check that your originating_system_id values match the format in Alma
- Verify the records exist in your Alma instance
- The API searches using the "other_system_id" parameter

## Advanced Configuration

### Using a Different Alma Region

The application defaults to the North America region. If you need to use a different region, modify the `AlmaAPIClient` initialization in `csv_processor.py`:

```python
# For Europe
client = AlmaAPIClient(api_key, base_url="https://api-eu.hosted.exlibrisgroup.com")

# For Asia-Pacific  
client = AlmaAPIClient(api_key, base_url="https://api-ap.hosted.exlibrisgroup.com")
```

## Sample Data

A sample CSV file (`sample_data.csv`) is included for testing purposes. You can use this to verify the application works before processing your actual data.

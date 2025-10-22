# Architecture Documentation

## Project Structure

```
alma-post-import-utilities/
├── main.py                 # Application entry point with routing
├── csv_processor.py        # CSV processing view/page
├── alma_api.py            # Alma API client module
├── requirements.txt       # Python dependencies
├── sample_data.csv       # Sample CSV for testing
├── README.md             # Project overview
├── USAGE.md              # Detailed usage instructions
└── .gitignore            # Git ignore patterns
```

## Component Design

### main.py
**Purpose**: Application entry point and navigation controller

**Key Functions**:
- `main(page)`: Initializes the Flet application and sets up routing
- `route_change(route)`: Handles navigation between views
- `view_pop(view)`: Handles back navigation

**Design Pattern**: Single-page application with view-based routing

### csv_processor.py
**Purpose**: Implements the CSV MMS ID updater view

**Key Components**:
- `csv_processor_view(page)`: Creates the main view with all UI components
- `pick_file_result(e)`: Handles file selection events
- `on_api_key_change(e)`: Validates form state and enables/disables process button
- `process_csv(e)`: Main processing logic that:
  1. Validates inputs
  2. Reads CSV file
  3. Queries Alma API for each row
  4. Updates CSV with MMS IDs
  5. Reports results to user

**UI Elements**:
- API key input field (password field with reveal option)
- File picker button
- Process button (enabled when both API key and file are selected)
- Progress/status text (updates in real-time)
- Instructions panel

**State Management**: Uses Flet's Ref system for reactive UI updates

### alma_api.py
**Purpose**: Provides interface to Alma API

**Class**: `AlmaAPIClient`

**Methods**:
- `__init__(api_key, base_url)`: Initializes client with credentials
- `get_mms_id_by_originating_system_id(originating_system_id)`: 
  - Queries Alma's bibs endpoint with other_system_id parameter
  - Returns MMS ID if found, None otherwise
  - Handles HTTP errors gracefully

**API Endpoint Used**:
- `GET /almaws/v1/bibs?other_system_id={id}`

**Error Handling**:
- Returns None on errors instead of raising exceptions
- Logs errors to console for debugging
- Handles network timeouts (30 second timeout)

## Data Flow

1. User enters API key and selects CSV file
2. User clicks "Process CSV"
3. Application reads entire CSV into memory
4. For each row:
   - Check if `originating_system_id` exists and `mms_id` is empty
   - If yes, query Alma API
   - Update row with returned MMS ID
5. Write all rows back to CSV file
6. Display summary statistics

## Design Decisions

### Why read entire CSV into memory?
- Simplifies processing logic
- Allows atomic file updates (all or nothing)
- Most CSV files are small enough for memory
- If needed for large files, could be refactored to use streaming

### Why update file in place?
- Matches typical workflow expectations
- Preserves original file location
- User doesn't need to manage multiple file versions
- Could add backup option if needed

### Why single view initially?
- Requirement specified first view for this functionality
- Architecture supports easy addition of more views
- Routing system is already in place

### Error Handling Strategy
- API errors: Log and continue processing other rows
- CSV errors: Stop immediately and inform user
- Network errors: Handled by requests library with timeout

## Extension Points

### Adding New Views
1. Create new view function in a new file (e.g., `another_view.py`)
2. Import in `main.py`
3. Add route handling in `route_change()` function

Example:
```python
from another_view import another_view_function

def route_change(route):
    page.views.clear()
    if page.route == "/":
        page.views.append(csv_processor_view(page))
    elif page.route == "/another":
        page.views.append(another_view_function(page))
    page.update()
```

### Supporting Different APIs
The `AlmaAPIClient` can be extended to support additional Alma endpoints:
```python
def get_digital_title(self, mms_id: str) -> Optional[dict]:
    url = f"{self.base_url}/almaws/v1/bibs/{mms_id}"
    # ... implementation
```

### Configuration Management
Future enhancement could add:
- Config file for API base URL
- Saved API keys (encrypted)
- Processing preferences

## Testing Strategy

### Manual Testing
- Use `sample_data.csv` for basic functionality testing
- Test with real API key for integration testing
- Test error cases (missing columns, invalid API key, network errors)

### Automated Testing
- Core logic verified with `/tmp/test_logic.py`
- CSV reading/writing operations tested
- API client instantiation tested
- No security vulnerabilities found (CodeQL scan passed)

### Future Testing
Could add:
- Unit tests for each module
- Mock API responses for testing without real API key
- UI automation tests using Flet's testing capabilities

## Security Considerations

### API Key Storage
- Currently stored in memory only during session
- Not persisted to disk
- Password field provides visual security
- Future: Could add encrypted storage option

### CSV File Security
- Files are read/written with UTF-8 encoding
- No arbitrary code execution risk
- File picker restricts to CSV files only

### Network Security
- Uses HTTPS for all API calls
- Includes timeout to prevent hanging
- API key sent in Authorization header (standard practice)

## Performance Considerations

### Current Implementation
- Sequential processing (one API call at a time)
- Simple and reliable
- Progress updates for each row

### Future Optimizations
If processing large files:
- Batch API requests (if Alma API supports)
- Parallel processing with async/await
- Streaming CSV processing
- Progress bar instead of text updates

## Dependencies

### Core Dependencies
- `flet>=0.23.0`: UI framework
- `requests>=2.31.0`: HTTP client

### Why These Versions?
- Flet 0.23.0+ has stable file picker API
- Requests 2.31.0+ includes security fixes

### Dependency Management
- All dependencies specified in `requirements.txt`
- No conflicting dependencies
- Easy to install: `pip install -r requirements.txt`

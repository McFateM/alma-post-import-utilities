"""
CSV Processing view for updating MMS IDs from Alma API.
"""
import csv
import logging
import flet as ft
from pathlib import Path
from alma_api import AlmaAPIClient

logger = logging.getLogger(__name__)


def csv_processor_view(page: ft.Page):
    """
    View for processing CSV files to update MMS IDs.
    
    Allows users to:
    1. Select a CSV file
    2. Configure Alma API credentials
    3. Process the CSV to update empty mms_id fields
    """
    
    # State variables
    selected_file_path = ft.Ref[ft.Text]()
    api_key_field = ft.Ref[ft.TextField]()
    progress_text = ft.Ref[ft.Text]()
    process_button = ft.Ref[ft.ElevatedButton]()
    
    def pick_file_result(e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files:
            file_path = e.files[0].path
            logger.info(f"File selected: {file_path}")
            selected_file_path.current.value = file_path
            selected_file_path.current.update()
            # Enable process button if API key is also provided
            if api_key_field.current.value:
                process_button.current.disabled = False
                process_button.current.update()
                logger.debug("Process button enabled (file and API key present)")
        else:
            logger.debug("File picker cancelled")
    
    def on_api_key_change(e):
        """Handle API key field change."""
        has_api_key = bool(api_key_field.current.value)
        has_file = bool(selected_file_path.current.value)
        logger.debug(f"API key change - has_api_key: {has_api_key}, has_file: {has_file}")
        
        if has_api_key and has_file:
            process_button.current.disabled = False
        else:
            process_button.current.disabled = True
        process_button.current.update()
    
    def process_csv(e):
        """Process the CSV file to update MMS IDs."""
        file_path = selected_file_path.current.value
        api_key = api_key_field.current.value
        
        logger.info(f"Starting CSV processing - File: {file_path}")
        
        if not file_path or not api_key:
            logger.error("Missing file path or API key")
            progress_text.current.value = "Error: Please select a file and provide API key"
            progress_text.current.color = ft.Colors.RED_800
            progress_text.current.update()
            return
        
        # Disable button during processing
        process_button.current.disabled = True
        process_button.current.update()
        logger.debug("Process button disabled during processing")
        
        try:
            # Initialize Alma API client
            logger.info("Initializing Alma API client")
            client = AlmaAPIClient(api_key)
            
            # Step 1: Fetch all digital titles from Alma
            progress_text.current.value = "Step 1/2: Fetching all digital titles from Alma..."
            progress_text.current.color = ft.Colors.BLUE
            progress_text.current.update()
            
            digital_titles_file = "All_Digital_Titles.csv"
            logger.info("Fetching all digital title records from Alma")
            
            if not client.fetch_all_digital_titles(digital_titles_file):
                progress_text.current.value = "Error: Failed to fetch digital titles from Alma"
                progress_text.current.color = ft.Colors.RED_800
                progress_text.current.update()
                process_button.current.disabled = False
                process_button.current.update()
                return
            
            # Step 2: Load the digital titles into a lookup dictionary
            logger.info(f"Loading digital titles from {digital_titles_file}")
            progress_text.current.value = "Step 2/2: Processing your CSV file..."
            progress_text.current.update()
            
            mms_lookup = {}  # Dictionary: originating_system_id -> mms_id
            
            with open(digital_titles_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for digital_row in reader:
                    mms_id = digital_row.get('mms_id', '').strip()
                    dc_identifiers = digital_row.get('dc_identifiers', '')
                    
                    # Split multiple identifiers and add each to the lookup
                    if mms_id and dc_identifiers:
                        identifiers = dc_identifiers.split('|')
                        for identifier in identifiers:
                            identifier = identifier.strip()
                            if identifier:
                                mms_lookup[identifier] = mms_id
            
            logger.info(f"Loaded {len(mms_lookup)} identifier-to-MMS ID mappings")
            
            # Step 3: Read the user's CSV file
            path = Path(file_path)
            logger.debug(f"Reading user CSV file: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
            
            logger.info(f"CSV file loaded - {len(rows)} rows, columns: {fieldnames}")
            
            # Ensure required columns exist
            if 'originating_system_id' not in fieldnames or 'mms_id' not in fieldnames:
                logger.error(f"Missing required columns. Found columns: {fieldnames}")
                progress_text.current.value = "Error: CSV must have 'originating_system_id' and 'mms_id' columns"
                progress_text.current.color = ft.Colors.RED_800
                progress_text.current.update()
                process_button.current.disabled = False
                process_button.current.update()
                return
            
            # Step 4: Process each row and update MMS IDs from lookup
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            logger.info(f"Beginning processing of {len(rows)} rows")
            
            for i, row in enumerate(rows):
                originating_system_id = row.get('originating_system_id', '').strip()
                mms_id = row.get('mms_id', '').strip()
                
                # Only process if originating_system_id exists and mms_id is empty
                if originating_system_id and not mms_id:
                    logger.debug(f"Processing row {i+1}/{len(rows)}: originating_system_id={originating_system_id}")
                    progress_text.current.value = f"Processing row {i+1}/{len(rows)}: {originating_system_id}"
                    progress_text.current.update()
                    
                    # Look up MMS ID in the digital titles data
                    fetched_mms_id = mms_lookup.get(originating_system_id)
                    
                    if fetched_mms_id:
                        logger.info(f"Row {i+1}: Found MMS ID {fetched_mms_id} for {originating_system_id}")
                        row['mms_id'] = fetched_mms_id
                        updated_count += 1
                    else:
                        logger.warning(f"Row {i+1}: No MMS ID found for {originating_system_id}")
                        error_count += 1
                else:
                    if not originating_system_id:
                        logger.debug(f"Row {i+1}: Skipped (no originating_system_id)")
                    elif mms_id:
                        logger.debug(f"Row {i+1}: Skipped (mms_id already exists: {mms_id})")
                    skipped_count += 1
            
            # Step 5: Write updated data back to CSV
            logger.info(f"Writing updated data back to {path}")
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            # Show success message
            summary = f"Updated: {updated_count} | Skipped: {skipped_count} | Not found: {error_count}"
            logger.info(f"Processing complete! {summary}")
            progress_text.current.value = (
                f"Processing complete!\n"
                f"{summary}\n"
                f"Digital titles saved to: {digital_titles_file}"
            )
            progress_text.current.color = ft.Colors.GREEN
            progress_text.current.update()
            
        except Exception as ex:
            logger.exception(f"Error during CSV processing: {str(ex)}")
            progress_text.current.value = f"Error: {str(ex)}"
            progress_text.current.color = ft.Colors.RED_800
            progress_text.current.update()
        
        finally:
            # Re-enable button
            process_button.current.disabled = False
            process_button.current.update()
            logger.debug("Process button re-enabled")
    
    # Create file picker
    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)
    page.update()
    
    # Build the view
    return ft.View(
        "/",
        [
            ft.AppBar(
                title=ft.Text("Alma Post-Import Utilities", color=ft.Colors.RED_800),
                bgcolor=ft.Colors.GREY_300
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("CSV MMS ID Updater", size=24, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        
                        # API Key input
                        ft.TextField(
                            ref=api_key_field,
                            label="Alma API Key",
                            password=True,
                            can_reveal_password=True,
                            on_change=on_api_key_change,
                            width=400,
                        ),
                        
                        # File picker section
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Select CSV File",
                                    icon=ft.Icons.UPLOAD_FILE,
                                    on_click=lambda _: file_picker.pick_files(
                                        allowed_extensions=["csv"],
                                        allow_multiple=False
                                    ),
                                ),
                            ]
                        ),
                        
                        ft.Text(
                            ref=selected_file_path,
                            value="No file selected",
                            italic=True,
                        ),
                        
                        ft.Divider(),
                        
                        # Process button
                        ft.ElevatedButton(
                            ref=process_button,
                            text="Process CSV",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=process_csv,
                            disabled=True,
                        ),
                        
                        # Progress/status text
                        ft.Text(
                            ref=progress_text,
                            value="",
                            size=14,
                        ),
                        
                        ft.Divider(),
                        
                        # Instructions
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Instructions:", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800),
                                    ft.Text("1. Enter your Alma API key", color=ft.Colors.RED_800),
                                    ft.Text("2. Select a CSV file with 'originating_system_id' and 'mms_id' columns", color=ft.Colors.RED_800),
                                    ft.Text("3. Click 'Process CSV' to update empty mms_id values", color=ft.Colors.RED_800),
                                    ft.Text("4. The CSV file will be updated in place", color=ft.Colors.RED_800),
                                ],
                                spacing=5,
                            ),
                            padding=10,
                            bgcolor=ft.Colors.GREY_300,
                            border_radius=10,
                        ),
                    ],
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

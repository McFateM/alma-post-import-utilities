"""
CSV Processing view for updating MMS IDs from Alma API.
"""
import csv
import flet as ft
from pathlib import Path
from alma_api import AlmaAPIClient


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
            selected_file_path.current.value = e.files[0].path
            selected_file_path.current.update()
            # Enable process button if API key is also provided
            if api_key_field.current.value:
                process_button.current.disabled = False
                process_button.current.update()
    
    def on_api_key_change(e):
        """Handle API key field change."""
        if api_key_field.current.value and selected_file_path.current.value:
            process_button.current.disabled = False
        else:
            process_button.current.disabled = True
        process_button.current.update()
    
    def process_csv(e):
        """Process the CSV file to update MMS IDs."""
        file_path = selected_file_path.current.value
        api_key = api_key_field.current.value
        
        if not file_path or not api_key:
            progress_text.current.value = "Error: Please select a file and provide API key"
            progress_text.current.color = ft.colors.RED
            progress_text.current.update()
            return
        
        # Disable button during processing
        process_button.current.disabled = True
        process_button.current.update()
        
        try:
            # Initialize Alma API client
            client = AlmaAPIClient(api_key)
            
            # Read the CSV file
            path = Path(file_path)
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
            
            # Ensure required columns exist
            if 'originating_system_id' not in fieldnames or 'mms_id' not in fieldnames:
                progress_text.current.value = "Error: CSV must have 'originating_system_id' and 'mms_id' columns"
                progress_text.current.color = ft.colors.RED
                progress_text.current.update()
                process_button.current.disabled = False
                process_button.current.update()
                return
            
            # Process each row
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            progress_text.current.value = f"Processing {len(rows)} rows..."
            progress_text.current.color = ft.colors.BLUE
            progress_text.current.update()
            
            for i, row in enumerate(rows):
                originating_system_id = row.get('originating_system_id', '').strip()
                mms_id = row.get('mms_id', '').strip()
                
                # Only process if originating_system_id exists and mms_id is empty
                if originating_system_id and not mms_id:
                    progress_text.current.value = f"Processing row {i+1}/{len(rows)}: {originating_system_id}"
                    progress_text.current.update()
                    
                    # Query Alma API
                    fetched_mms_id = client.get_mms_id_by_originating_system_id(originating_system_id)
                    
                    if fetched_mms_id:
                        row['mms_id'] = fetched_mms_id
                        updated_count += 1
                    else:
                        error_count += 1
                else:
                    skipped_count += 1
            
            # Write updated data back to CSV
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            # Show success message
            progress_text.current.value = (
                f"Processing complete!\n"
                f"Updated: {updated_count} | Skipped: {skipped_count} | Not found: {error_count}"
            )
            progress_text.current.color = ft.colors.GREEN
            progress_text.current.update()
            
        except Exception as ex:
            progress_text.current.value = f"Error: {str(ex)}"
            progress_text.current.color = ft.colors.RED
            progress_text.current.update()
        
        finally:
            # Re-enable button
            process_button.current.disabled = False
            process_button.current.update()
    
    # Create file picker
    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)
    page.update()
    
    # Build the view
    return ft.View(
        "/",
        [
            ft.AppBar(title=ft.Text("Alma Post-Import Utilities"), bgcolor=ft.colors.SURFACE_VARIANT),
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
                                    icon=ft.icons.UPLOAD_FILE,
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
                            icon=ft.icons.PLAY_ARROW,
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
                                    ft.Text("Instructions:", weight=ft.FontWeight.BOLD),
                                    ft.Text("1. Enter your Alma API key"),
                                    ft.Text("2. Select a CSV file with 'originating_system_id' and 'mms_id' columns"),
                                    ft.Text("3. Click 'Process CSV' to update empty mms_id values"),
                                    ft.Text("4. The CSV file will be updated in place"),
                                ],
                                spacing=5,
                            ),
                            padding=10,
                            bgcolor=ft.colors.SURFACE_VARIANT,
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

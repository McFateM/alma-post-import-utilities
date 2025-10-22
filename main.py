"""
Alma Post-Import Utilities - Main Application

A Flet application for managing Alma records after import.
"""
import logging
import flet as ft
from csv_processor import csv_processor_view

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to see detailed progress without DEBUG noise
    # level=logging.DEBUG,  # Uncomment for full debug logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alma_post_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    """Main application entry point."""
    logger.info("Starting Alma Post-Import Utilities application")
    page.title = "Alma Post-Import Utilities"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.height = page.window.height + 10 if page.window.height else 610
    
    def route_change(route):
        """Handle route changes."""
        # logger.debug(f"Route change to: {route}")
        page.views.clear()
        
        # Route to CSV processor view (main view)
        if page.route == "/":
            page.views.append(csv_processor_view(page))
        
        page.update()
    
    def view_pop(view):
        """Handle back navigation."""
        # logger.debug("View pop navigation")
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    logger.info("Launching Flet application")
    ft.app(target=main)

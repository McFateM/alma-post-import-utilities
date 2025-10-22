"""
Alma Post-Import Utilities - Main Application

A Flet application for managing Alma records after import.
"""
import flet as ft
from csv_processor import csv_processor_view


def main(page: ft.Page):
    """Main application entry point."""
    page.title = "Alma Post-Import Utilities"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    def route_change(route):
        """Handle route changes."""
        page.views.clear()
        
        # Route to CSV processor view (main view)
        if page.route == "/":
            page.views.append(csv_processor_view(page))
        
        page.update()
    
    def view_pop(view):
        """Handle back navigation."""
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main)

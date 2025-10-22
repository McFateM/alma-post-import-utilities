"""
Alma API client for querying digital objects.
"""
import requests
from typing import Optional


class AlmaAPIClient:
    """Client for interacting with the Alma API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api-na.hosted.exlibrisgroup.com"):
        """
        Initialize the Alma API client.
        
        Args:
            api_key: Alma API key
            base_url: Base URL for Alma API (default: North America region)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"apikey {api_key}",
            "Accept": "application/json"
        }
    
    def get_mms_id_by_originating_system_id(self, originating_system_id: str) -> Optional[str]:
        """
        Query Alma API to get MMS ID for a given originating_system_id.
        
        Args:
            originating_system_id: The originating system ID to search for
            
        Returns:
            The MMS ID if found, None otherwise
        """
        try:
            # Search for the digital object using the originating_system_id
            # Using the bibs search endpoint with other_system_id parameter
            url = f"{self.base_url}/almaws/v1/bibs"
            params = {
                "other_system_id": originating_system_id
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # The API returns a list of bibs
                if "bib" in data and len(data["bib"]) > 0:
                    # Return the MMS ID of the first matching record
                    return data["bib"][0].get("mms_id")
            elif response.status_code == 400:
                # No results found
                return None
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error querying Alma API: {str(e)}")
            return None
        
        return None

"""
Alma API client for querying digital objects.
"""
import csv
import logging
import requests
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class AlmaServerError(Exception):
    """Raised when Alma API servers are experiencing widespread issues."""
    pass


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
        self.consecutive_server_errors = 0  # Track consecutive 500 errors
        self.max_consecutive_errors = 3     # Terminate after 3 consecutive 500 errors
        logger.info(f"AlmaAPIClient initialized with base_url: {base_url}")
        logger.debug(f"API key length: {len(api_key)} characters")
    
    def fetch_all_digital_titles(self, output_file: str = "All_Digital_Titles.csv") -> bool:
        """
        Fetch digital title information by using a different approach.
        Instead of fetching all records upfront, we'll create a lookup method
        that queries individual records as needed.
        
        For now, this creates an empty CSV file and returns True to indicate
        the lookup method should be used instead.
        
        Args:
            output_file: Path to the output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Setting up digital title lookup (individual record approach)")
        try:
            # Create an empty CSV file with headers
            # The actual lookup will be done individually for each originating_system_id
            output_path = Path(output_file)
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ["mms_id", "dc_identifiers"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            
            logger.info(f"Created lookup CSV file: {output_file}")
            logger.info("Note: Digital titles will be looked up individually during processing")
            return True
                
        except Exception as e:
            logger.exception(f"Error setting up digital titles lookup: {str(e)}")
            return False
    
    def get_mms_id_by_originating_system_id(self, originating_system_id: str) -> Optional[str]:
        """
        Query Primo Search API to get MMS ID for a given originating_system_id.
        
        Args:
            originating_system_id: The originating system ID to search for in dc:identifier
            
        Returns:
            The MMS ID if found, None otherwise
        """
        import time
        
        logger.info(f"Starting search for originating_system_id: {originating_system_id}")
        logger.debug(f"Querying Primo Search API for originating_system_id in dc:identifier: {originating_system_id}")
        
        # Retry logic for server errors
        max_retries = 5  # Increased from 3 to 5
        retry_delay = 2  # Increased from 1 to 2 seconds
        
        for attempt in range(max_retries):
            try:
                # Search for the record using Primo Search with dc:identifier query
                url = f"{self.base_url}/primo/v1/search"
                params = {
                    "q": f'any,contains,{originating_system_id}',  # Try broader search
                    "limit": 1,
                    "offset": 0
                }
                
                logger.info(f"Making API request (attempt {attempt + 1}/{max_retries}) for {originating_system_id}")
                logger.debug(f"API request - URL: {url}, params: {params} (attempt {attempt + 1}/{max_retries})")
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                logger.info(f"API response received - Status: {response.status_code}")
                logger.debug(f"API response - Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Success - reset consecutive error counter
                    self.consecutive_server_errors = 0
                    data = response.json()
                    logger.info(f"Parsing response data for {originating_system_id}")
                    # The API returns docs in the response
                    if "docs" in data and len(data["docs"]) > 0:
                        logger.info(f"Found {len(data['docs'])} docs in response for {originating_system_id}")
                        # Extract the MMS ID from the pnx section
                        doc = data["docs"][0]
                        if "pnx" in doc and "control" in doc["pnx"]:
                            control = doc["pnx"]["control"]
                            # MMS ID is typically in the sourcerecordid or recordid field
                            mms_id = None
                            if "sourcerecordid" in control and len(control["sourcerecordid"]) > 0:
                                mms_id = control["sourcerecordid"][0]
                            elif "recordid" in control and len(control["recordid"]) > 0:
                                mms_id = control["recordid"][0]
                            
                            if mms_id:
                                logger.info(f"Successfully found MMS ID: {mms_id} for {originating_system_id}")
                                return mms_id
                            else:
                                logger.info(f"No MMS ID found in control section for {originating_system_id}")
                                logger.debug(f"No MMS ID found in control section for {originating_system_id}")
                        else:
                            logger.info(f"No pnx/control section in response for {originating_system_id}")
                            logger.debug(f"No pnx/control section in response for {originating_system_id}")
                    else:
                        logger.info(f"No docs found in response for {originating_system_id}")
                        logger.debug(f"No docs found in response for {originating_system_id}")
                        return None  # No results found, no need to retry
                
                elif response.status_code == 400:
                    # No results found - reset consecutive error counter and don't retry
                    self.consecutive_server_errors = 0
                    logger.info(f"No results found (400 status) for {originating_system_id}")
                    logger.debug(f"No results found (400 status) for {originating_system_id}")
                    return None
                
                elif response.status_code == 500:
                    # Server error - track consecutive errors and potentially terminate
                    error_text = response.text
                    logger.warning(f"Server error (attempt {attempt + 1}/{max_retries}) for {originating_system_id}: {response.status_code} - {error_text}")
                    
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # All retries failed for this request - check if we should terminate
                        self.consecutive_server_errors += 1
                        logger.error(f"Max retries reached for {originating_system_id} (consecutive server errors: {self.consecutive_server_errors})")
                        
                        if self.consecutive_server_errors >= self.max_consecutive_errors:
                            error_msg = (f"Alma API servers are experiencing widespread issues. "
                                       f"Encountered {self.consecutive_server_errors} consecutive 500 Internal Server Errors. "
                                       f"Terminating processing to avoid wasting time. "
                                       f"Please try again later when Alma's servers have recovered.")
                            logger.error(error_msg)
                            raise AlmaServerError(error_msg)
                        
                        return None
                
                else:
                    # Other error - reset consecutive error counter and don't retry
                    self.consecutive_server_errors = 0
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                logger.error(f"Exception occurred querying Primo Search API for {originating_system_id}: {str(e)}")
                logger.exception(f"Error querying Primo Search API for {originating_system_id}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying due to exception in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
        logger.info(f"Exhausted all retry attempts for {originating_system_id}")
        return None

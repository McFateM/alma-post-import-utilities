"""
Alma API client for querying digital objects.
"""
import csv
import logging
import requests
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


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
        logger.info(f"AlmaAPIClient initialized with base_url: {base_url}")
        logger.debug(f"API key length: {len(api_key)} characters")
    
    def fetch_all_digital_titles(self, output_file: str = "All_Digital_Titles.csv") -> bool:
        """
        Fetch all digital title bib records from Alma and save to CSV.
        
        Args:
            output_file: Path to the output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting to fetch all digital title bib records from Alma")
        try:
            all_records = []
            offset = 0
            limit = 100  # Fetch 100 records per request
            total_fetched = 0
            
            while True:
                # Query for digital titles using Alma bibs
                url = f"{self.base_url}/almaws/v1/bibs"
                params = {
                    "q": "rtype,exact,digital",  # Query for digital resource type
                    "limit": limit,
                    "offset": offset
                }
                
                logger.debug(f"Fetching digital titles - offset: {offset}, limit: {limit}")
                response = requests.get(url, headers=self.headers, params=params, timeout=60)
                
                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return False
                
                data = response.json()
                
                if "docs" not in data or len(data["docs"]) == 0:
                    logger.info(f"No more records found. Total fetched: {total_fetched}")
                    break
                
                # Extract relevant information from each record
                for doc in data["docs"]:
                    record = {}
                    
                    # Extract MMS ID
                    if "pnx" in doc and "control" in doc["pnx"]:
                        control = doc["pnx"]["control"]
                        if "sourcerecordid" in control and len(control["sourcerecordid"]) > 0:
                            record["mms_id"] = control["sourcerecordid"][0]
                        elif "recordid" in control and len(control["recordid"]) > 0:
                            record["mms_id"] = control["recordid"][0]
                    
                    # Extract dc:identifier values
                    if "pnx" in doc and "addata" in doc["pnx"]:
                        addata = doc["pnx"]["addata"]
                        identifiers = []
                        if "identifier" in addata:
                            identifiers = addata["identifier"]
                        record["dc_identifiers"] = "|".join(identifiers) if identifiers else ""
                    
                    if "mms_id" in record:
                        all_records.append(record)
                        total_fetched += 1
                
                logger.info(f"Fetched {len(data['docs'])} records, total so far: {total_fetched}")
                
                # Check if we've fetched all records
                if len(data["docs"]) < limit:
                    break
                
                offset += limit
            
            # Write to CSV
            if all_records:
                output_path = Path(output_file)
                logger.info(f"Writing {len(all_records)} records to {output_path}")
                
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    fieldnames = ["mms_id", "dc_identifiers"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_records)
                
                logger.info(f"Successfully wrote {len(all_records)} digital title records to {output_file}")
                return True
            else:
                logger.warning("No digital title records found")
                return False
                
        except Exception as e:
            logger.exception(f"Error fetching digital titles: {str(e)}")
            return False
    
    def get_mms_id_by_originating_system_id(self, originating_system_id: str) -> Optional[str]:
        """
        Query Primo Search API to get MMS ID for a given originating_system_id.
        
        Args:
            originating_system_id: The originating system ID to search for in dc:identifier
            
        Returns:
            The MMS ID if found, None otherwise
        """
        logger.debug(f"Querying Primo Search API for originating_system_id in dc:identifier: {originating_system_id}")
        try:
            # Search for the record using Primo Search with dc:identifier query
            # Using the Primo Search endpoint
            url = f"{self.base_url}/primo/v1/search"
            params = {
                "q": f'dc:identifier,contains,{originating_system_id}',
                "limit": 1,
                "offset": 0
            }
            
            logger.debug(f"API request - URL: {url}, params: {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            logger.debug(f"API response - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # The API returns docs in the response
                if "docs" in data and len(data["docs"]) > 0:
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
                            logger.debug(f"No MMS ID found in control section for {originating_system_id}")
                    else:
                        logger.debug(f"No pnx/control section in response for {originating_system_id}")
                else:
                    logger.debug(f"No docs found in response for {originating_system_id}")
            elif response.status_code == 400:
                # No results found
                logger.debug(f"No results found (400 status) for {originating_system_id}")
                return None
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.exception(f"Error querying Primo Search API for {originating_system_id}: {str(e)}")
            return None
        
        return None

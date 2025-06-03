"""
Inventory Service Module for GCP VM Inventory Tool.

This module provides a unified service for collecting inventory data from GCP.
"""

import csv
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from .gcp_client import GCPClient
from .vm_inventory import VMInventory
from .bigquery_inventory import BigQueryInventory
from .models import (
    VMInfo, 
    BigQueryDatasetInfo, 
    SQLInstanceInfo, 
    GKEClusterInfo,
    APIStatus,
    InventoryResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InventoryService:
    """Service for collecting inventory data from GCP."""
    
    def __init__(self, project_id: Optional[str] = None, service_account_key: Optional[str] = None):
        """Initialize the inventory service.
        
        Args:
            project_id: The GCP project ID (optional)
            service_account_key: Path to service account key file (optional)
        """
        self.project_id = project_id
        self.service_account_key = service_account_key
        self.client = GCPClient(project_id, service_account_key)
        self.vm_inventory = VMInventory(self.client)
        self.bq_inventory = BigQueryInventory(self.client)
    
    def check_api_status(self, project_id: Optional[str] = None) -> List[APIStatus]:
        """Check the status of required APIs.
        
        Args:
            project_id: The GCP project ID (optional)
            
        Returns:
            List of APIStatus objects
        """
        required_apis = {
            "compute.googleapis.com": "Compute Engine API",
            "sqladmin.googleapis.com": "Cloud SQL Admin API",
            "bigquery.googleapis.com": "BigQuery API",
            "container.googleapis.com": "Kubernetes Engine API"
        }
        
        api_status_list = []
        projects = []
        
        if project_id:
            projects = [project_id]
        else:
            # Get all accessible projects
            projects_data = self.client.get_projects()
            if not projects_data:
                logger.warning("No projects found or unable to access project list.")
                return []
            
            projects = [p.get('projectId') for p in projects_data]
        
        for proj_id in projects:
            logger.info(f"Checking API status for project: {proj_id}")
            
            for api_id, api_name in required_apis.items():
                status = self.client.check_api_status(proj_id, api_id)
                
                api_status_list.append(APIStatus(
                    project_id=proj_id,
                    api_id=api_id,
                    api_name=api_name,
                    status=status
                ))
        
        return api_status_list
    
    def collect_vm_inventory(self, skip_disabled_apis: bool = False) -> List[VMInfo]:
        """Collect VM inventory data.
        
        Args:
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            List of VMInfo objects
        """
        return self.vm_inventory.collect_vm_inventory(
            project_id=self.project_id,
            skip_disabled_apis=skip_disabled_apis
        )
    
    def collect_bigquery_inventory(self, skip_disabled_apis: bool = False) -> List[BigQueryDatasetInfo]:
        """Collect BigQuery inventory data.
        
        Args:
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            List of BigQueryDatasetInfo objects
        """
        return self.bq_inventory.collect_bigquery_inventory(
            project_id=self.project_id,
            skip_disabled_apis=skip_disabled_apis
        )
    
    def collect_sql_inventory(self, skip_disabled_apis: bool = False) -> List[SQLInstanceInfo]:
        """Collect Cloud SQL inventory data.
        
        Args:
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            List of SQLInstanceInfo objects
        """
        # TODO: Implement SQL inventory collection
        return []
    
    def collect_gke_inventory(self, skip_disabled_apis: bool = False) -> List[GKEClusterInfo]:
        """Collect GKE inventory data.
        
        Args:
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            List of GKEClusterInfo objects
        """
        # TODO: Implement GKE inventory collection
        return []
    
    def collect_all_inventory(self, skip_disabled_apis: bool = False) -> InventoryResult:
        """Collect all inventory data.
        
        Args:
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            InventoryResult object with all collected data
        """
        logger.info("Starting inventory collection")
        
        # Check API status first
        api_status = self.check_api_status(self.project_id)
        
        # Collect VM inventory
        logger.info("Collecting VM inventory")
        vms = self.collect_vm_inventory(skip_disabled_apis)
        
        # Collect BigQuery inventory
        logger.info("Collecting BigQuery inventory")
        bigquery_datasets = self.collect_bigquery_inventory(skip_disabled_apis)
        
        # Collect SQL inventory
        logger.info("Collecting Cloud SQL inventory")
        sql_instances = self.collect_sql_inventory(skip_disabled_apis)
        
        # Collect GKE inventory
        logger.info("Collecting GKE inventory")
        gke_clusters = self.collect_gke_inventory(skip_disabled_apis)
        
        logger.info("Inventory collection completed")
        
        return InventoryResult(
            timestamp=datetime.now(),
            vms=vms,
            sql_instances=sql_instances,
            bigquery_datasets=bigquery_datasets,
            gke_clusters=gke_clusters,
            api_status=api_status
        )
    
    def export_to_csv(self, data: List[Union[VMInfo, SQLInstanceInfo, BigQueryDatasetInfo, GKEClusterInfo]], 
                     output_dir: str, filename_prefix: str) -> Optional[str]:
        """Export data to a CSV file.
        
        Args:
            data: List of data objects to export
            output_dir: Directory to store the CSV output
            filename_prefix: Prefix for the CSV filename
            
        Returns:
            Path to the created CSV file or None if export failed
        """
        if not data:
            logger.warning(f"No {filename_prefix} data to export.")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.csv")
        
        # Convert data objects to dictionaries
        dict_data = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
        
        fieldnames = dict_data[0].keys()
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dict_data)
            
            logger.info(f"Data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting data to CSV: {str(e)}")
            return None
    
    def export_to_json(self, data: Any, output_dir: str, filename_prefix: str) -> Optional[str]:
        """Export data to a JSON file.
        
        Args:
            data: Data to export
            output_dir: Directory to store the JSON output
            filename_prefix: Prefix for the JSON filename
            
        Returns:
            Path to the created JSON file or None if export failed
        """
        if not data:
            logger.warning(f"No {filename_prefix} data to export.")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.json")
        
        # Convert data objects to dictionaries if they have a to_dict method
        if hasattr(data, 'to_dict'):
            dict_data = data.to_dict()
        elif isinstance(data, list) and all(hasattr(item, 'to_dict') for item in data):
            dict_data = [item.to_dict() for item in data]
        else:
            dict_data = data
        
        try:
            with open(filename, 'w') as jsonfile:
                json.dump(dict_data, jsonfile, indent=2)
            
            logger.info(f"Data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting data to JSON: {str(e)}")
            return None

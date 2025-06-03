"""
BigQuery Inventory Module for GCP VM Inventory Tool.

This module provides functionality to collect BigQuery inventory data from GCP.
"""

import logging
from typing import Dict, List, Optional, Any
from google.cloud import bigquery
from .gcp_client import GCPClient
from .models import BigQueryDatasetInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BigQueryInventory:
    """Class for collecting BigQuery inventory data from GCP."""
    
    def __init__(self, client: GCPClient):
        """Initialize the BigQuery inventory collector.
        
        Args:
            client: GCP client instance
        """
        self.client = client
        self._bq_client = None
    
    def _get_bq_client(self) -> Optional[bigquery.Client]:
        """Get a BigQuery client.
        
        Returns:
            BigQuery client or None if creation failed
        """
        if not self._bq_client:
            self._bq_client = self.client.get_bigquery_client()
        return self._bq_client
    
    def get_datasets(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all BigQuery datasets in a specific project.
        
        Args:
            project_id: The GCP project ID
            
        Returns:
            List of dataset dictionaries
        """
        bq_client = self._get_bq_client()
        if not bq_client:
            logger.error(f"Could not create BigQuery client for project {project_id}")
            return []
            
        try:
            datasets = list(bq_client.list_datasets())
            
            # Convert to a format similar to CLI output for compatibility
            result = []
            for dataset in datasets:
                # DatasetListItem objects don't have a location attribute
                # We need to get the full dataset to access the location
                try:
                    dataset_ref = bq_client.dataset(dataset.dataset_id)
                    full_dataset = bq_client.get_dataset(dataset_ref)
                    location = full_dataset.location
                except Exception as e:
                    logger.warning(f"Could not get location for dataset {dataset.dataset_id}: {str(e)}")
                    location = "unknown"
                    
                result.append({
                    'datasetReference': {
                        'datasetId': dataset.dataset_id,
                        'projectId': project_id
                    },
                    'id': f"{project_id}:{dataset.dataset_id}",
                    'kind': 'bigquery#dataset',
                    'location': location
                })
            
            logger.info(f"Found {len(result)} datasets in project {project_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting BigQuery datasets for project {project_id}: {str(e)}")
            return []
    
    def get_dataset_info(self, project_id: str, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a BigQuery dataset.
        
        Args:
            project_id: The GCP project ID
            dataset_id: The BigQuery dataset ID
            
        Returns:
            Dictionary with dataset information or None if not available
        """
        bq_client = self._get_bq_client()
        if not bq_client:
            return None
            
        try:
            dataset_ref = bq_client.dataset(dataset_id)
            dataset = bq_client.get_dataset(dataset_ref)
            
            # Convert to a dictionary format
            return {
                'id': f"{project_id}:{dataset_id}",
                'datasetReference': {
                    'datasetId': dataset_id,
                    'projectId': project_id
                },
                'location': dataset.location,
                'creationTime': dataset.created.timestamp() * 1000 if dataset.created else None,
                'lastModifiedTime': dataset.modified.timestamp() * 1000 if dataset.modified else None,
                'description': dataset.description
            }
        except Exception as e:
            logger.error(f"Error getting BigQuery dataset info for {project_id}:{dataset_id}: {str(e)}")
            return None
    
    def get_tables(self, project_id: str, dataset_id: str) -> List[Dict[str, Any]]:
        """Get all tables in a BigQuery dataset.
        
        Args:
            project_id: The GCP project ID
            dataset_id: The BigQuery dataset ID
            
        Returns:
            List of table dictionaries
        """
        bq_client = self._get_bq_client()
        if not bq_client:
            return []
            
        try:
            dataset_ref = bq_client.dataset(dataset_id)
            tables = list(bq_client.list_tables(dataset_ref))
            
            # Get detailed information for each table
            result = []
            for table in tables:
                try:
                    table_ref = bq_client.get_table(table.reference)
                    result.append({
                        'id': f"{project_id}:{dataset_id}.{table.table_id}",
                        'tableReference': {
                            'projectId': project_id,
                            'datasetId': dataset_id,
                            'tableId': table.table_id
                        },
                        'numBytes': table_ref.num_bytes,
                        'numRows': table_ref.num_rows,
                        'creationTime': table_ref.created.timestamp() * 1000 if table_ref.created else None,
                        'lastModifiedTime': table_ref.modified.timestamp() * 1000 if table_ref.modified else None,
                        'type': table_ref.table_type
                    })
                except Exception as e:
                    logger.warning(f"Error getting details for table {table.table_id}: {str(e)}")
                    # Add basic info without details
                    result.append({
                        'id': f"{project_id}:{dataset_id}.{table.table_id}",
                        'tableReference': {
                            'projectId': project_id,
                            'datasetId': dataset_id,
                            'tableId': table.table_id
                        },
                        'numBytes': 0,
                        'numRows': 0
                    })
            
            logger.info(f"Found {len(result)} tables in dataset {dataset_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting BigQuery tables for {project_id}:{dataset_id}: {str(e)}")
            return []
    
    def extract_dataset_info(self, project_id: str, dataset_id: str, location: str) -> Optional[BigQueryDatasetInfo]:
        """Extract BigQuery dataset information.
        
        Args:
            project_id: The GCP project ID
            dataset_id: The BigQuery dataset ID
            location: The dataset location
            
        Returns:
            BigQueryDatasetInfo object or None if extraction failed
        """
        bq_client = self._get_bq_client()
        if not bq_client:
            return None
            
        try:
            # Get dataset details
            dataset_ref = bq_client.dataset(dataset_id)
            full_dataset = bq_client.get_dataset(dataset_ref)
            creation_time = full_dataset.created.timestamp() * 1000 if full_dataset.created else None
            last_modified_time = full_dataset.modified.timestamp() * 1000 if full_dataset.modified else None
            
            # Get tables in the dataset
            tables = self.get_tables(project_id, dataset_id)
            
            # Calculate total storage
            total_size_bytes = sum(table.get('numBytes', 0) for table in tables if 'numBytes' in table)
            total_size_gb = round(total_size_bytes / (1024 * 1024 * 1024), 2) if total_size_bytes > 0 else 0
            
            return BigQueryDatasetInfo(
                project_id=project_id,
                dataset_id=dataset_id,
                location=location,
                creation_time=creation_time,
                last_modified_time=last_modified_time,
                table_count=len(tables),
                total_size_gb=total_size_gb
            )
        except Exception as e:
            logger.error(f"Error extracting dataset info for {project_id}:{dataset_id}: {str(e)}")
            return None
    
    def collect_bigquery_inventory(self, project_id: Optional[str] = None, 
                                  skip_disabled_apis: bool = False) -> List[BigQueryDatasetInfo]:
        """Collect BigQuery inventory data from GCP.
        
        Args:
            project_id: Specific project ID to inventory (optional)
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            List of BigQueryDatasetInfo objects
        """
        all_bq_data = []
        
        try:
            if project_id:
                # Process a single project
                logger.info(f"Collecting BigQuery data for project: {project_id}")
                
                # First check if we can create a client - this will fail fast if there are permission issues
                bq_client = self._get_bq_client()
                if not bq_client:
                    logger.error(f"Could not create BigQuery client for project {project_id}")
                    if not skip_disabled_apis:
                        logger.warning(f"Skipping project {project_id} due to client creation failure")
                    return all_bq_data
                
                # Get all datasets
                datasets = self.get_datasets(project_id)
                if not datasets:
                    logger.info(f"No BigQuery datasets found in project {project_id}")
                    return all_bq_data
                
                logger.info(f"Found {len(datasets)} datasets in project {project_id}")
                
                # Process each dataset
                for dataset in datasets:
                    dataset_id = dataset.get('datasetReference', {}).get('datasetId')
                    if not dataset_id:
                        continue
                    
                    location = dataset.get('location', 'N/A')
                    logger.info(f"Processing dataset: {dataset_id}")
                    
                    dataset_info = self.extract_dataset_info(project_id, dataset_id, location)
                    if dataset_info:
                        all_bq_data.append(dataset_info)
                        logger.info(f"Added dataset {dataset_id} with {dataset_info.table_count} tables and {dataset_info.total_size_gb} GB")
            else:
                # Process all accessible projects
                projects = self.client.get_projects()
                if not projects:
                    logger.warning("No projects found or unable to access project list.")
                    return []
                
                logger.info(f"Found {len(projects)} projects to check for BigQuery datasets")
                
                for project in projects:
                    project_id = project.get('projectId')
                    logger.info(f"Collecting BigQuery data for project: {project_id}")
                    
                    # Set the project ID for the client
                    self.client.project_id = project_id
                    self._bq_client = None  # Reset the BQ client to create a new one with the current project
                    
                    # First check if we can create a client - this will fail fast if there are permission issues
                    bq_client = self._get_bq_client()
                    if not bq_client:
                        logger.error(f"Could not create BigQuery client for project {project_id}")
                        if not skip_disabled_apis:
                            logger.warning(f"Skipping project {project_id} due to client creation failure")
                        continue
                    
                    # Get all datasets
                    datasets = self.get_datasets(project_id)
                    if not datasets:
                        logger.info(f"No BigQuery datasets found in project {project_id}")
                        continue
                    
                    logger.info(f"Found {len(datasets)} datasets in project {project_id}")
                    
                    # Process each dataset
                    for dataset in datasets:
                        dataset_id = dataset.get('datasetReference', {}).get('datasetId')
                        if not dataset_id:
                            continue
                        
                        location = dataset.get('location', 'N/A')
                        logger.info(f"Processing dataset: {dataset_id}")
                        
                        dataset_info = self.extract_dataset_info(project_id, dataset_id, location)
                        if dataset_info:
                            all_bq_data.append(dataset_info)
                            logger.info(f"Added dataset {dataset_id} with {dataset_info.table_count} tables and {dataset_info.total_size_gb} GB")
        except Exception as e:
            logger.error(f"Error collecting BigQuery inventory: {str(e)}")
        
        logger.info(f"Collected information for {len(all_bq_data)} BigQuery datasets across all projects")
        return all_bq_data

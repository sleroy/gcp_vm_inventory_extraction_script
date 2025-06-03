"""
Unit tests for the BigQuery Inventory module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gcp_vm_inventory.bigquery_inventory import BigQueryInventory
from gcp_vm_inventory.models import BigQueryDatasetInfo


class TestBigQueryInventory(unittest.TestCase):
    """Test cases for the BigQueryInventory class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_client = MagicMock()
        self.bq_inventory = BigQueryInventory(self.mock_client)
        
        # Mock BigQuery client
        self.mock_bq_client = MagicMock()
        self.mock_client.get_bigquery_client.return_value = self.mock_bq_client
        
        # Sample dataset for testing
        self.mock_dataset = MagicMock()
        self.mock_dataset.dataset_id = 'test_dataset'
        self.mock_dataset.location = 'US'
        self.mock_dataset.created = datetime(2025, 1, 1)
        self.mock_dataset.modified = datetime(2025, 1, 2)
        
        # Sample table for testing
        self.mock_table = MagicMock()
        self.mock_table.table_id = 'test_table'
        self.mock_table.reference = MagicMock()
        
        # Sample table reference for testing
        self.mock_table_ref = MagicMock()
        self.mock_table_ref.num_bytes = 1024 * 1024 * 10  # 10 MB
        self.mock_table_ref.num_rows = 100
        self.mock_table_ref.created = datetime(2025, 1, 1)
        self.mock_table_ref.modified = datetime(2025, 1, 2)
        self.mock_table_ref.table_type = 'TABLE'
    
    def test_get_bq_client(self):
        """Test getting a BigQuery client."""
        # Get the BigQuery client
        result = self.bq_inventory._get_bq_client()
        
        # Verify the result
        self.assertEqual(result, self.mock_bq_client)
        self.mock_client.get_bigquery_client.assert_called_once()
    
    def test_get_datasets(self):
        """Test getting BigQuery datasets."""
        # Mock the BigQuery client's list_datasets method
        self.mock_bq_client.list_datasets.return_value = [self.mock_dataset]
        self.mock_bq_client.dataset.return_value = 'dataset_ref'
        self.mock_bq_client.get_dataset.return_value = self.mock_dataset
        
        # Get datasets
        result = self.bq_inventory.get_datasets('test-project')
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['datasetReference']['datasetId'], 'test_dataset')
        self.assertEqual(result[0]['datasetReference']['projectId'], 'test-project')
        self.assertEqual(result[0]['location'], 'US')
        self.mock_bq_client.list_datasets.assert_called_once()
    
    def test_get_dataset_info(self):
        """Test getting BigQuery dataset information."""
        # Mock the BigQuery client's dataset and get_dataset methods
        self.mock_bq_client.dataset.return_value = 'dataset_ref'
        self.mock_bq_client.get_dataset.return_value = self.mock_dataset
        
        # Get dataset info
        result = self.bq_inventory.get_dataset_info('test-project', 'test_dataset')
        
        # Verify the result
        self.assertEqual(result['datasetReference']['datasetId'], 'test_dataset')
        self.assertEqual(result['datasetReference']['projectId'], 'test-project')
        self.assertEqual(result['location'], 'US')
        self.assertIsNotNone(result['creationTime'])
        self.assertIsNotNone(result['lastModifiedTime'])
        self.mock_bq_client.dataset.assert_called_once_with('test_dataset')
        self.mock_bq_client.get_dataset.assert_called_once_with('dataset_ref')
    
    def test_get_tables(self):
        """Test getting BigQuery tables."""
        # Mock the BigQuery client's list_tables and get_table methods
        self.mock_bq_client.dataset.return_value = 'dataset_ref'
        self.mock_bq_client.list_tables.return_value = [self.mock_table]
        self.mock_bq_client.get_table.return_value = self.mock_table_ref
        
        # Get tables
        result = self.bq_inventory.get_tables('test-project', 'test_dataset')
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['tableReference']['tableId'], 'test_table')
        self.assertEqual(result[0]['tableReference']['datasetId'], 'test_dataset')
        self.assertEqual(result[0]['tableReference']['projectId'], 'test-project')
        self.assertEqual(result[0]['numBytes'], 1024 * 1024 * 10)
        self.assertEqual(result[0]['numRows'], 100)
        self.mock_bq_client.list_tables.assert_called_once_with('dataset_ref')
        self.mock_bq_client.get_table.assert_called_once()
    
    def test_extract_dataset_info(self):
        """Test extracting BigQuery dataset information."""
        # Mock the BigQuery client's methods
        self.mock_bq_client.dataset.return_value = 'dataset_ref'
        self.mock_bq_client.get_dataset.return_value = self.mock_dataset
        self.mock_bq_client.list_tables.return_value = [self.mock_table]
        self.mock_bq_client.get_table.return_value = self.mock_table_ref
        
        # Extract dataset info
        result = self.bq_inventory.extract_dataset_info('test-project', 'test_dataset', 'US')
        
        # Verify the result
        self.assertIsInstance(result, BigQueryDatasetInfo)
        self.assertEqual(result.project_id, 'test-project')
        self.assertEqual(result.dataset_id, 'test_dataset')
        self.assertEqual(result.location, 'US')
        self.assertEqual(result.table_count, 1)
        self.assertEqual(result.total_size_gb, 0.01)  # 10 MB = 0.01 GB
    
    @patch('gcp_vm_inventory.bigquery_inventory.BigQueryInventory.get_datasets')
    @patch('gcp_vm_inventory.bigquery_inventory.BigQueryInventory.extract_dataset_info')
    def test_collect_bigquery_inventory_single_project(self, mock_extract_dataset_info, mock_get_datasets):
        """Test collecting BigQuery inventory for a single project."""
        # Mock the get_datasets method
        mock_get_datasets.return_value = [
            {
                'datasetReference': {'datasetId': 'test_dataset', 'projectId': 'test-project'},
                'location': 'US'
            }
        ]
        
        # Mock the extract_dataset_info method
        mock_dataset_info = BigQueryDatasetInfo(
            project_id='test-project',
            dataset_id='test_dataset',
            location='US',
            table_count=1,
            total_size_gb=0.01
        )
        mock_extract_dataset_info.return_value = mock_dataset_info
        
        # Collect BigQuery inventory
        result = self.bq_inventory.collect_bigquery_inventory(project_id='test-project')
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_dataset_info)
        mock_get_datasets.assert_called_once_with('test-project')
        mock_extract_dataset_info.assert_called_once_with('test-project', 'test_dataset', 'US')
    
    @patch('gcp_vm_inventory.bigquery_inventory.BigQueryInventory.get_datasets')
    @patch('gcp_vm_inventory.bigquery_inventory.BigQueryInventory.extract_dataset_info')
    def test_collect_bigquery_inventory_all_projects(self, mock_extract_dataset_info, mock_get_datasets):
        """Test collecting BigQuery inventory for all projects."""
        # Mock the client's get_projects method
        self.mock_client.get_projects.return_value = [
            {'projectId': 'project-1'},
            {'projectId': 'project-2'}
        ]
        
        # Mock the get_datasets method
        mock_get_datasets.return_value = [
            {
                'datasetReference': {'datasetId': 'test_dataset', 'projectId': 'project-1'},
                'location': 'US'
            }
        ]
        
        # Mock the extract_dataset_info method
        mock_dataset_info = BigQueryDatasetInfo(
            project_id='project-1',
            dataset_id='test_dataset',
            location='US',
            table_count=1,
            total_size_gb=0.01
        )
        mock_extract_dataset_info.return_value = mock_dataset_info
        
        # Collect BigQuery inventory
        result = self.bq_inventory.collect_bigquery_inventory()
        
        # Verify the result
        self.assertEqual(len(result), 2)  # One dataset for each project
        self.assertEqual(result[0], mock_dataset_info)
        self.assertEqual(result[1], mock_dataset_info)
        self.assertEqual(mock_get_datasets.call_count, 2)
        self.assertEqual(mock_extract_dataset_info.call_count, 2)


if __name__ == '__main__':
    unittest.main()

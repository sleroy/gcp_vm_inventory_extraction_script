"""
Unit tests for the GCP Client module.
"""

import unittest
import json
import subprocess
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gcp_vm_inventory.gcp_client import GCPClient


class TestGCPClient(unittest.TestCase):
    """Test cases for the GCPClient class."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_id = "test-project"
        self.client = GCPClient(self.project_id)
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_run_gcloud_command_success(self, mock_run):
        """Test running a gcloud command successfully."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.stdout = '{"key": "value"}'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Run the command
        command = ["gcloud", "projects", "list", "--format=json"]
        result = self.client.run_gcloud_command(command)
        
        # Verify the result
        self.assertEqual(result, {"key": "value"})
        mock_run.assert_called_once_with(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_run_gcloud_command_empty_output(self, mock_run):
        """Test running a gcloud command with empty output."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.stdout = ''
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Run the command
        command = ["gcloud", "projects", "list", "--format=json"]
        result = self.client.run_gcloud_command(command)
        
        # Verify the result
        self.assertEqual(result, [])
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_run_gcloud_command_error(self, mock_run):
        """Test running a gcloud command that fails."""
        # Mock the subprocess.run to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")
        
        # Run the command
        command = ["gcloud", "projects", "list", "--format=json"]
        result = self.client.run_gcloud_command(command)
        
        # Verify the result
        self.assertIsNone(result)
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_get_projects(self, mock_run):
        """Test getting a list of projects."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.stdout = '[{"projectId": "test-project", "name": "Test Project"}]'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Get projects
        result = self.client.get_projects()
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["projectId"], "test-project")
        self.assertEqual(result[0]["name"], "Test Project")
    
    @patch('gcp_vm_inventory.gcp_client.bigquery.Client')
    def test_get_bigquery_client(self, mock_bq_client):
        """Test getting a BigQuery client."""
        # Mock the BigQuery client
        mock_client = MagicMock()
        mock_bq_client.return_value = mock_client
        
        # Get the BigQuery client
        result = self.client.get_bigquery_client()
        
        # Verify the result
        self.assertEqual(result, mock_client)
        mock_bq_client.assert_called_once_with(project=self.project_id)
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_check_api_status_enabled(self, mock_run):
        """Test checking API status when API is enabled."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.stdout = 'ENABLED'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Check API status
        result = self.client.check_api_status(self.project_id, "compute.googleapis.com")
        
        # Verify the result
        self.assertEqual(result, "OK")
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_check_api_status_disabled(self, mock_run):
        """Test checking API status when API is disabled."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.stdout = 'DISABLED'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Check API status
        result = self.client.check_api_status(self.project_id, "compute.googleapis.com")
        
        # Verify the result
        self.assertEqual(result, "MISSING")
    
    @patch('gcp_vm_inventory.gcp_client.subprocess.run')
    def test_check_api_status_permission_denied(self, mock_run):
        """Test checking API status when permission is denied."""
        # Mock the subprocess.run to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "cmd", stderr="PERMISSION_DENIED"
        )
        
        # Check API status
        result = self.client.check_api_status(self.project_id, "compute.googleapis.com")
        
        # Verify the result
        self.assertEqual(result, "CREDENTIAL_ISSUE")


if __name__ == '__main__':
    unittest.main()

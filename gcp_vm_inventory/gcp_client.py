"""
GCP Client Module for GCP VM Inventory Tool.

This module provides a unified client interface for interacting with GCP services.
"""

import json
import subprocess
import logging
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GCPClient:
    """Client for interacting with GCP services."""
    
    def __init__(self, project_id: Optional[str] = None, service_account_key: Optional[str] = None):
        """Initialize the GCP client.
        
        Args:
            project_id: The GCP project ID (optional)
            service_account_key: Path to service account key file (optional)
        """
        self.project_id = project_id
        self.service_account_key = service_account_key
        self._bq_client = None
        
        # Check if gcloud is installed
        self._check_gcloud_installed()
        
        # Authenticate with service account if provided
        if service_account_key:
            self._authenticate_service_account()
    
    def _check_gcloud_installed(self) -> Tuple[bool, Optional[str]]:
        """Check if the gcloud command line tool is installed.
        
        Returns:
            Tuple of (is_installed, error_message)
        """
        import shutil
        
        if shutil.which("gcloud") is None:
            error_message = (
                "The Google Cloud SDK (gcloud) command line tool is not installed or not in your PATH.\n"
                "Please install it from https://cloud.google.com/sdk/docs/install and try again.\n"
                "After installation, run 'gcloud init' to configure it."
            )
            logger.error(error_message)
            return False, error_message
        return True, None
    
    def _authenticate_service_account(self) -> bool:
        """Authenticate with the provided service account key.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        auth_command = ["gcloud", "auth", "activate-service-account", "--key-file", self.service_account_key]
        try:
            subprocess.run(
                auth_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            logger.info(f"Successfully authenticated with service account key: {self.service_account_key}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error authenticating with service account: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False
    
    def run_gcloud_command(self, command: List[str], check_json: bool = True, 
                          suppress_errors: bool = False) -> Optional[Union[Dict, List, str]]:
        """Execute a gcloud command and return the output.
        
        Args:
            command: List of command parts to execute
            check_json: Whether to parse the output as JSON
            suppress_errors: Whether to suppress error messages
            
        Returns:
            Parsed JSON object, list, or raw text output
        """
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            
            # Check if output is empty
            if not result.stdout or result.stdout.strip() == "":
                if check_json:
                    return []
                else:
                    return ""
                    
            if check_json:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    if not suppress_errors:
                        logger.warning(f"Command output is not valid JSON: {command}")
                        logger.warning(f"Output: {result.stdout}")
                        logger.warning(f"Error: {str(e)}")
                    return []
            else:
                return result.stdout
        except subprocess.CalledProcessError as e:
            if not suppress_errors:
                logger.error(f"Error executing command: {e}")
                logger.error(f"Error output: {e.stderr}")
                
                # Check for API not enabled error
                if "API not enabled" in e.stderr or "API has not been used" in e.stderr:
                    logger.warning("\nNOTE: This error indicates that an API is not enabled for this project.")
                    logger.warning("You need to enable the API before you can access the information.")
                    logger.warning("You can enable it by visiting the URL in the error message above.")
            
            return None
    
    def get_bigquery_client(self) -> Optional[bigquery.Client]:
        """Get a BigQuery client for the current project.
        
        Returns:
            BigQuery client or None if creation failed
        """
        if self._bq_client:
            return self._bq_client
            
        try:
            if self.service_account_key:
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_key,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                self._bq_client = bigquery.Client(project=self.project_id, credentials=credentials)
            else:
                # Use default credentials from environment
                self._bq_client = bigquery.Client(project=self.project_id)
            
            logger.info(f"Successfully created BigQuery client for project: {self.project_id}")
            return self._bq_client
        except Exception as e:
            logger.error(f"Error creating BigQuery client: {str(e)}")
            return None
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get a list of all accessible GCP projects.
        
        Returns:
            List of project dictionaries
        """
        command = ["gcloud", "projects", "list", "--format=json", "--quiet"]
        result = self.run_gcloud_command(command)
        return result if result else []
    
    def get_organization_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the GCP organization.
        
        Returns:
            Dictionary with organization information or None if not available
        """
        command = ["gcloud", "organizations", "list", "--format=json", "--quiet"]
        return self.run_gcloud_command(command)
    
    def check_api_status(self, project_id: str, api_id: str) -> str:
        """Check if an API is enabled for a project.
        
        Args:
            project_id: The GCP project ID
            api_id: The API ID to check
            
        Returns:
            Status string: "OK", "MISSING", "CREDENTIAL_ISSUE", or "ERROR"
        """
        command = [
            "gcloud", "services", "list",
            "--project", project_id,
            "--filter", f"config.name:{api_id}",
            "--format=value(state)",
            "--quiet"
        ]
        
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            
            output = result.stdout.strip()
            
            if output == "ENABLED":
                return "OK"
            else:
                return "MISSING"
                
        except subprocess.CalledProcessError as e:
            if "PERMISSION_DENIED" in e.stderr:
                return "CREDENTIAL_ISSUE"
            else:
                return "ERROR"

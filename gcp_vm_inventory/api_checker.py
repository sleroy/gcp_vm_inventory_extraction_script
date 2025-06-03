"""
API Checker Module for GCP VM Inventory Tool.

This module provides functionality to check if required GCP APIs are enabled
for projects.
"""

import subprocess
import json
from .core import run_gcloud_command, get_projects


def check_required_apis(project_id, service_account_key=None):
    """Check if required APIs are enabled for a project.
    
    Args:
        project_id: The GCP project ID to check
        service_account_key: Path to service account key file (optional)
    
    Returns:
        Dictionary with API status information
    """
    required_apis = {
        "compute.googleapis.com": "Compute Engine API",
    }
    
    results = {}
    
    for api_id, api_name in required_apis.items():
        # Check if the API is enabled
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
                status = "OK"
            else:
                status = "MISSING"
                
        except subprocess.CalledProcessError as e:
            if "PERMISSION_DENIED" in e.stderr:
                status = "CREDENTIAL_ISSUE"
            else:
                status = "ERROR"
        
        results[api_id] = {
            "name": api_name,
            "status": status
        }
    
    return results


def check_apis_for_projects(projects=None, service_account_key=None):
    """Check required APIs for all projects or a specific project.
    
    Args:
        projects: List of project IDs or a single project ID string
        service_account_key: Path to service account key file (optional)
    
    Returns:
        Dictionary mapping project IDs to API status information
    """
    project_api_status = {}
    
    if isinstance(projects, str):
        # Single project ID provided
        projects = [projects]
    elif not projects:
        # Get all accessible projects
        projects_data = get_projects(service_account_key)
        if not projects_data:
            print("No projects found or unable to access project list.")
            return {}
        
        projects = [p.get('projectId') for p in projects_data]
    
    for project_id in projects:
        print(f"Checking API status for project: {project_id}")
        api_status = check_required_apis(project_id, service_account_key)
        project_api_status[project_id] = api_status
    
    return project_api_status


def display_api_status(project_api_status):
    """Display API status information in a formatted way.
    
    Args:
        project_api_status: Dictionary mapping project IDs to API status information
        
    Returns:
        Boolean indicating if all APIs are OK
    """
    print("\n=== API Status Check Results ===")
    
    all_apis_ok = True
    
    for project_id, api_status in project_api_status.items():
        print(f"\nProject: {project_id}")
        
        for api_id, info in api_status.items():
            status_display = {
                "OK": "\033[92mAPI [OK]\033[0m",                  # Green
                "MISSING": "\033[91mAPI [MISSING]\033[0m",        # Red
                "CREDENTIAL_ISSUE": "\033[93mAPI [CREDENTIAL_ISSUE]\033[0m",  # Yellow
                "ERROR": "\033[91mAPI [ERROR]\033[0m"             # Red
            }.get(info["status"], f"API [{info['status']}]")
            
            print(f"  {info['name']} ({api_id}): {status_display}")
            
            if info["status"] != "OK":
                all_apis_ok = False
    
    return all_apis_ok


def get_api_status_data(project_api_status):
    """Get API status data in a format suitable for display in UI.
    
    Args:
        project_api_status: Dictionary mapping project IDs to API status information
        
    Returns:
        List of dictionaries with API status information
    """
    status_data = []
    
    for project_id, api_status in project_api_status.items():
        for api_id, info in api_status.items():
            status_data.append({
                "project_id": project_id,
                "api_id": api_id,
                "api_name": info["name"],
                "status": info["status"]
            })
    
    return status_data

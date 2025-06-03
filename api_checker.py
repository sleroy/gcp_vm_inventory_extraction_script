#!/usr/bin/env python3
"""
GCP API Checker Module

This module provides functionality to check if required GCP APIs are enabled
for projects.
"""

import subprocess
import json

def run_gcloud_command(command, check_json=True, suppress_errors=False):
    """Execute a gcloud command and return the output as JSON or text."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        if check_json:
            return json.loads(result.stdout)
        else:
            return result.stdout
    except subprocess.CalledProcessError as e:
        if not suppress_errors:
            print(f"Error executing command: {e}")
            print(f"Error output: {e.stderr}")
        return None

def get_projects():
    """Get a list of all accessible GCP projects."""
    command = ["gcloud", "projects", "list", "--format=json", "--quiet"]
    return run_gcloud_command(command)

def check_required_apis(project_id):
    """Check if required APIs are enabled for a project.
    
    Returns a dictionary with API status information.
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

def check_apis_for_projects(projects=None):
    """Check required APIs for all projects or a specific project.
    
    Args:
        projects: List of project IDs or a single project ID string
    
    Returns:
        Dictionary mapping project IDs to API status information
    """
    project_api_status = {}
    
    if isinstance(projects, str):
        # Single project ID provided
        projects = [projects]
    elif not projects:
        # Get all accessible projects
        projects_data = get_projects()
        if not projects_data:
            print("No projects found or unable to access project list.")
            return {}
        
        projects = [p.get('projectId') for p in projects_data]
    
    for project_id in projects:
        print(f"Checking API status for project: {project_id}")
        api_status = check_required_apis(project_id)
        project_api_status[project_id] = api_status
    
    return project_api_status

def display_api_status(project_api_status):
    """Display API status information in a formatted way."""
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

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Check specific project
        project_api_status = check_apis_for_projects(sys.argv[1])
    else:
        # Check all accessible projects
        project_api_status = check_apis_for_projects()
    
    display_api_status(project_api_status)

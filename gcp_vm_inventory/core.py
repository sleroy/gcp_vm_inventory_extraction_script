"""
Core functionality for GCP VM Inventory Tool.

This module contains the core functions for extracting VM information from GCP.
"""

import csv
import json
import os
import subprocess
from datetime import datetime


def run_gcloud_command(command, check_json=True, suppress_errors=False, service_account_key=None):
    """Execute a gcloud command and return the output as JSON or text.
    
    Args:
        command: List of command parts to execute
        check_json: Whether to parse the output as JSON
        suppress_errors: Whether to suppress error messages
        service_account_key: Path to service account key file (optional)
        
    Returns:
        Parsed JSON object or raw text output
    """
    # If service account key is provided, add authentication
    if service_account_key:
        # Add authentication to the command
        auth_command = ["gcloud", "auth", "activate-service-account", "--key-file", service_account_key]
        try:
            subprocess.run(
                auth_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            if not suppress_errors:
                print(f"Error authenticating with service account: {e}")
                print(f"Error output: {e.stderr}")
            return None
    
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
            
            # Check for API not enabled error
            if "API not enabled" in e.stderr or "API has not been used" in e.stderr:
                print("\nNOTE: This error indicates that the Compute Engine API is not enabled for this project.")
                print("You need to enable the API before you can access VM information.")
                print("You can enable it by visiting the URL in the error message above.")
                print("After enabling the API, wait a few minutes for the change to propagate before retrying.")
        
        return None


def get_organization_info(service_account_key=None):
    """Get information about the GCP organization.
    
    Args:
        service_account_key: Path to service account key file (optional)
        
    Returns:
        Dictionary with organization information or None if not available
    """
    command = ["gcloud", "organizations", "list", "--format=json", "--quiet"]
    org_data = run_gcloud_command(command, service_account_key=service_account_key)
    
    if not org_data:
        return None
    
    return org_data


def get_projects(service_account_key=None):
    """Get a list of all accessible GCP projects.
    
    Args:
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of project dictionaries
    """
    command = ["gcloud", "projects", "list", "--format=json", "--quiet"]
    return run_gcloud_command(command, service_account_key=service_account_key)


def get_vms_in_project(project_id, service_account_key=None):
    """Get all VMs in a specific project."""
    command = [
        "gcloud", "compute", "instances", "list",
        "--project", project_id,
        "--format=json",
        "--quiet"  # Prevent interactive prompts
    ]
    return run_gcloud_command(command, service_account_key=service_account_key)


def extract_vm_info(vm, project_id, service_account_key=None):
    """Extract relevant information from VM data."""
    machine_type_parts = vm.get('machineType', '').split('/')
    machine_type = machine_type_parts[-1] if machine_type_parts else 'unknown'
    
    # Extract CPU and memory information
    machine_info = get_machine_type_info(project_id, vm.get('zone', '').split('/')[-1], machine_type, service_account_key)
    
    return {
        'project_id': project_id,
        'vm_id': vm.get('id', 'N/A'),
        'name': vm.get('name', 'N/A'),
        'zone': vm.get('zone', 'N/A').split('/')[-1] if vm.get('zone') else 'N/A',
        'status': vm.get('status', 'N/A'),
        'machine_type': machine_type,
        'cpu_count': machine_info.get('cpu_count', 'N/A'),
        'memory_mb': machine_info.get('memory_mb', 'N/A'),
        'os': get_os_info(vm),
        'creation_timestamp': vm.get('creationTimestamp', 'N/A'),
        'network': vm.get('networkInterfaces', [{}])[0].get('network', 'N/A').split('/')[-1] 
                  if vm.get('networkInterfaces') else 'N/A',
        'internal_ip': vm.get('networkInterfaces', [{}])[0].get('networkIP', 'N/A') 
                      if vm.get('networkInterfaces') else 'N/A',
        'external_ip': get_external_ip(vm)
    }


def get_machine_type_info(project_id, zone, machine_type, service_account_key=None):
    """Get CPU and memory information for a machine type."""
    if machine_type == 'unknown':
        return {'cpu_count': 'N/A', 'memory_mb': 'N/A'}
    
    command = [
        "gcloud", "compute", "machine-types", "describe",
        machine_type,
        "--project", project_id,
        "--zone", zone,
        "--format=json",
        "--quiet"  # Prevent interactive prompts
    ]
    
    result = run_gcloud_command(command, service_account_key=service_account_key)
    if result:
        return {
            'cpu_count': result.get('guestCpus', 'N/A'),
            'memory_mb': result.get('memoryMb', 'N/A')
        }
    return {'cpu_count': 'N/A', 'memory_mb': 'N/A'}


def get_os_info(vm):
    """Extract OS information from VM data."""
    disks = vm.get('disks', [])
    if not disks:
        return 'N/A'
    
    boot_disk = next((disk for disk in disks if disk.get('boot', False)), None)
    if not boot_disk:
        return 'N/A'
    
    licenses = boot_disk.get('licenses', [])
    if not licenses:
        return 'N/A'
    
    # Extract OS name from license URL
    license_parts = licenses[0].split('/')
    if len(license_parts) >= 2:
        return license_parts[-1]
    return 'N/A'


def get_external_ip(vm):
    """Extract external IP address from VM data."""
    network_interfaces = vm.get('networkInterfaces', [])
    if not network_interfaces:
        return 'N/A'
    
    access_configs = network_interfaces[0].get('accessConfigs', [])
    if not access_configs:
        return 'N/A'
    
    return access_configs[0].get('natIP', 'N/A')


def export_to_csv(vm_data, output_dir):
    """Export VM data to a CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"gcp_vm_inventory_{timestamp}.csv")
    
    if not vm_data:
        print("No VM data to export.")
        return None
    
    fieldnames = vm_data[0].keys()
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(vm_data)
    
    print(f"VM inventory exported to {filename}")
    return filename


def collect_vm_inventory(project_id=None, skip_disabled_apis=False, service_account_key=None):
    """Collect VM inventory data from GCP.
    
    Args:
        project_id: Specific project ID to inventory (optional)
        skip_disabled_apis: Whether to skip projects with disabled APIs
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of VM data dictionaries
    """
    all_vm_data = []
    
    if project_id:
        # Process a single project
        print(f"Collecting VM data for project: {project_id}")
        vms = get_vms_in_project(project_id, service_account_key)
        if vms:
            for vm in vms:
                vm_info = extract_vm_info(vm, project_id, service_account_key)
                all_vm_data.append(vm_info)
    else:
        # Process all accessible projects
        projects = get_projects(service_account_key)
        if not projects:
            print("No projects found or unable to access project list.")
            return []
        
        for project in projects:
            project_id = project.get('projectId')
            print(f"\nCollecting VM data for project: {project_id}")
            vms = get_vms_in_project(project_id, service_account_key)
            if vms:
                for vm in vms:
                    vm_info = extract_vm_info(vm, project_id, service_account_key)
                    all_vm_data.append(vm_info)
            elif not skip_disabled_apis:
                print(f"No VM data found for project: {project_id} or API access issue")
            else:
                print(f"Skipping project: {project_id} (possibly due to disabled API)")
    
    return all_vm_data

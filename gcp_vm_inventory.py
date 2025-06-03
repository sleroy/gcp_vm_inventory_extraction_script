#!/usr/bin/env python3
"""
GCP VM Inventory Script

This script extracts information about virtual machines from Google Cloud Platform
and exports the data to a CSV file.
"""

import argparse
import csv
import json
import os
import subprocess
from datetime import datetime


def run_gcloud_command(command):
    """Execute a gcloud command and return the output as JSON."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        return None


def get_projects():
    """Get a list of all accessible GCP projects."""
    command = ["gcloud", "projects", "list", "--format=json"]
    return run_gcloud_command(command)


def get_vms_in_project(project_id):
    """Get all VMs in a specific project."""
    command = [
        "gcloud", "compute", "instances", "list",
        "--project", project_id,
        "--format=json"
    ]
    return run_gcloud_command(command)


def extract_vm_info(vm, project_id):
    """Extract relevant information from VM data."""
    machine_type_parts = vm.get('machineType', '').split('/')
    machine_type = machine_type_parts[-1] if machine_type_parts else 'unknown'
    
    # Extract CPU and memory information
    machine_info = get_machine_type_info(project_id, vm.get('zone', '').split('/')[-1], machine_type)
    
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


def get_machine_type_info(project_id, zone, machine_type):
    """Get CPU and memory information for a machine type."""
    if machine_type == 'unknown':
        return {'cpu_count': 'N/A', 'memory_mb': 'N/A'}
    
    command = [
        "gcloud", "compute", "machine-types", "describe",
        machine_type,
        "--project", project_id,
        "--zone", zone,
        "--format=json"
    ]
    
    result = run_gcloud_command(command)
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


def main():
    parser = argparse.ArgumentParser(description='Extract GCP VM inventory to CSV')
    parser.add_argument('--output-dir', default='output', help='Directory to store the CSV output')
    parser.add_argument('--project', help='Specific GCP project ID to inventory (optional)')
    args = parser.parse_args()
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output_dir)
    
    all_vm_data = []
    
    if args.project:
        # Process a single project
        print(f"Collecting VM data for project: {args.project}")
        vms = get_vms_in_project(args.project)
        if vms:
            for vm in vms:
                vm_info = extract_vm_info(vm, args.project)
                all_vm_data.append(vm_info)
    else:
        # Process all accessible projects
        projects = get_projects()
        if not projects:
            print("No projects found or unable to access project list.")
            return
        
        for project in projects:
            project_id = project.get('projectId')
            print(f"Collecting VM data for project: {project_id}")
            vms = get_vms_in_project(project_id)
            if vms:
                for vm in vms:
                    vm_info = extract_vm_info(vm, project_id)
                    all_vm_data.append(vm_info)
    
    if all_vm_data:
        export_to_csv(all_vm_data, output_dir)
    else:
        print("No VM data collected.")


if __name__ == "__main__":
    main()

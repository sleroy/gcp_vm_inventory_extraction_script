#!/usr/bin/env python3
"""
Command Line Interface for GCP VM Inventory Tool.

This module provides a command-line interface for the GCP VM Inventory Tool.
"""

import argparse
import os
import sys
from .core import collect_vm_inventory, export_to_csv
from .api_checker import check_apis_for_projects, display_api_status
from .utils import check_gcloud_installed, display_disclaimer


def main():
    """Main entry point for the CLI."""
    # Check if gcloud is installed
    is_gcloud_installed, error_message = check_gcloud_installed()
    if not is_gcloud_installed:
        print(error_message)
        sys.exit(1)
    
    # Display disclaimer and get user agreement
    if not display_disclaimer():
        print("You must accept the disclaimer to use this tool. Exiting.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='Extract GCP VM inventory to CSV')
    parser.add_argument('--output-dir', default='output', help='Directory to store the CSV output')
    parser.add_argument('--project', help='Specific GCP project ID to inventory (optional)')
    parser.add_argument('--skip-disabled-apis', action='store_true', 
                      help='Skip projects with disabled Compute Engine API instead of showing errors')
    parser.add_argument('--check-apis-only', action='store_true',
                      help='Only check API status without collecting VM inventory')
    parser.add_argument('--service-account-key', help='Path to service account key file (optional)')
    parser.add_argument('--skip-disclaimer', action='store_true',
                      help='Skip the disclaimer prompt (use with caution)')
    args = parser.parse_args()
    
    # Determine the output directory path
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(script_dir, args.output_dir)
    
    # Check API status first
    service_account_key = args.service_account_key
    if args.project:
        project_api_status = check_apis_for_projects(args.project, service_account_key)
    else:
        project_api_status = check_apis_for_projects(service_account_key=service_account_key)
    
    all_apis_ok = display_api_status(project_api_status)
    
    if args.check_apis_only:
        print("\nAPI check completed. Exiting as requested.")
        return
    
    if not all_apis_ok:
        print("\nWARNING: Some required APIs are not enabled or have credential issues.")
        print("You may encounter errors when collecting VM inventory.")
        proceed = input("Do you want to proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting as requested.")
            return
    
    # Collect VM inventory
    all_vm_data = collect_vm_inventory(
        project_id=args.project,
        skip_disabled_apis=args.skip_disabled_apis,
        service_account_key=service_account_key
    )
    
    if all_vm_data:
        export_to_csv(all_vm_data, output_dir)
    else:
        print("No VM data collected.")


if __name__ == "__main__":
    main()

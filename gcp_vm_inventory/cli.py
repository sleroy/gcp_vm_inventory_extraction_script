#!/usr/bin/env python3
"""
Command Line Interface for GCP VM Inventory Tool.

This module provides a command-line interface for the GCP VM Inventory Tool.
"""

import argparse
import os
import sys
import logging
from .inventory_service import InventoryService
from .utils import display_disclaimer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def display_api_status(api_status_list):
    """Display API status information in a formatted way.
    
    Args:
        api_status_list: List of APIStatus objects
        
    Returns:
        Boolean indicating if all APIs are OK
    """
    print("\n=== API Status Check Results ===")
    
    all_apis_ok = True
    
    # Group by project
    projects = {}
    for api_status in api_status_list:
        if api_status.project_id not in projects:
            projects[api_status.project_id] = []
        projects[api_status.project_id].append(api_status)
    
    for project_id, api_statuses in projects.items():
        print(f"\nProject: {project_id}")
        
        for api_status in api_statuses:
            status_display = {
                "OK": "\033[92mAPI [OK]\033[0m",                  # Green
                "MISSING": "\033[91mAPI [MISSING]\033[0m",        # Red
                "CREDENTIAL_ISSUE": "\033[93mAPI [CREDENTIAL_ISSUE]\033[0m",  # Yellow
                "ERROR": "\033[91mAPI [ERROR]\033[0m"             # Red
            }.get(api_status.status, f"API [{api_status.status}]")
            
            print(f"  {api_status.api_name} ({api_status.api_id}): {status_display}")
            
            if api_status.status != "OK":
                all_apis_ok = False
    
    return all_apis_ok


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='Extract GCP VM inventory to CSV')
    parser.add_argument('--output-dir', default='output', help='Directory to store the CSV output')
    parser.add_argument('--project', help='Specific GCP project ID to inventory (optional)')
    parser.add_argument('--skip-disabled-apis', action='store_true', 
                      help='Skip projects with disabled APIs instead of showing errors')
    parser.add_argument('--check-apis-only', action='store_true',
                      help='Only check API status without collecting VM inventory')
    parser.add_argument('--service-account-key', help='Path to service account key file (optional)')
    parser.add_argument('--skip-disclaimer', action='store_true',
                      help='Skip the disclaimer prompt (use with caution)')
    parser.add_argument('--collect-vms', action='store_true', default=True,
                      help='Collect VM inventory (default: True)')
    parser.add_argument('--collect-sql', action='store_true', default=True,
                      help='Collect Cloud SQL inventory (default: True)')
    parser.add_argument('--collect-bigquery', action='store_true', default=True,
                      help='Collect BigQuery inventory (default: True)')
    parser.add_argument('--collect-gke', action='store_true', default=True,
                      help='Collect GKE inventory (default: True)')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='csv',
                      help='Output format (default: csv)')
    args = parser.parse_args()
    
    # Display disclaimer and get user agreement
    if not args.skip_disclaimer and not display_disclaimer():
        print("You must accept the disclaimer to use this tool. Exiting.")
        sys.exit(1)
    
    # Determine the output directory path
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(script_dir, args.output_dir)
    
    # Create inventory service
    service = InventoryService(
        project_id=args.project,
        service_account_key=args.service_account_key
    )
    
    # Check API status first
    logger.info("Checking API status...")
    api_status_list = service.check_api_status()
    
    all_apis_ok = display_api_status(api_status_list)
    
    if args.check_apis_only:
        logger.info("API check completed. Exiting as requested.")
        return
    
    if not all_apis_ok:
        logger.warning("Some required APIs are not enabled or have credential issues.")
        logger.warning("You may encounter errors when collecting inventory.")
        proceed = input("Do you want to proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            logger.info("Exiting as requested.")
            return
    
    # Collect inventory data
    if args.collect_vms:
        logger.info("Collecting VM inventory...")
        vms = service.collect_vm_inventory(skip_disabled_apis=args.skip_disabled_apis)
        if vms:
            if args.format in ['csv', 'both']:
                service.export_to_csv(vms, output_dir, 'vm_inventory')
            if args.format in ['json', 'both']:
                service.export_to_json(vms, output_dir, 'vm_inventory')
        else:
            logger.warning("No VM data collected.")
    
    if args.collect_bigquery:
        logger.info("Collecting BigQuery inventory...")
        bigquery_datasets = service.collect_bigquery_inventory(skip_disabled_apis=args.skip_disabled_apis)
        if bigquery_datasets:
            if args.format in ['csv', 'both']:
                service.export_to_csv(bigquery_datasets, output_dir, 'bigquery_inventory')
            if args.format in ['json', 'both']:
                service.export_to_json(bigquery_datasets, output_dir, 'bigquery_inventory')
        else:
            logger.warning("No BigQuery data collected.")
    
    if args.collect_sql:
        logger.info("Collecting Cloud SQL inventory...")
        sql_instances = service.collect_sql_inventory(skip_disabled_apis=args.skip_disabled_apis)
        if sql_instances:
            if args.format in ['csv', 'both']:
                service.export_to_csv(sql_instances, output_dir, 'sql_inventory')
            if args.format in ['json', 'both']:
                service.export_to_json(sql_instances, output_dir, 'sql_inventory')
        else:
            logger.warning("No Cloud SQL data collected.")
    
    if args.collect_gke:
        logger.info("Collecting GKE inventory...")
        gke_clusters = service.collect_gke_inventory(skip_disabled_apis=args.skip_disabled_apis)
        if gke_clusters:
            if args.format in ['csv', 'both']:
                service.export_to_csv(gke_clusters, output_dir, 'gke_inventory')
            if args.format in ['json', 'both']:
                service.export_to_json(gke_clusters, output_dir, 'gke_inventory')
        else:
            logger.warning("No GKE data collected.")
    
    logger.info("Inventory collection completed.")


if __name__ == "__main__":
    main()

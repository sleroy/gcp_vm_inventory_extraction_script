#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot BigQuery dataset detection.
"""

import os
import sys
from google.cloud import bigquery
import json

# Project ID from our demo dataset
PROJECT_ID = "sites-web-273920"
DATASET_ID = "demo_dataset"

def diagnose_bigquery_access():
    """Test BigQuery access and dataset visibility."""
    print(f"Testing BigQuery access for project: {PROJECT_ID}")
    
    # 1. Test basic client creation
    try:
        print("\n1. Creating BigQuery client...")
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✓ Client created successfully with project: {client.project}")
    except Exception as e:
        print(f"✗ Failed to create client: {str(e)}")
        print("Check your authentication and permissions.")
        return
    
    # 2. List datasets using the client directly
    try:
        print("\n2. Listing datasets using client.list_datasets()...")
        datasets = list(client.list_datasets())
        if datasets:
            print(f"✓ Found {len(datasets)} datasets:")
            for dataset in datasets:
                print(f"  - {dataset.dataset_id}")
                if dataset.dataset_id == DATASET_ID:
                    print(f"    ✓ Found our demo dataset: {DATASET_ID}")
        else:
            print("✗ No datasets found. Check permissions.")
    except Exception as e:
        print(f"✗ Error listing datasets: {str(e)}")
    
    # 3. Try to access the specific dataset
    try:
        print(f"\n3. Trying to access dataset {DATASET_ID} directly...")
        dataset_ref = client.dataset(DATASET_ID)
        dataset = client.get_dataset(dataset_ref)
        print(f"✓ Successfully accessed dataset: {dataset.dataset_id}")
        print(f"  - Location: {dataset.location}")
        print(f"  - Created: {dataset.created}")
    except Exception as e:
        print(f"✗ Failed to access dataset: {str(e)}")
    
    # 4. List tables in the dataset
    try:
        print(f"\n4. Listing tables in dataset {DATASET_ID}...")
        dataset_ref = client.dataset(DATASET_ID)
        tables = list(client.list_tables(dataset_ref))
        if tables:
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table.table_id}")
        else:
            print("✗ No tables found in the dataset.")
    except Exception as e:
        print(f"✗ Error listing tables: {str(e)}")
    
    # 5. Check authentication method
    print("\n5. Checking authentication method...")
    import google.auth
    try:
        credentials, project = google.auth.default()
        print(f"✓ Using default credentials")
        print(f"  - Project from credentials: {project}")
        print(f"  - Credential type: {type(credentials).__name__}")
    except Exception as e:
        print(f"✗ Error getting default credentials: {str(e)}")
    
    # 6. Check environment variables
    print("\n6. Checking relevant environment variables...")
    env_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "CLOUDSDK_CORE_PROJECT",
        "GCLOUD_PROJECT"
    ]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"  - {var}: {value}")
        else:
            print(f"  - {var}: Not set")
    
    # 7. Compare with the implementation in resources.py
    print("\n7. Testing the get_bigquery_datasets function from resources.py...")
    try:
        from gcp_vm_inventory.resources import get_bigquery_datasets
        print("Calling get_bigquery_datasets()...")
        datasets = get_bigquery_datasets(PROJECT_ID)
        print(f"Function returned {len(datasets)} datasets")
        print("Dataset objects returned:")
        for dataset in datasets:
            print(json.dumps(dataset, indent=2))
    except Exception as e:
        print(f"✗ Error calling get_bigquery_datasets: {str(e)}")

if __name__ == "__main__":
    diagnose_bigquery_access()

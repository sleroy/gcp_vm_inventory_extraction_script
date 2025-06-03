"""
GCP Resources Module for GCP VM Inventory Tool.

This module provides functionality to collect information about various GCP resources
including SQL instances, BigQuery datasets, and GKE clusters.
"""

import json
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from .core import run_gcloud_command, get_projects
from .utils import check_gcloud_installed


def get_bigquery_client(project_id, service_account_key=None):
    """Get a BigQuery client for a specific project.
    
    Args:
        project_id: The GCP project ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        BigQuery client
    """
    try:
        if service_account_key:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_key,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            return bigquery.Client(project=project_id, credentials=credentials)
        else:
            # Use default credentials from environment
            return bigquery.Client(project=project_id)
    except Exception as e:
        print(f"Error creating BigQuery client: {str(e)}")
        return None


def get_sql_instances(project_id, service_account_key=None):
    """Get all Cloud SQL instances in a specific project.
    
    Args:
        project_id: The GCP project ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of SQL instance data
    """
    command = [
        "gcloud", "sql", "instances", "list",
        "--project", project_id,
        "--format=json",
        "--quiet"
    ]
    return run_gcloud_command(command, service_account_key=service_account_key)


def extract_sql_instance_info(instance, project_id):
    """Extract relevant information from SQL instance data.
    
    Args:
        instance: SQL instance data
        project_id: The GCP project ID
        
    Returns:
        Dictionary with SQL instance information
    """
    return {
        'project_id': project_id,
        'instance_name': instance.get('name', 'N/A'),
        'database_version': instance.get('databaseVersion', 'N/A'),
        'region': instance.get('region', 'N/A'),
        'tier': instance.get('settings', {}).get('tier', 'N/A'),
        'storage_size_gb': instance.get('settings', {}).get('dataDiskSizeGb', 'N/A'),
        'storage_type': instance.get('settings', {}).get('dataDiskType', 'N/A'),
        'availability_type': instance.get('settings', {}).get('availabilityType', 'N/A'),
        'state': instance.get('state', 'N/A'),
        'creation_time': instance.get('createTime', 'N/A'),
        'public_ip': instance.get('ipAddresses', [{}])[0].get('ipAddress', 'N/A') 
                    if instance.get('ipAddresses') else 'N/A',
        'private_ip': next((ip.get('ipAddress') for ip in instance.get('ipAddresses', []) 
                          if ip.get('type') == 'PRIVATE'), 'N/A')
    }


def get_bigquery_datasets(project_id, service_account_key=None):
    """Get all BigQuery datasets in a specific project using the API.
    
    Args:
        project_id: The GCP project ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of BigQuery dataset data
    """
    try:
        client = get_bigquery_client(project_id, service_account_key)
        if not client:
            return []
            
        datasets = list(client.list_datasets())
        
        # Convert to a format similar to CLI output for compatibility
        result = []
        for dataset in datasets:
            result.append({
                'datasetReference': {
                    'datasetId': dataset.dataset_id,
                    'projectId': project_id
                },
                'id': f"{project_id}:{dataset.dataset_id}",
                'kind': 'bigquery#dataset',
                'location': dataset.location
            })
        return result
    except Exception as e:
        print(f"Error getting BigQuery datasets for project {project_id}: {str(e)}")
        return []


def get_bigquery_dataset_info(project_id, dataset_id, service_account_key=None):
    """Get detailed information about a BigQuery dataset using the API.
    
    Args:
        project_id: The GCP project ID
        dataset_id: The BigQuery dataset ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        Dictionary with dataset information
    """
    try:
        client = get_bigquery_client(project_id, service_account_key)
        if not client:
            return None
            
        dataset_ref = client.dataset(dataset_id)
        dataset = client.get_dataset(dataset_ref)
        
        # Convert to a dictionary format
        return {
            'id': f"{project_id}:{dataset_id}",
            'datasetReference': {
                'datasetId': dataset_id,
                'projectId': project_id
            },
            'location': dataset.location,
            'creationTime': dataset.created.timestamp() * 1000 if dataset.created else None,  # Convert to milliseconds
            'lastModifiedTime': dataset.modified.timestamp() * 1000 if dataset.modified else None,
            'description': dataset.description
        }
    except Exception as e:
        print(f"Error getting BigQuery dataset info for {project_id}:{dataset_id}: {str(e)}")
        return None


def get_bigquery_tables(project_id, dataset_id, service_account_key=None):
    """Get all tables in a BigQuery dataset using the API.
    
    Args:
        project_id: The GCP project ID
        dataset_id: The BigQuery dataset ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of table data
    """
    try:
        client = get_bigquery_client(project_id, service_account_key)
        if not client:
            return []
            
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))
        
        # Get detailed information for each table
        result = []
        for table in tables:
            try:
                table_ref = client.get_table(table.reference)
                result.append({
                    'id': f"{project_id}:{dataset_id}.{table.table_id}",
                    'tableReference': {
                        'projectId': project_id,
                        'datasetId': dataset_id,
                        'tableId': table.table_id
                    },
                    'numBytes': table_ref.num_bytes,
                    'numRows': table_ref.num_rows,
                    'creationTime': table_ref.created.timestamp() * 1000 if table_ref.created else None,
                    'lastModifiedTime': table_ref.modified.timestamp() * 1000 if table_ref.modified else None,
                    'type': table_ref.table_type
                })
            except Exception as e:
                print(f"Error getting details for table {table.table_id}: {str(e)}")
                # Add basic info without details
                result.append({
                    'id': f"{project_id}:{dataset_id}.{table.table_id}",
                    'tableReference': {
                        'projectId': project_id,
                        'datasetId': dataset_id,
                        'tableId': table.table_id
                    },
                    'numBytes': 0,
                    'numRows': 0
                })
        return result
    except Exception as e:
        print(f"Error getting BigQuery tables for {project_id}:{dataset_id}: {str(e)}")
        return []


def extract_bigquery_info(project_id, service_account_key=None):
    """Extract BigQuery storage information for a project.
    
    Args:
        project_id: The GCP project ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of dictionaries with BigQuery storage information
    """
    bq_info = []
    
    # Get all datasets
    datasets = get_bigquery_datasets(project_id, service_account_key)
    if not datasets:
        return bq_info
    
    for dataset in datasets:
        dataset_id = dataset.get('datasetReference', {}).get('datasetId')
        if not dataset_id:
            continue
        
        # Get dataset details
        dataset_info = get_bigquery_dataset_info(project_id, dataset_id, service_account_key)
        if not dataset_info:
            continue
        
        # Get tables in the dataset
        tables = get_bigquery_tables(project_id, dataset_id, service_account_key)
        if not tables:
            tables = []
        
        # Calculate total storage
        total_size_bytes = sum(table.get('numBytes', 0) for table in tables if 'numBytes' in table)
        total_size_gb = round(total_size_bytes / (1024 * 1024 * 1024), 2) if total_size_bytes > 0 else 0
        
        bq_info.append({
            'project_id': project_id,
            'dataset_id': dataset_id,
            'location': dataset_info.get('location', 'N/A'),
            'creation_time': dataset_info.get('creationTime', 'N/A'),
            'last_modified_time': dataset_info.get('lastModifiedTime', 'N/A'),
            'table_count': len(tables),
            'total_size_gb': total_size_gb
        })
    
    return bq_info


def get_gke_clusters(project_id, service_account_key=None):
    """Get all GKE clusters in a specific project.
    
    Args:
        project_id: The GCP project ID
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of GKE cluster data
    """
    command = [
        "gcloud", "container", "clusters", "list",
        "--project", project_id,
        "--format=json",
        "--quiet"
    ]
    return run_gcloud_command(command, service_account_key=service_account_key)


def extract_gke_cluster_info(cluster, project_id):
    """Extract relevant information from GKE cluster data.
    
    Args:
        cluster: GKE cluster data
        project_id: The GCP project ID
        
    Returns:
        Dictionary with GKE cluster information
    """
    node_pools = cluster.get('nodePools', [])
    total_nodes = sum(pool.get('initialNodeCount', 0) for pool in node_pools)
    
    return {
        'project_id': project_id,
        'cluster_name': cluster.get('name', 'N/A'),
        'location': cluster.get('location', 'N/A'),
        'status': cluster.get('status', 'N/A'),
        'kubernetes_version': cluster.get('currentMasterVersion', 'N/A'),
        'node_count': total_nodes,
        'node_pools': len(node_pools),
        'network': cluster.get('network', 'N/A'),
        'subnetwork': cluster.get('subnetwork', 'N/A'),
        'creation_time': cluster.get('createTime', 'N/A')
    }


def collect_sql_inventory(project_id=None, skip_disabled_apis=False, service_account_key=None):
    """Collect Cloud SQL inventory data from GCP.
    
    Args:
        project_id: Specific project ID to inventory (optional)
        skip_disabled_apis: Whether to skip projects with disabled APIs
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of SQL instance data dictionaries
    """
    # Check if gcloud is installed
    is_gcloud_installed, error_message = check_gcloud_installed()
    if not is_gcloud_installed:
        print(error_message)
        return []
        
    all_sql_data = []
    
    if project_id:
        # Process a single project
        print(f"Collecting SQL data for project: {project_id}")
        instances = get_sql_instances(project_id, service_account_key)
        if instances:
            for instance in instances:
                instance_info = extract_sql_instance_info(instance, project_id)
                all_sql_data.append(instance_info)
    else:
        # Process all accessible projects
        projects = get_projects(service_account_key)
        if not projects:
            print("No projects found or unable to access project list.")
            return []
        
        for project in projects:
            project_id = project.get('projectId')
            print(f"\nCollecting SQL data for project: {project_id}")
            instances = get_sql_instances(project_id, service_account_key)
            if instances:
                for instance in instances:
                    instance_info = extract_sql_instance_info(instance, project_id)
                    all_sql_data.append(instance_info)
            elif not skip_disabled_apis:
                print(f"No SQL data found for project: {project_id} or API access issue")
            else:
                print(f"Skipping project: {project_id} (possibly due to disabled API)")
    
    return all_sql_data


def collect_bigquery_inventory(project_id=None, skip_disabled_apis=False, service_account_key=None):
    """Collect BigQuery inventory data from GCP.
    
    Args:
        project_id: Specific project ID to inventory (optional)
        skip_disabled_apis: Whether to skip projects with disabled APIs
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of BigQuery data dictionaries
    """
    all_bq_data = []
    
    try:
        if project_id:
            # Process a single project
            print(f"Collecting BigQuery data for project: {project_id}")
            bq_info = extract_bigquery_info(project_id, service_account_key)
            all_bq_data.extend(bq_info)
        else:
            # Process all accessible projects
            projects = get_projects(service_account_key)
            if not projects:
                print("No projects found or unable to access project list.")
                return []
            
            for project in projects:
                project_id = project.get('projectId')
                print(f"\nCollecting BigQuery data for project: {project_id}")
                bq_info = extract_bigquery_info(project_id, service_account_key)
                all_bq_data.extend(bq_info)
    except Exception as e:
        print(f"Error collecting BigQuery inventory: {str(e)}")
    
    return all_bq_data


def collect_gke_inventory(project_id=None, skip_disabled_apis=False, service_account_key=None):
    """Collect GKE cluster inventory data from GCP.
    
    Args:
        project_id: Specific project ID to inventory (optional)
        skip_disabled_apis: Whether to skip projects with disabled APIs
        service_account_key: Path to service account key file (optional)
        
    Returns:
        List of GKE cluster data dictionaries
    """
    # Check if gcloud is installed
    is_gcloud_installed, error_message = check_gcloud_installed()
    if not is_gcloud_installed:
        print(error_message)
        return []
        
    all_gke_data = []
    
    if project_id:
        # Process a single project
        print(f"Collecting GKE data for project: {project_id}")
        clusters = get_gke_clusters(project_id, service_account_key)
        if clusters:
            for cluster in clusters:
                cluster_info = extract_gke_cluster_info(cluster, project_id)
                all_gke_data.append(cluster_info)
    else:
        # Process all accessible projects
        projects = get_projects(service_account_key)
        if not projects:
            print("No projects found or unable to access project list.")
            return []
        
        for project in projects:
            project_id = project.get('projectId')
            print(f"\nCollecting GKE data for project: {project_id}")
            clusters = get_gke_clusters(project_id, service_account_key)
            if clusters:
                for cluster in clusters:
                    cluster_info = extract_gke_cluster_info(cluster, project_id)
                    all_gke_data.append(cluster_info)
            elif not skip_disabled_apis:
                print(f"No GKE data found for project: {project_id} or API access issue")
            else:
                print(f"Skipping project: {project_id} (possibly due to disabled API)")
    
    return all_gke_data

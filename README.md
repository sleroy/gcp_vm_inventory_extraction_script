## Development

### Running Tests

The project uses pytest for testing. To run the tests:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests with coverage report
pytest

# Run specific test file
pytest tests/test_gcp_client.py

# Run tests with more verbose output
pytest -v

# Run tests and generate HTML coverage report
pytest --cov=gcp_vm_inventory --cov-report=html
```

The test suite includes:
- Unit tests for the GCP client
- Unit tests for VM inventory collection
- Unit tests for BigQuery inventory collection

### Project Structure

```
gcp-vm-inventory/
├── gcp_vm_inventory/       # Main package
│   ├── __init__.py
│   ├── api_checker.py      # API permission checking
│   ├── bigquery_inventory.py # BigQuery inventory collection
│   ├── cli.py              # Command-line interface
│   ├── core.py             # Core functionality (legacy)
│   ├── gcp_client.py       # GCP client abstraction
│   ├── inventory_service.py # Unified inventory service
│   ├── models.py           # Data models
│   ├── resources.py        # Resource collection (legacy)
│   ├── streamlit_app.py    # Streamlit web UI
│   ├── utils.py            # Utility functions
│   └── vm_inventory.py     # VM inventory collection
├── tests/                  # Test package
│   ├── __init__.py
│   ├── test_bigquery_inventory.py
│   ├── test_gcp_client.py
│   └── test_vm_inventory.py
├── output/                 # Default output directory
├── .coveragerc             # Coverage configuration
├── CHANGES.md              # Change log
├── DISCLAIMER.md           # Legal disclaimer
├── LICENSE                 # License file
├── pytest.ini              # Pytest configuration
├── README.md               # This file
├── requirements.txt        # Dependencies
└── setup.py                # Package setup

## Prerequisites

- Python 3.6+
- Google Cloud SDK installed and configured
- Appropriate permissions to access GCP projects and VM information

## Required GCP Permissions

To use this tool, you need the following permissions in your GCP environment:

### For VM Inventory
- `compute.instances.list` - To list VM instances
- `compute.machineTypes.get` - To get machine type details

### For Cloud SQL Inventory
- `cloudsql.instances.list` - To list SQL instances

### For BigQuery Inventory
- `bigquery.datasets.get` - To get dataset information
- `bigquery.datasets.list` - To list datasets
- `bigquery.tables.list` - To list tables in datasets
- `bigquery.tables.get` - To get table information

### For GKE Inventory
- `container.clusters.list` - To list GKE clusters

### Recommended IAM Roles
The following predefined IAM roles include the necessary permissions:

- `roles/compute.viewer` - For VM inventory
- `roles/cloudsql.viewer` - For Cloud SQL inventory
- `roles/bigquery.dataViewer` - For BigQuery inventory
- `roles/container.viewer` - For GKE inventory

Alternatively, you can create a custom role with just the required permissions listed above.

## Creating a Service Account Key

To use this tool with a service account instead of your personal credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "IAM & Admin" > "Service Accounts"
3. Click "Create Service Account"
4. Enter a name and description for the service account
5. Click "Create and Continue"
6. Assign the following roles:
   - Compute Viewer
   - Cloud SQL Viewer
   - BigQuery Data Viewer
   - Kubernetes Engine Viewer
7. Click "Continue" and then "Done"
8. Find your new service account in the list and click on it
9. Go to the "Keys" tab
10. Click "Add Key" > "Create new key"
11. Choose "JSON" as the key type
12. Click "Create" to download the key file

Keep this key file secure and use it with the `--service-account-key` option or upload it in the Streamlit UI.

## Installation

### From GitHub

1. Clone this repository:
   ```
   git clone https://github.com/sleroy/gcp_vm_inventory_extraction_script.git
   cd gcp_vm_inventory_extraction_script
   ```

2. Install the package and dependencies:
   ```
   pip install -e .
   ```

### Using pip (coming soon)

```
pip install gcp-vm-inventory
```

## Usage

### Command Line Interface

#### Basic usage (all accessible projects):

```
gcp-vm-inventory
```

#### Specify a single project:

```
gcp-vm-inventory --project your-project-id
```

#### Specify a custom output directory:

```
gcp-vm-inventory --output-dir /path/to/output
```

#### Check API permissions only:

```
gcp-vm-inventory --check-apis-only
```

#### Skip projects with disabled APIs:

```
gcp-vm-inventory --skip-disabled-apis
```

#### Use a service account key:

```
gcp-vm-inventory --service-account-key /path/to/key.json
```

### Streamlit Web UI

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser to the URL displayed in the terminal (typically http://localhost:8501)

3. Use the sidebar to configure:
   - Authentication method (current gcloud config or service account key)
   - Project selection (all projects or specific project)
   - Resource types to collect (VMs, SQL, BigQuery, GKE)
   - Other options

4. Click "Check APIs" to verify API permissions
5. Click "Collect Inventory" to gather resource data
6. Use the tabs to view different resource types
7. Use the filtering options to narrow down results
8. Export the data as CSV or Excel using the download links

## Output

The tool generates data with the following fields:

### VM Inventory
- project_id: The GCP project identifier
- vm_id: The unique identifier of the VM
- name: The name of the VM
- zone: The zone where the VM is located
- status: Current status of the VM (running, stopped, etc.)
- machine_type: The machine type of the VM
- cpu_count: Number of vCPUs
- memory_mb: Memory in MB
- os: Operating system information
- creation_timestamp: When the VM was created
- network: Network name
- internal_ip: Internal IP address
- external_ip: External IP address (if any)

### Cloud SQL Inventory
- project_id: The GCP project identifier
- instance_name: The name of the SQL instance
- database_version: The database engine version
- region: The region where the instance is located
- tier: The machine type of the instance
- storage_size_gb: Storage size in GB
- storage_type: Type of storage (SSD, HDD)
- availability_type: High availability configuration
- state: Current state of the instance
- creation_time: When the instance was created
- public_ip: Public IP address (if any)
- private_ip: Private IP address (if any)

### BigQuery Inventory
- project_id: The GCP project identifier
- dataset_id: The BigQuery dataset ID
- location: The location where the dataset is stored
- creation_time: When the dataset was created
- last_modified_time: When the dataset was last modified
- table_count: Number of tables in the dataset
- total_size_gb: Total storage size in GB

### GKE Cluster Inventory
- project_id: The GCP project identifier
- cluster_name: The name of the GKE cluster
- location: The location where the cluster is deployed
- status: Current status of the cluster
- kubernetes_version: The Kubernetes version
- node_count: Number of nodes in the cluster
- node_pools: Number of node pools
- network: Network name
- subnetwork: Subnetwork name
- creation_time: When the cluster was created

## Troubleshooting

### Common Issues

1. **Missing gcloud command line tool**:
   - Error: "The Google Cloud SDK (gcloud) command line tool is not installed or not in your PATH"
   - Solution: Install the Google Cloud SDK from https://cloud.google.com/sdk/docs/install

2. **API not enabled**:
   - Error: "API [MISSING]" in the API status check
   - Solution: Enable the required APIs in the Google Cloud Console or use `gcloud services enable [API_NAME]`

3. **Permission denied**:
   - Error: "API [CREDENTIAL_ISSUE]" in the API status check
   - Solution: Ensure your account or service account has the necessary permissions listed above

4. **BigQuery errors**:
   - Error: Issues with BigQuery data collection
   - Solution: Ensure the BigQuery API is enabled and you have the required permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

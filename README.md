# GCP VM Inventory Tool

This tool extracts information about virtual machines from Google Cloud Platform and exports the data to a CSV file.

## Features

- Lists all VMs across all accessible GCP projects (or a specific project)
- Extracts key information including:
  - Project ID
  - VM ID and name
  - Operating system information
  - Machine type
  - CPU count and memory
  - Zone
  - Network information
  - IP addresses
  - Creation timestamp

## Prerequisites

- Python 3.6+
- Google Cloud SDK installed and configured
- Appropriate permissions to access GCP projects and VM information

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd gcp-vm-inventory
   ```

2. Make the script executable:
   ```
   chmod +x gcp_vm_inventory.py
   ```

## Usage

### Basic usage (all accessible projects):

```
./gcp_vm_inventory.py
```

### Specify a single project:

```
./gcp_vm_inventory.py --project your-project-id
```

### Specify a custom output directory:

```
./gcp_vm_inventory.py --output-dir /path/to/output
```

## Output

The script generates a CSV file with the following columns:

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

## License

[MIT License](LICENSE)

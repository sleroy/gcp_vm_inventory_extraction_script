"""
VM Inventory Module for GCP VM Inventory Tool.

This module provides functionality to collect VM inventory data from GCP.
"""

import logging
from typing import Dict, List, Optional, Any
from .gcp_client import GCPClient
from .models import VMInfo, MachineTypeInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VMInventory:
    """Class for collecting VM inventory data from GCP."""
    
    def __init__(self, client: GCPClient):
        """Initialize the VM inventory collector.
        
        Args:
            client: GCP client instance
        """
        self.client = client
    
    def get_machine_type_info(self, project_id: str, zone: str, machine_type: str) -> MachineTypeInfo:
        """Get CPU and memory information for a machine type.
        
        Args:
            project_id: The GCP project ID
            zone: The zone where the machine type is available
            machine_type: The machine type name
            
        Returns:
            MachineTypeInfo object with CPU and memory information
        """
        if machine_type == 'unknown':
            return MachineTypeInfo()
        
        command = [
            "gcloud", "compute", "machine-types", "describe",
            machine_type,
            "--project", project_id,
            "--zone", zone,
            "--format=json",
            "--quiet"
        ]
        
        result = self.client.run_gcloud_command(command)
        if result:
            return MachineTypeInfo(
                cpu_count=result.get('guestCpus', 0),
                memory_mb=result.get('memoryMb', 0)
            )
        return MachineTypeInfo()
    
    def get_os_info(self, vm: Dict[str, Any]) -> str:
        """Extract OS information from VM data.
        
        Args:
            vm: VM data dictionary
            
        Returns:
            OS information string
        """
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
    
    def get_external_ip(self, vm: Dict[str, Any]) -> str:
        """Extract external IP address from VM data.
        
        Args:
            vm: VM data dictionary
            
        Returns:
            External IP address or 'N/A' if not available
        """
        network_interfaces = vm.get('networkInterfaces', [])
        if not network_interfaces:
            return 'N/A'
        
        access_configs = network_interfaces[0].get('accessConfigs', [])
        if not access_configs:
            return 'N/A'
        
        return access_configs[0].get('natIP', 'N/A')
    
    def extract_vm_info(self, vm: Dict[str, Any], project_id: str) -> VMInfo:
        """Extract relevant information from VM data.
        
        Args:
            vm: VM data dictionary
            project_id: The GCP project ID
            
        Returns:
            VMInfo object with extracted information
        """
        machine_type_parts = vm.get('machineType', '').split('/')
        machine_type = machine_type_parts[-1] if machine_type_parts else 'unknown'
        zone_parts = vm.get('zone', '').split('/')
        zone = zone_parts[-1] if zone_parts else 'N/A'
        
        # Extract CPU and memory information
        machine_info = self.get_machine_type_info(project_id, zone, machine_type)
        
        # Extract network information
        network_interfaces = vm.get('networkInterfaces', [])
        network = 'N/A'
        internal_ip = 'N/A'
        
        if network_interfaces:
            network_parts = network_interfaces[0].get('network', '').split('/')
            network = network_parts[-1] if network_parts else 'N/A'
            internal_ip = network_interfaces[0].get('networkIP', 'N/A')
        
        return VMInfo(
            project_id=project_id,
            vm_id=vm.get('id', 'N/A'),
            name=vm.get('name', 'N/A'),
            zone=zone,
            status=vm.get('status', 'N/A'),
            machine_type=machine_type,
            cpu_count=machine_info.cpu_count,
            memory_mb=machine_info.memory_mb,
            os=self.get_os_info(vm),
            creation_timestamp=vm.get('creationTimestamp', 'N/A'),
            network=network,
            internal_ip=internal_ip,
            external_ip=self.get_external_ip(vm)
        )
    
    def get_vms_in_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all VMs in a specific project.
        
        Args:
            project_id: The GCP project ID
            
        Returns:
            List of VM data dictionaries
        """
        command = [
            "gcloud", "compute", "instances", "list",
            "--project", project_id,
            "--format=json",
            "--quiet"
        ]
        result = self.client.run_gcloud_command(command)
        return result if result else []
    
    def collect_vm_inventory(self, project_id: Optional[str] = None, 
                            skip_disabled_apis: bool = False) -> List[VMInfo]:
        """Collect VM inventory data from GCP.
        
        Args:
            project_id: Specific project ID to inventory (optional)
            skip_disabled_apis: Whether to skip projects with disabled APIs
            
        Returns:
            List of VMInfo objects
        """
        all_vm_data = []
        
        if project_id:
            # Process a single project
            logger.info(f"Collecting VM data for project: {project_id}")
            vms = self.get_vms_in_project(project_id)
            if vms:
                for vm in vms:
                    vm_info = self.extract_vm_info(vm, project_id)
                    all_vm_data.append(vm_info)
                logger.info(f"Found {len(vms)} VMs in project {project_id}")
            else:
                logger.info(f"No VMs found in project {project_id}")
        else:
            # Process all accessible projects
            projects = self.client.get_projects()
            if not projects:
                logger.warning("No projects found or unable to access project list.")
                return []
            
            logger.info(f"Found {len(projects)} projects to check for VMs")
            
            for project in projects:
                project_id = project.get('projectId')
                logger.info(f"Collecting VM data for project: {project_id}")
                vms = self.get_vms_in_project(project_id)
                if vms:
                    for vm in vms:
                        vm_info = self.extract_vm_info(vm, project_id)
                        all_vm_data.append(vm_info)
                    logger.info(f"Found {len(vms)} VMs in project {project_id}")
                elif not skip_disabled_apis:
                    logger.warning(f"No VM data found for project: {project_id} or API access issue")
                else:
                    logger.info(f"Skipping project: {project_id} (possibly due to disabled API)")
        
        logger.info(f"Collected information for {len(all_vm_data)} VMs across all projects")
        return all_vm_data

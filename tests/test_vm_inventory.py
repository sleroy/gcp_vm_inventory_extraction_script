"""
Unit tests for the VM Inventory module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gcp_vm_inventory.vm_inventory import VMInventory
from gcp_vm_inventory.models import VMInfo, MachineTypeInfo


class TestVMInventory(unittest.TestCase):
    """Test cases for the VMInventory class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_client = MagicMock()
        self.vm_inventory = VMInventory(self.mock_client)
        
        # Sample VM data for testing
        self.sample_vm = {
            'id': '1234567890',
            'name': 'test-vm',
            'zone': 'projects/test-project/zones/us-central1-a',
            'status': 'RUNNING',
            'machineType': 'projects/test-project/machineTypes/n1-standard-2',
            'creationTimestamp': '2025-01-01T00:00:00.000Z',
            'networkInterfaces': [
                {
                    'network': 'projects/test-project/global/networks/default',
                    'networkIP': '10.0.0.2',
                    'accessConfigs': [
                        {
                            'natIP': '34.68.105.21'
                        }
                    ]
                }
            ],
            'disks': [
                {
                    'boot': True,
                    'licenses': [
                        'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/licenses/debian-11'
                    ]
                }
            ]
        }
        
        # Sample machine type data for testing
        self.sample_machine_type = {
            'guestCpus': 2,
            'memoryMb': 7680
        }
    
    def test_get_os_info(self):
        """Test extracting OS information from VM data."""
        # Test with sample VM data
        os_info = self.vm_inventory.get_os_info(self.sample_vm)
        self.assertEqual(os_info, 'debian-11')
        
        # Test with missing disks
        vm_no_disks = {'name': 'test-vm'}
        os_info = self.vm_inventory.get_os_info(vm_no_disks)
        self.assertEqual(os_info, 'N/A')
        
        # Test with no boot disk
        vm_no_boot = {'disks': [{'boot': False}]}
        os_info = self.vm_inventory.get_os_info(vm_no_boot)
        self.assertEqual(os_info, 'N/A')
        
        # Test with no licenses
        vm_no_licenses = {'disks': [{'boot': True}]}
        os_info = self.vm_inventory.get_os_info(vm_no_licenses)
        self.assertEqual(os_info, 'N/A')
    
    def test_get_external_ip(self):
        """Test extracting external IP address from VM data."""
        # Test with sample VM data
        external_ip = self.vm_inventory.get_external_ip(self.sample_vm)
        self.assertEqual(external_ip, '34.68.105.21')
        
        # Test with missing network interfaces
        vm_no_network = {'name': 'test-vm'}
        external_ip = self.vm_inventory.get_external_ip(vm_no_network)
        self.assertEqual(external_ip, 'N/A')
        
        # Test with no access configs
        vm_no_access = {'networkInterfaces': [{'networkIP': '10.0.0.2'}]}
        external_ip = self.vm_inventory.get_external_ip(vm_no_access)
        self.assertEqual(external_ip, 'N/A')
    
    @patch('gcp_vm_inventory.vm_inventory.VMInventory.get_machine_type_info')
    def test_extract_vm_info(self, mock_get_machine_type):
        """Test extracting VM information."""
        # Mock the get_machine_type_info method
        mock_get_machine_type.return_value = MachineTypeInfo(cpu_count=2, memory_mb=7680)
        
        # Extract VM info
        vm_info = self.vm_inventory.extract_vm_info(self.sample_vm, 'test-project')
        
        # Verify the result
        self.assertEqual(vm_info.project_id, 'test-project')
        self.assertEqual(vm_info.vm_id, '1234567890')
        self.assertEqual(vm_info.name, 'test-vm')
        self.assertEqual(vm_info.zone, 'us-central1-a')
        self.assertEqual(vm_info.status, 'RUNNING')
        self.assertEqual(vm_info.machine_type, 'n1-standard-2')
        self.assertEqual(vm_info.cpu_count, 2)
        self.assertEqual(vm_info.memory_mb, 7680)
        self.assertEqual(vm_info.os, 'debian-11')
        self.assertEqual(vm_info.creation_timestamp, '2025-01-01T00:00:00.000Z')
        self.assertEqual(vm_info.network, 'default')
        self.assertEqual(vm_info.internal_ip, '10.0.0.2')
        self.assertEqual(vm_info.external_ip, '34.68.105.21')
    
    def test_get_machine_type_info(self):
        """Test getting machine type information."""
        # Mock the client's run_gcloud_command method
        self.mock_client.run_gcloud_command.return_value = self.sample_machine_type
        
        # Get machine type info
        machine_info = self.vm_inventory.get_machine_type_info('test-project', 'us-central1-a', 'n1-standard-2')
        
        # Verify the result
        self.assertEqual(machine_info.cpu_count, 2)
        self.assertEqual(machine_info.memory_mb, 7680)
        
        # Test with unknown machine type
        machine_info = self.vm_inventory.get_machine_type_info('test-project', 'us-central1-a', 'unknown')
        self.assertEqual(machine_info.cpu_count, 0)
        self.assertEqual(machine_info.memory_mb, 0)
    
    @patch('gcp_vm_inventory.vm_inventory.VMInventory.get_vms_in_project')
    @patch('gcp_vm_inventory.vm_inventory.VMInventory.extract_vm_info')
    def test_collect_vm_inventory_single_project(self, mock_extract_vm_info, mock_get_vms):
        """Test collecting VM inventory for a single project."""
        # Mock the get_vms_in_project method
        mock_get_vms.return_value = [self.sample_vm]
        
        # Mock the extract_vm_info method
        mock_vm_info = VMInfo(
            project_id='test-project',
            vm_id='1234567890',
            name='test-vm',
            zone='us-central1-a',
            status='RUNNING',
            machine_type='n1-standard-2',
            cpu_count=2,
            memory_mb=7680
        )
        mock_extract_vm_info.return_value = mock_vm_info
        
        # Collect VM inventory
        result = self.vm_inventory.collect_vm_inventory(project_id='test-project')
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_vm_info)
        mock_get_vms.assert_called_once_with('test-project')
        mock_extract_vm_info.assert_called_once_with(self.sample_vm, 'test-project')
    
    @patch('gcp_vm_inventory.vm_inventory.VMInventory.get_vms_in_project')
    @patch('gcp_vm_inventory.vm_inventory.VMInventory.extract_vm_info')
    def test_collect_vm_inventory_all_projects(self, mock_extract_vm_info, mock_get_vms):
        """Test collecting VM inventory for all projects."""
        # Mock the client's get_projects method
        self.mock_client.get_projects.return_value = [
            {'projectId': 'project-1'},
            {'projectId': 'project-2'}
        ]
        
        # Mock the get_vms_in_project method
        mock_get_vms.return_value = [self.sample_vm]
        
        # Mock the extract_vm_info method
        mock_vm_info = VMInfo(
            project_id='project-1',
            vm_id='1234567890',
            name='test-vm',
            zone='us-central1-a',
            status='RUNNING',
            machine_type='n1-standard-2',
            cpu_count=2,
            memory_mb=7680
        )
        mock_extract_vm_info.return_value = mock_vm_info
        
        # Collect VM inventory
        result = self.vm_inventory.collect_vm_inventory()
        
        # Verify the result
        self.assertEqual(len(result), 2)  # One VM for each project
        self.assertEqual(result[0], mock_vm_info)
        self.assertEqual(result[1], mock_vm_info)
        self.assertEqual(mock_get_vms.call_count, 2)
        self.assertEqual(mock_extract_vm_info.call_count, 2)


if __name__ == '__main__':
    unittest.main()

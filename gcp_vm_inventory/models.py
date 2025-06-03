"""
Data models for GCP VM Inventory Tool.

This module defines the data models used throughout the application.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MachineTypeInfo:
    """Information about a GCP machine type."""
    cpu_count: int = 0
    memory_mb: int = 0


@dataclass
class VMInfo:
    """Information about a GCP VM instance."""
    project_id: str
    vm_id: str
    name: str
    zone: str
    status: str
    machine_type: str
    cpu_count: int = 0
    memory_mb: int = 0
    os: str = "N/A"
    creation_timestamp: str = "N/A"
    network: str = "N/A"
    internal_ip: str = "N/A"
    external_ip: str = "N/A"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_id': self.project_id,
            'vm_id': self.vm_id,
            'name': self.name,
            'zone': self.zone,
            'status': self.status,
            'machine_type': self.machine_type,
            'cpu_count': self.cpu_count,
            'memory_mb': self.memory_mb,
            'os': self.os,
            'creation_timestamp': self.creation_timestamp,
            'network': self.network,
            'internal_ip': self.internal_ip,
            'external_ip': self.external_ip
        }


@dataclass
class SQLInstanceInfo:
    """Information about a GCP Cloud SQL instance."""
    project_id: str
    instance_name: str
    database_version: str = "N/A"
    region: str = "N/A"
    tier: str = "N/A"
    storage_size_gb: int = 0
    storage_type: str = "N/A"
    availability_type: str = "N/A"
    state: str = "N/A"
    creation_time: str = "N/A"
    public_ip: str = "N/A"
    private_ip: str = "N/A"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_id': self.project_id,
            'instance_name': self.instance_name,
            'database_version': self.database_version,
            'region': self.region,
            'tier': self.tier,
            'storage_size_gb': self.storage_size_gb,
            'storage_type': self.storage_type,
            'availability_type': self.availability_type,
            'state': self.state,
            'creation_time': self.creation_time,
            'public_ip': self.public_ip,
            'private_ip': self.private_ip
        }


@dataclass
class BigQueryDatasetInfo:
    """Information about a GCP BigQuery dataset."""
    project_id: str
    dataset_id: str
    location: str = "N/A"
    creation_time: Optional[float] = None
    last_modified_time: Optional[float] = None
    table_count: int = 0
    total_size_gb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_id': self.project_id,
            'dataset_id': self.dataset_id,
            'location': self.location,
            'creation_time': self.creation_time,
            'last_modified_time': self.last_modified_time,
            'table_count': self.table_count,
            'total_size_gb': self.total_size_gb
        }


@dataclass
class GKEClusterInfo:
    """Information about a GCP GKE cluster."""
    project_id: str
    cluster_name: str
    location: str = "N/A"
    status: str = "N/A"
    kubernetes_version: str = "N/A"
    node_count: int = 0
    node_pools: int = 0
    network: str = "N/A"
    subnetwork: str = "N/A"
    creation_time: str = "N/A"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_id': self.project_id,
            'cluster_name': self.cluster_name,
            'location': self.location,
            'status': self.status,
            'kubernetes_version': self.kubernetes_version,
            'node_count': self.node_count,
            'node_pools': self.node_pools,
            'network': self.network,
            'subnetwork': self.subnetwork,
            'creation_time': self.creation_time
        }


@dataclass
class APIStatus:
    """Status of a GCP API."""
    project_id: str
    api_id: str
    api_name: str
    status: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_id': self.project_id,
            'api_id': self.api_id,
            'api_name': self.api_name,
            'status': self.status
        }


@dataclass
class InventoryResult:
    """Result of an inventory collection operation."""
    timestamp: datetime = field(default_factory=datetime.now)
    vms: List[VMInfo] = field(default_factory=list)
    sql_instances: List[SQLInstanceInfo] = field(default_factory=list)
    bigquery_datasets: List[BigQueryDatasetInfo] = field(default_factory=list)
    gke_clusters: List[GKEClusterInfo] = field(default_factory=list)
    api_status: List[APIStatus] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'vms': [vm.to_dict() for vm in self.vms],
            'sql_instances': [sql.to_dict() for sql in self.sql_instances],
            'bigquery_datasets': [bq.to_dict() for bq in self.bigquery_datasets],
            'gke_clusters': [gke.to_dict() for gke in self.gke_clusters],
            'api_status': [api.to_dict() for api in self.api_status]
        }

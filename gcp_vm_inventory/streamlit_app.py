"""
Streamlit UI for GCP VM Inventory Tool.

This module provides a web-based user interface for the GCP VM Inventory Tool
using Streamlit.
"""

import os
import tempfile
import base64
import pandas as pd
import streamlit as st
from datetime import datetime
import io
import json

from .core import collect_vm_inventory, get_projects, get_organization_info
from .api_checker import check_apis_for_projects, get_api_status_data
from .resources import collect_sql_inventory, collect_bigquery_inventory, collect_gke_inventory
from .utils import check_gcloud_installed, get_disclaimer_text


def get_table_download_link(df, filename, file_format="csv"):
    """Generate a link to download the dataframe as a file."""
    if file_format == "csv":
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV File</a>'
    elif file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_data = output.getvalue()
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">Download Excel File</a>'
    else:
        return "Unsupported file format"
    
    return href


def load_gcp_data(service_account_key=None):
    """Load GCP organization and project data."""
    with st.spinner("Loading GCP data..."):
        # Get organization info
        org_info = get_organization_info(service_account_key)
        
        # Get projects list
        projects = get_projects(service_account_key)
        
        return org_info, projects


def show_disclaimer():
    """Show the disclaimer and get user agreement.
    
    Returns:
        bool: True if the user agrees, False otherwise
    """
    st.markdown("## Disclaimer")
    st.text(get_disclaimer_text())
    
    agree = st.checkbox("I have read and agree to the terms above")
    
    if agree:
        st.session_state.disclaimer_accepted = True
    
    return agree


def main():
    """Main function for the Streamlit app."""
    st.set_page_config(
        page_title="GCP VM Inventory Tool",
        page_icon="☁️",
        layout="wide",
    )
    
    st.title("GCP VM Inventory Tool")
    st.write("Extract information about resources from Google Cloud Platform")
    
    # Check if gcloud is installed
    is_gcloud_installed, error_message = check_gcloud_installed()
    if not is_gcloud_installed:
        st.error(error_message)
        st.stop()
    
    # Initialize session state
    if 'disclaimer_accepted' not in st.session_state:
        st.session_state.disclaimer_accepted = False
    if 'org_info' not in st.session_state:
        st.session_state.org_info = None
    if 'projects' not in st.session_state:
        st.session_state.projects = None
    if 'api_status' not in st.session_state:
        st.session_state.api_status = None
    if 'vm_inventory' not in st.session_state:
        st.session_state.vm_inventory = None
    if 'sql_inventory' not in st.session_state:
        st.session_state.sql_inventory = None
    if 'bq_inventory' not in st.session_state:
        st.session_state.bq_inventory = None
    if 'gke_inventory' not in st.session_state:
        st.session_state.gke_inventory = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'service_account_key_path' not in st.session_state:
        st.session_state.service_account_key_path = None
    
    # Show disclaimer if not accepted
    if not st.session_state.disclaimer_accepted:
        if not show_disclaimer():
            st.warning("You must accept the disclaimer to use this tool.")
            st.stop()
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Authentication options
    auth_option = st.sidebar.radio(
        "Authentication Method",
        ["Use Current gcloud Configuration", "Upload Service Account Key"]
    )
    
    # Authentication section
    st.sidebar.subheader("Authentication")
    
    if auth_option == "Upload Service Account Key":
        uploaded_file = st.sidebar.file_uploader("Upload Service Account Key (JSON)", type="json")
        if uploaded_file:
            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                st.session_state.service_account_key_path = tmp_file.name
            
            # Mark as authenticated and load GCP data
            if not st.session_state.authenticated:
                st.session_state.authenticated = True
                st.session_state.org_info, st.session_state.projects = load_gcp_data(st.session_state.service_account_key_path)
        else:
            st.session_state.service_account_key_path = None
            st.session_state.authenticated = False
    else:
        # Using current gcloud configuration
        st.session_state.service_account_key_path = None
        
        # Add a button to authenticate and load GCP data
        if st.sidebar.button("Authenticate with gcloud"):
            st.session_state.authenticated = True
            st.session_state.org_info, st.session_state.projects = load_gcp_data()
    
    # Display organization info if available
    if st.session_state.authenticated and st.session_state.org_info:
        st.sidebar.subheader("GCP Organization")
        for org in st.session_state.org_info:
            st.sidebar.info(f"Organization: {org.get('displayName', 'N/A')} ({org.get('name', 'N/A')})")
    
    # Project selection (only if authenticated)
    if st.session_state.authenticated:
        st.sidebar.subheader("Project Selection")
        
        project_option = st.sidebar.radio(
            "Project Selection",
            ["All Accessible Projects", "Specific Project"]
        )
        
        project_id = None
        if project_option == "Specific Project" and st.session_state.projects:
            # Create a dictionary of project names to IDs for the selectbox
            project_options = {f"{p.get('name', 'Unknown')} ({p.get('projectId', 'Unknown')})": p.get('projectId') 
                              for p in st.session_state.projects}
            
            # Add an option for manual entry
            project_options["Enter Project ID manually"] = "manual"
            
            # Create a selectbox with project names
            selected_project = st.sidebar.selectbox(
                "Select Project",
                options=list(project_options.keys())
            )
            
            # Handle manual entry
            if project_options[selected_project] == "manual":
                project_id = st.sidebar.text_input("Enter Project ID")
            else:
                project_id = project_options[selected_project]
        
        # Other options
        skip_disabled_apis = st.sidebar.checkbox("Skip Projects with Disabled APIs", value=True)
        
        # Resource selection
        st.sidebar.subheader("Resource Types")
        collect_vms = st.sidebar.checkbox("Compute Engine VMs", value=True)
        collect_sql = st.sidebar.checkbox("Cloud SQL Instances", value=True)
        collect_bq = st.sidebar.checkbox("BigQuery Datasets", value=True)
        collect_gke = st.sidebar.checkbox("GKE Clusters", value=True)
        
        # Action buttons
        col1, col2 = st.sidebar.columns(2)
        check_apis_button = col1.button("Check APIs")
        collect_inventory_button = col2.button("Collect Inventory")
        
        # Handle API check
        if check_apis_button:
            with st.spinner("Checking API status..."):
                project_api_status = check_apis_for_projects(
                    projects=project_id,
                    service_account_key=st.session_state.service_account_key_path
                )
                st.session_state.api_status = get_api_status_data(project_api_status)
        
        # Handle inventory collection
        if collect_inventory_button:
            if project_id == "":
                st.error("Please enter a valid Project ID or select 'All Accessible Projects'")
            else:
                # Collect VM inventory
                if collect_vms:
                    with st.spinner("Collecting VM inventory..."):
                        vm_data = collect_vm_inventory(
                            project_id=project_id,
                            skip_disabled_apis=skip_disabled_apis,
                            service_account_key=st.session_state.service_account_key_path
                        )
                        st.session_state.vm_inventory = vm_data if vm_data else []
                
                # Collect SQL inventory
                if collect_sql:
                    with st.spinner("Collecting Cloud SQL inventory..."):
                        sql_data = collect_sql_inventory(
                            project_id=project_id,
                            skip_disabled_apis=skip_disabled_apis,
                            service_account_key=st.session_state.service_account_key_path
                        )
                        st.session_state.sql_inventory = sql_data if sql_data else []
                
                # Collect BigQuery inventory
                if collect_bq:
                    try:
                        with st.spinner("Collecting BigQuery inventory..."):
                            bq_data = collect_bigquery_inventory(
                                project_id=project_id,
                                skip_disabled_apis=skip_disabled_apis,
                                service_account_key=st.session_state.service_account_key_path
                            )
                            # Always update the session state, even with empty list
                            st.session_state.bq_inventory = bq_data if bq_data else []
                    except Exception as e:
                        st.error(f"Error collecting BigQuery inventory: {str(e)}")
                        st.error("Make sure the BigQuery API is enabled and you have the necessary permissions.")
                        # Initialize with empty list on error
                        st.session_state.bq_inventory = []
                
                # Collect GKE inventory
                if collect_gke:
                    with st.spinner("Collecting GKE inventory..."):
                        gke_data = collect_gke_inventory(
                            project_id=project_id,
                            skip_disabled_apis=skip_disabled_apis,
                            service_account_key=st.session_state.service_account_key_path
                        )
                        st.session_state.gke_inventory = gke_data if gke_data else []
                
                # Check if any data was collected
                if all([
                    len(st.session_state.vm_inventory) == 0 if collect_vms else True,
                    len(st.session_state.sql_inventory) == 0 if collect_sql else True,
                    len(st.session_state.bq_inventory) == 0 if collect_bq else True,
                    len(st.session_state.gke_inventory) == 0 if collect_gke else True
                ]):
                    st.warning("No data collected. Check API permissions or project selection.")
    else:
        st.sidebar.info("Please authenticate to access GCP data")
    
    # Main content area
    
    # Display project list if authenticated
    if st.session_state.authenticated and st.session_state.projects:
        with st.expander("Available GCP Projects", expanded=False):
            projects_df = pd.DataFrame([
                {
                    "Project Name": p.get("name", "N/A"),
                    "Project ID": p.get("projectId", "N/A"),
                    "Project Number": p.get("projectNumber", "N/A"),
                    "Creation Time": p.get("createTime", "N/A"),
                    "Status": p.get("lifecycleState", "N/A")
                }
                for p in st.session_state.projects
            ])
            st.dataframe(projects_df)
    
    # Display API status if available
    if st.session_state.api_status:
        st.header("API Status")
        
        # Convert to DataFrame for display
        api_df = pd.DataFrame(st.session_state.api_status)
        
        # Add color coding for status
        def color_status(val):
            if val == 'OK':
                return 'background-color: #8eff8e'  # Green
            elif val == 'MISSING':
                return 'background-color: #ff8e8e'  # Red
            elif val == 'CREDENTIAL_ISSUE':
                return 'background-color: #ffde8e'  # Yellow
            else:
                return 'background-color: #ff8e8e'  # Red
        
        # Display styled DataFrame
        st.dataframe(api_df.style.applymap(color_status, subset=['status']))
    
    # Create tabs for different resource types
    if any([
        hasattr(st.session_state, 'vm_inventory') and st.session_state.vm_inventory is not None,
        hasattr(st.session_state, 'sql_inventory') and st.session_state.sql_inventory is not None,
        hasattr(st.session_state, 'bq_inventory') and st.session_state.bq_inventory is not None,
        hasattr(st.session_state, 'gke_inventory') and st.session_state.gke_inventory is not None
    ]):
        tab1, tab2, tab3, tab4 = st.tabs(["VMs", "Cloud SQL", "BigQuery", "GKE"])
        
        # VM Inventory Tab
        with tab1:
            if hasattr(st.session_state, 'vm_inventory') and st.session_state.vm_inventory:
                st.header("VM Inventory")
                
                # Convert to DataFrame for display
                vm_df = pd.DataFrame(st.session_state.vm_inventory)
                
                if len(vm_df) > 0:
                    # Add filtering options
                    st.subheader("Filter Options")
                    col1, col2, col3 = st.columns(3)
                    
                    # Filter by project (if multiple projects)
                    if 'project_id' in vm_df.columns and len(vm_df['project_id'].unique()) > 1:
                        selected_projects = col1.multiselect(
                            "Filter by Project",
                            options=sorted(vm_df['project_id'].unique()),
                            default=sorted(vm_df['project_id'].unique())
                        )
                        if selected_projects:
                            vm_df = vm_df[vm_df['project_id'].isin(selected_projects)]
                    
                    # Filter by zone
                    if 'zone' in vm_df.columns and len(vm_df['zone'].unique()) > 1:
                        selected_zones = col2.multiselect(
                            "Filter by Zone",
                            options=sorted(vm_df['zone'].unique()),
                            default=sorted(vm_df['zone'].unique())
                        )
                        if selected_zones:
                            vm_df = vm_df[vm_df['zone'].isin(selected_zones)]
                    
                    # Filter by status
                    if 'status' in vm_df.columns and len(vm_df['status'].unique()) > 1:
                        selected_statuses = col3.multiselect(
                            "Filter by Status",
                            options=sorted(vm_df['status'].unique()),
                            default=sorted(vm_df['status'].unique())
                        )
                        if selected_statuses:
                            vm_df = vm_df[vm_df['status'].isin(selected_statuses)]
                    
                    # Display the filtered DataFrame
                    st.dataframe(vm_df)
                    
                    # Export options
                    st.subheader("Export Options")
                    col1, col2 = st.columns(2)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"gcp_vm_inventory_{timestamp}"
                    
                    col1.markdown(get_table_download_link(vm_df, filename, "csv"), unsafe_allow_html=True)
                    col2.markdown(get_table_download_link(vm_df, filename, "excel"), unsafe_allow_html=True)
                else:
                    st.info("No VM instances found in the selected project(s).")
            else:
                st.info("No VM inventory data collected yet.")
        
        # Cloud SQL Tab
        with tab2:
            if hasattr(st.session_state, 'sql_inventory') and st.session_state.sql_inventory:
                st.header("Cloud SQL Inventory")
                
                # Convert to DataFrame for display
                sql_df = pd.DataFrame(st.session_state.sql_inventory)
                
                if len(sql_df) > 0:
                    # Add filtering options
                    st.subheader("Filter Options")
                    col1, col2 = st.columns(2)
                    
                    # Filter by project (if multiple projects)
                    if 'project_id' in sql_df.columns and len(sql_df['project_id'].unique()) > 1:
                        selected_projects = col1.multiselect(
                            "Filter by Project",
                            options=sorted(sql_df['project_id'].unique()),
                            default=sorted(sql_df['project_id'].unique()),
                            key="sql_projects"
                        )
                        if selected_projects:
                            sql_df = sql_df[sql_df['project_id'].isin(selected_projects)]
                    
                    # Filter by database version
                    if 'database_version' in sql_df.columns and len(sql_df['database_version'].unique()) > 1:
                        selected_versions = col2.multiselect(
                            "Filter by Database Version",
                            options=sorted(sql_df['database_version'].unique()),
                            default=sorted(sql_df['database_version'].unique())
                        )
                        if selected_versions:
                            sql_df = sql_df[sql_df['database_version'].isin(selected_versions)]
                    
                    # Display the filtered DataFrame
                    st.dataframe(sql_df)
                    
                    # Export options
                    st.subheader("Export Options")
                    col1, col2 = st.columns(2)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"gcp_sql_inventory_{timestamp}"
                    
                    col1.markdown(get_table_download_link(sql_df, filename, "csv"), unsafe_allow_html=True)
                    col2.markdown(get_table_download_link(sql_df, filename, "excel"), unsafe_allow_html=True)
                else:
                    st.info("No Cloud SQL instances found in the selected project(s).")
            else:
                st.info("No Cloud SQL inventory data collected yet.")
        
        # BigQuery Tab
        with tab3:
            if hasattr(st.session_state, 'bq_inventory') and st.session_state.bq_inventory is not None:
                st.header("BigQuery Inventory")
                
                # Convert to DataFrame for display
                bq_df = pd.DataFrame(st.session_state.bq_inventory)
                
                if len(bq_df) > 0:
                    # Add filtering options
                    st.subheader("Filter Options")
                    col1, col2 = st.columns(2)
                    
                    # Filter by project (if multiple projects)
                    if 'project_id' in bq_df.columns and len(bq_df['project_id'].unique()) > 1:
                        selected_projects = col1.multiselect(
                            "Filter by Project",
                            options=sorted(bq_df['project_id'].unique()),
                            default=sorted(bq_df['project_id'].unique()),
                            key="bq_projects"
                        )
                        if selected_projects:
                            bq_df = bq_df[bq_df['project_id'].isin(selected_projects)]
                    
                    # Filter by location
                    if 'location' in bq_df.columns and len(bq_df['location'].unique()) > 1:
                        selected_locations = col2.multiselect(
                            "Filter by Location",
                            options=sorted(bq_df['location'].unique()),
                            default=sorted(bq_df['location'].unique())
                        )
                        if selected_locations:
                            bq_df = bq_df[bq_df['location'].isin(selected_locations)]
                    
                    # Display the filtered DataFrame
                    st.dataframe(bq_df)
                    
                    # Add visualization for BigQuery storage
                    st.subheader("BigQuery Storage Visualization")
                    
                    # Create a dataframe for visualization
                    if len(bq_df) > 0:
                        # Group by project and sum the total storage
                        project_storage = bq_df.groupby('project_id')['total_size_gb'].sum().reset_index()
                        project_storage = project_storage.sort_values('total_size_gb', ascending=False)
                        
                        # Create bar chart
                        st.bar_chart(
                            project_storage.set_index('project_id')['total_size_gb'],
                            use_container_width=True
                        )
                        
                        # Add dataset-level visualization if there are multiple datasets
                        if len(bq_df) > 1:
                            st.subheader("Storage by Dataset")
                            # Sort datasets by size
                            dataset_storage = bq_df.sort_values('total_size_gb', ascending=False)
                            # Create a unique identifier combining project and dataset
                            dataset_storage['dataset_label'] = dataset_storage['project_id'] + ':' + dataset_storage['dataset_id']
                            # Limit to top 15 datasets to keep chart readable
                            if len(dataset_storage) > 15:
                                st.info("Showing top 15 datasets by storage size")
                                dataset_storage = dataset_storage.head(15)
                            
                            st.bar_chart(
                                dataset_storage.set_index('dataset_label')['total_size_gb'],
                                use_container_width=True
                            )
                            
                        # Add summary statistics
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Storage (GB)", f"{bq_df['total_size_gb'].sum():.2f}")
                        col2.metric("Total Datasets", f"{len(bq_df)}")
                        col3.metric("Total Tables", f"{bq_df['table_count'].sum()}")
                    
                    # Export options
                    st.subheader("Export Options")
                    col1, col2 = st.columns(2)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"gcp_bigquery_inventory_{timestamp}"
                    
                    col1.markdown(get_table_download_link(bq_df, filename, "csv"), unsafe_allow_html=True)
                    col2.markdown(get_table_download_link(bq_df, filename, "excel"), unsafe_allow_html=True)
                else:
                    st.info("No BigQuery datasets found in the selected project(s).")
            else:
                st.info("No BigQuery inventory data collected yet.")
        
        # GKE Tab
        with tab4:
            if hasattr(st.session_state, 'gke_inventory') and st.session_state.gke_inventory:
                st.header("GKE Cluster Inventory")
                
                # Convert to DataFrame for display
                gke_df = pd.DataFrame(st.session_state.gke_inventory)
                
                if len(gke_df) > 0:
                    # Add filtering options
                    st.subheader("Filter Options")
                    col1, col2 = st.columns(2)
                    
                    # Filter by project (if multiple projects)
                    if 'project_id' in gke_df.columns and len(gke_df['project_id'].unique()) > 1:
                        selected_projects = col1.multiselect(
                            "Filter by Project",
                            options=sorted(gke_df['project_id'].unique()),
                            default=sorted(gke_df['project_id'].unique()),
                            key="gke_projects"
                        )
                        if selected_projects:
                            gke_df = gke_df[gke_df['project_id'].isin(selected_projects)]
                    
                    # Filter by location
                    if 'location' in gke_df.columns and len(gke_df['location'].unique()) > 1:
                        selected_locations = col2.multiselect(
                            "Filter by Location",
                            options=sorted(gke_df['location'].unique()),
                            default=sorted(gke_df['location'].unique()),
                            key="gke_locations"
                        )
                        if selected_locations:
                            gke_df = gke_df[gke_df['location'].isin(selected_locations)]
                    
                    # Display the filtered DataFrame
                    st.dataframe(gke_df)
                    
                    # Export options
                    st.subheader("Export Options")
                    col1, col2 = st.columns(2)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"gcp_gke_inventory_{timestamp}"
                    
                    col1.markdown(get_table_download_link(gke_df, filename, "csv"), unsafe_allow_html=True)
                    col2.markdown(get_table_download_link(gke_df, filename, "excel"), unsafe_allow_html=True)
                else:
                    st.info("No GKE clusters found in the selected project(s).")
            else:
                st.info("No GKE cluster inventory data collected yet.")


if __name__ == "__main__":
    main()

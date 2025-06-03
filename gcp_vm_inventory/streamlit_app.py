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


def get_table_download_link(df, filename, file_format="csv"):
    """Generate a link to download the dataframe as a file.
    
    Args:
        df: Pandas DataFrame to download
        filename: Name of the file
        file_format: Format of the file (csv or excel)
        
    Returns:
        HTML link to download the file
    """
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
    """Load GCP organization and project data.
    
    Args:
        service_account_key: Path to service account key file (optional)
        
    Returns:
        Tuple of (organization_info, projects_list)
    """
    with st.spinner("Loading GCP data..."):
        # Get organization info
        org_info = get_organization_info(service_account_key)
        
        # Get projects list
        projects = get_projects(service_account_key)
        
        return org_info, projects


def main():
    """Main function for the Streamlit app."""
    st.set_page_config(
        page_title="GCP VM Inventory Tool",
        page_icon="☁️",
        layout="wide",
    )
    
    st.title("GCP VM Inventory Tool")
    st.write("Extract information about virtual machines from Google Cloud Platform")
    
    # Initialize session state for GCP data
    if 'org_info' not in st.session_state:
        st.session_state.org_info = None
    if 'projects' not in st.session_state:
        st.session_state.projects = None
    if 'api_status' not in st.session_state:
        st.session_state.api_status = None
    if 'vm_inventory' not in st.session_state:
        st.session_state.vm_inventory = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'service_account_key_path' not in st.session_state:
        st.session_state.service_account_key_path = None
    
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
                with st.spinner("Collecting VM inventory..."):
                    vm_data = collect_vm_inventory(
                        project_id=project_id,
                        skip_disabled_apis=skip_disabled_apis,
                        service_account_key=st.session_state.service_account_key_path
                    )
                    if vm_data:
                        st.session_state.vm_inventory = vm_data
                    else:
                        st.error("No VM data collected. Check API permissions or project selection.")
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
    
    # Display VM inventory if available
    if st.session_state.vm_inventory:
        st.header("VM Inventory")
        
        # Convert to DataFrame for display
        vm_df = pd.DataFrame(st.session_state.vm_inventory)
        
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


if __name__ == "__main__":
    main()

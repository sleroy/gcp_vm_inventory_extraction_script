# Change Log

## [0.3.1] - 2025-06-03

### BigQuery Inventory Fix

- Fixed issue with BigQuery dataset detection
- Improved error handling in BigQuery inventory collection
- Enhanced logging for better troubleshooting
- Added more robust dataset and table information retrieval
- Optimized BigQuery client usage

## [0.3.0] - 2025-06-03

### Streamlit UI Feature

- Added web-based user interface using Streamlit
- Restructured project as a proper Python package
- Added support for authentication via service account key
- Implemented filtering options in the UI
- Added export functionality for both CSV and Excel formats
- Created a modular design with separate components for core functionality, CLI, and UI

## [0.2.0] - 2025-06-03

### API Permission Check Feature

- Added preliminary API permission check functionality
- Implemented status display with color-coded indicators: API [OK], API [MISSING], API [CREDENTIAL_ISSUE]
- Created separate module for API checking functionality
- Added command-line option to only check APIs without collecting inventory
- Added interactive prompt to proceed with inventory collection if API issues are detected

## [0.1.0] - 2025-06-03

### Initial Implementation

- Created project structure and basic files
- Implemented Python script to extract VM information from GCP
- Design choices:
  - Used Python for cross-platform compatibility and rich library support
  - Leveraged the Google Cloud SDK CLI commands via subprocess for simplicity and reliability
  - Implemented a modular design with separate functions for different tasks
  - Added support for both single-project and multi-project inventory
  - Included comprehensive VM details beyond the basic requirements:
    - Added VM name, zone, status, and network information
    - Included both internal and external IP addresses
    - Added creation timestamp for age tracking
  - Created timestamped output files to maintain historical inventory data
  - Added command-line arguments for flexibility
  - Implemented error handling for robustness

### Technical Decisions

1. **Data Collection Method**: 
   - Used `gcloud` CLI commands instead of the Python API for simplicity
   - This approach requires less setup (no additional Python packages)
   - Commands are executed with JSON output format for easy parsing

2. **Output Format**:
   - Selected CSV as the primary output format for maximum compatibility with spreadsheet applications
   - Implemented timestamped filenames to preserve historical data

3. **Project Structure**:
   - Created a dedicated git repository for version control
   - Added comprehensive documentation in README.md
   - Implemented a change log to track modifications and design decisions

4. **Error Handling**:
   - Added robust error handling for command execution
   - Implemented graceful fallbacks when information is not available

### Future Improvements

- Add support for exporting to other formats (Excel, JSON)
- Implement parallel processing for faster data collection from multiple projects
- Add filtering options (by zone, machine type, etc.)
- Create a web interface for viewing and filtering the inventory
- Add scheduling capabilities for automated inventory collection

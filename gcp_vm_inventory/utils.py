"""
Utility functions for GCP VM Inventory Tool.
"""

import shutil
import sys
import os

def check_gcloud_installed():
    """Check if the gcloud command line tool is installed and available in the PATH.
    
    Returns:
        tuple: (is_installed, error_message)
    """
    if shutil.which("gcloud") is None:
        error_message = (
            "The Google Cloud SDK (gcloud) command line tool is not installed or not in your PATH.\n"
            "Please install it from https://cloud.google.com/sdk/docs/install and try again.\n"
            "After installation, run 'gcloud init' to configure it."
        )
        return False, error_message
    return True, None

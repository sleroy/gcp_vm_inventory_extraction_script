"""
Utility functions for GCP VM Inventory Tool.
"""

import shutil
import sys
import os
import textwrap


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


def get_disclaimer_text():
    """Get the disclaimer text.
    
    Returns:
        str: The disclaimer text
    """
    disclaimer = """
    DISCLAIMER - PLEASE READ CAREFULLY
    
    This tool:
    - Is provided "AS IS" WITHOUT WARRANTY OF ANY KIND
    - Does NOT collect or store any data in the cloud
    - Processes data only in memory and on your local machine
    - Exports data only to your specified local directory
    - Does not transmit any collected information to external servers
    
    For maximum security:
    1. Review the source code before use
    2. Use a dedicated Google service account with minimal permissions
    3. Revoke service account keys after use if they are no longer needed
    
    By continuing, you acknowledge that:
    1. You have reviewed and accepted this disclaimer
    2. You have the necessary permissions to access the GCP resources
    3. You will use this tool in compliance with your organization's policies
    4. You understand that you are responsible for the security of exported data
    
    For the full disclaimer, see the DISCLAIMER.md file.
    """
    return textwrap.dedent(disclaimer)


def display_disclaimer():
    """Display the disclaimer and get user agreement.
    
    Returns:
        bool: True if the user agrees, False otherwise
    """
    print(get_disclaimer_text())
    print("\nDo you accept these terms and wish to continue? (y/n): ", end="")
    response = input().strip().lower()
    return response == 'y'

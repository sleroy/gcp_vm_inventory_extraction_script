from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gcp-vm-inventory",
    version="0.2.0",
    author="sleroy",
    author_email="your.email@example.com",
    description="A tool to extract VM inventory from Google Cloud Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sleroy/gcp_vm_inventory_extraction_script",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pandas>=1.0.0",
        "streamlit>=1.0.0",
        "xlsxwriter>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "gcp-vm-inventory=gcp_vm_inventory.cli:main",
        ],
    },
)

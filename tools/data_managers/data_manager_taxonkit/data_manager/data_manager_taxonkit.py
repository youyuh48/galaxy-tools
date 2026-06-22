#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import subprocess
import datetime

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Download and populate NCBI taxonomy for TaxonKit')
    parser.add_argument('--out_json', required=True, help='Galaxy Data Manager JSON output file')
    parser.add_argument('--db_name', required=True, help='Display name for the database')
    args = parser.parse_args()

    # Load output destination info from the JSON file provided by Galaxy Data Manager framework
    with open(args.out_json, 'r') as f:
        params = json.load(f)
    
    # Generate a unique ID to register the database (e.g., taxonkit_20260620)
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    db_id = f"taxonkit_{today_str}"

    # Resolve the centralized data path if configured by Galaxy
    data_manager_data_path = params.get('galaxy_data_manager_data_path')
    if not data_manager_data_path:
        data_manager_data_path = os.environ.get('GALAXY_DATA_MANAGER_DATA_PATH')

    if data_manager_data_path:
        # Construct standard centralized directory path for shared reference data
        target_dir = os.path.join(data_manager_data_path, 'taxonkit', db_id)
    else:
        # Fallback to the history dataset extra files path if no central path is set
        target_dir = params['output_data'][0]['extra_files_path']

    # Ensure target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print(f"Downloading NCBI Taxonomy data to: {target_dir}...")
    
    # Download via wget and pipe to tar to extract only the required files (to save space)
    cmd = (
        f"wget -qO- ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz | "
        f"tar -zxv -C '{target_dir}' names.dmp nodes.dmp delnodes.dmp merged.dmp"
    )
    
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"An error occurred while downloading or extracting NCBI taxonomy data: {e}\n")
        sys.exit(1)

    # Create the data table structure to register a new entry in tool-data/taxonkit_format.loc
    data_manager_dict = {
        "data_tables": {
            "taxonkit_format": [
                {
                    "value": db_id,
                    "name": f"{args.db_name} ({today_str})",
                    "path": target_dir
                }
            ]
        }
    }

    # Write the results back to the JSON file to notify Galaxy of the registration
    with open(args.out_json, 'w') as f:
        json.dump(data_manager_dict, f, indent=4)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PDF Generator Wrapper Script
This script acts as a bridge between the Node.js server and the existing PDF generation scripts.
It handles command-line arguments and prepares the environment for the specific PDF templates.
"""

import sys
import os
import shutil
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Generate PDFs using various templates')
    parser.add_argument('--template', required=True, help='Template script to use')
    parser.add_argument('--input', required=True, help='Input Excel file path')
    parser.add_argument('--output', required=True, help='Output directory for PDFs')
    
    args = parser.parse_args()
    
    # Validate template file exists
    if not os.path.exists(args.template):
        print(f"Error: Template file '{args.template}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Use Generic_Template.xlsx as the standard input filename for all templates
    expected_filename = 'Generic_Template.xlsx'
    
    # Copy input file to expected location
    try:
        shutil.copy2(args.input, expected_filename)
        print(f"Copied input file '{args.input}' to '{expected_filename}'")
        
        # Verify the file was copied correctly
        if not os.path.exists(expected_filename):
            raise Exception(f"Failed to create {expected_filename}")
            
        file_size = os.path.getsize(expected_filename)
        print(f"Input file size: {file_size} bytes")
        
    except Exception as e:
        print(f"Error copying input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Change to the script directory to ensure relative paths work
    original_cwd = os.getcwd()
    script_dir = os.path.dirname(os.path.abspath(args.template))
    if script_dir:
        os.chdir(script_dir)
    
    try:
        # Execute the template script with output folder argument
        print(f"Executing template: {args.template}")
        result = subprocess.run([sys.executable, args.template, '--output', args.output], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"Template execution failed with return code {result.returncode}", file=sys.stderr)
            print(f"STDOUT: {result.stdout}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        print("Template executed successfully")
        print(f"STDOUT: {result.stdout}")
        
        # Check if PDFs were generated in the target output directory
        moved_files = 0
        if os.path.exists(args.output):
            pdf_files = [f for f in os.listdir(args.output) if f.endswith('.pdf')]
            moved_files = len(pdf_files)
            print(f"Found {moved_files} PDF files in target directory: {args.output}")
        else:
            print(f"Warning: Target output directory not found: {args.output}")
        
        print(f"Successfully moved {moved_files} PDF files to {args.output}")
        
    except subprocess.TimeoutExpired:
        print("Template execution timed out (5 minutes)", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error executing template: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        
        # Mark input file as processed instead of deleting
        try:
            if os.path.exists(expected_filename):
                processed_filename = expected_filename.replace('.xlsx', '_processed.xlsx')
                shutil.move(expected_filename, processed_filename)
                print(f"Marked file as processed: {processed_filename}")
        except Exception as e:
            print(f"Warning: Could not mark file as processed: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
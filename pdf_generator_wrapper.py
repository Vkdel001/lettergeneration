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
    
    # Copy input file to expected location with robust error handling
    try:
        # First, verify input file exists
        if not os.path.exists(args.input):
            raise Exception(f"Input file does not exist: {args.input}")
        
        # Copy the file
        shutil.copy2(args.input, expected_filename)
        print(f"Copied input file '{args.input}' to '{expected_filename}'")
        
        # Verify the file was copied correctly
        if not os.path.exists(expected_filename):
            raise Exception(f"Failed to create {expected_filename}")
            
        # Verify file size
        input_size = os.path.getsize(args.input)
        output_size = os.path.getsize(expected_filename)
        
        if input_size != output_size:
            raise Exception(f"File size mismatch: input={input_size}, output={output_size}")
            
        print(f"Input file successfully copied: {output_size} bytes")
        
        # Validate the copied file has required columns
        try:
            import pandas as pd
            test_df = pd.read_excel(expected_filename, engine='openpyxl')
            available_cols = list(test_df.columns)
            required_cols = ['Policy No', 'Arrears Amount']
            
            print(f"Copied file validation:")
            print(f"  - Rows: {len(test_df)}")
            print(f"  - Columns: {len(available_cols)}")
            print(f"  - Column names: {available_cols}")
            
            missing_required = [col for col in required_cols if col not in available_cols]
            if missing_required:
                raise Exception(f"Copied file missing required columns: {missing_required}")
            
            has_email = 'EMAIL_ID' in available_cols
            print(f"  - EMAIL_ID present: {has_email}")
            
            if not has_email:
                print("WARNING: EMAIL_ID column not found - email functionality may not work")
            
            print("File validation successful!")
            
        except Exception as validation_error:
            print(f"WARNING: File validation failed: {validation_error}")
            print("Proceeding anyway, but there may be issues...")
        
        # Also create a timestamped backup for debugging
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"Generic_Template_backup_{timestamp}.xlsx"
        shutil.copy2(expected_filename, backup_name)
        print(f"Created backup: {backup_name}")
        
    except Exception as e:
        print(f"Error copying input file: {e}", file=sys.stderr)
        
        # Try to find alternative files as fallback
        print("Attempting to find alternative Excel files...", file=sys.stderr)
        import glob
        xlsx_files = glob.glob("*.xlsx") + glob.glob("temp_uploads/*.xlsx")
        
        if xlsx_files:
            print(f"Found alternative files: {xlsx_files}", file=sys.stderr)
            for alt_file in xlsx_files:
                if os.path.exists(alt_file) and alt_file != expected_filename:
                    try:
                        shutil.copy2(alt_file, expected_filename)
                        print(f"Using alternative file: {alt_file}", file=sys.stderr)
                        break
                    except Exception as alt_error:
                        print(f"Failed to use {alt_file}: {alt_error}", file=sys.stderr)
                        continue
        
        # Final check
        if not os.path.exists(expected_filename):
            print(f"FATAL: Could not create {expected_filename}", file=sys.stderr)
            sys.exit(1)
    
    # Change to the script directory to ensure relative paths work
    original_cwd = os.getcwd()
    script_dir = os.path.dirname(os.path.abspath(args.template))
    if script_dir:
        os.chdir(script_dir)
    
    try:
        # Execute the template script with output folder argument
        print(f"Executing template: {args.template}")
        # Increased timeout for very large files (6 hours for processing thousands of rows)
        timeout_seconds = 21600  # 6 hours (6 * 60 * 60)
        print(f"Starting template execution with {timeout_seconds/60:.0f} minute timeout...")
        result = subprocess.run([sys.executable, args.template, '--output', args.output], 
                              capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout_seconds)
        
        if result.returncode != 0:
            print(f"Template execution failed with return code {result.returncode}", file=sys.stderr)
            print(f"STDOUT: {result.stdout}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        print("Template executed successfully")
        print(f"STDOUT: {result.stdout}")
        
        # Check if PDFs were generated in the target output directory (including subfolders)
        moved_files = 0
        if os.path.exists(args.output):
            # Count PDFs in main folder
            pdf_files = [f for f in os.listdir(args.output) if f.endswith('.pdf')]
            moved_files = len(pdf_files)
            
            # Count PDFs in protected subfolder
            protected_path = os.path.join(args.output, 'protected')
            if os.path.exists(protected_path):
                protected_pdfs = [f for f in os.listdir(protected_path) if f.endswith('.pdf')]
                moved_files += len(protected_pdfs)
                print(f"Found {len(protected_pdfs)} PDFs in protected folder")
            
            # Count PDFs in unprotected subfolder
            unprotected_path = os.path.join(args.output, 'unprotected')
            if os.path.exists(unprotected_path):
                unprotected_pdfs = [f for f in os.listdir(unprotected_path) if f.endswith('.pdf')]
                moved_files += len(unprotected_pdfs)
                print(f"Found {len(unprotected_pdfs)} PDFs in unprotected folder")
            
            print(f"Found {moved_files} total PDF files in directory: {args.output}")
        else:
            print(f"Warning: Target output directory not found: {args.output}")
        
        print(f"Successfully generated {moved_files} PDF files in {args.output}")
        
    except subprocess.TimeoutExpired:
        print(f"Template execution timed out ({timeout_seconds/60:.0f} minutes)", file=sys.stderr)
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
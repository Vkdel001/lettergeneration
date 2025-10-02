#!/usr/bin/env python3
"""
PDF Combiner Script
Combines multiple PDF files into a single PDF file.
"""

import sys
import os
import argparse
from PyPDF2 import PdfFileReader, PdfFileWriter
import json

def combine_pdfs(pdf_files, output_path):
    """Combine multiple PDF files into one using unprotected PDFs."""
    try:
        writer = PdfFileWriter()
        
        # Convert paths to use unprotected folder if dual structure exists
        unprotected_files = []
        for pdf_file in pdf_files:
            # Check if this is from a dual folder structure
            if '/protected/' in pdf_file or '\\protected\\' in pdf_file:
                # Convert to unprotected path
                unprotected_file = pdf_file.replace('/protected/', '/unprotected/').replace('\\protected\\', '\\unprotected\\')
                if os.path.exists(unprotected_file):
                    unprotected_files.append(unprotected_file)
                    print(f"Using unprotected version: {unprotected_file}")
                else:
                    unprotected_files.append(pdf_file)
                    print(f"Unprotected version not found, using original: {pdf_file}")
            else:
                # Check if unprotected subfolder exists in the same directory
                folder_path = os.path.dirname(pdf_file)
                unprotected_folder = os.path.join(folder_path, 'unprotected')
                if os.path.exists(unprotected_folder):
                    filename = os.path.basename(pdf_file)
                    unprotected_file = os.path.join(unprotected_folder, filename)
                    if os.path.exists(unprotected_file):
                        unprotected_files.append(unprotected_file)
                        print(f"Using unprotected version: {unprotected_file}")
                    else:
                        unprotected_files.append(pdf_file)
                        print(f"Unprotected version not found, using original: {pdf_file}")
                else:
                    unprotected_files.append(pdf_file)
        
        for pdf_file in unprotected_files:
            if os.path.exists(pdf_file):
                print(f"Adding: {pdf_file}")
                reader = PdfFileReader(pdf_file)
                
                # Add all pages from this PDF (should be unprotected)
                for page_num in range(reader.getNumPages()):
                    page = reader.getPage(page_num)
                    writer.addPage(page)
            else:
                print(f"Warning: File not found: {pdf_file}")
        
        # Write the combined PDF to unprotected folder if possible
        output_dir = os.path.dirname(output_path)
        if os.path.basename(output_dir) == 'protected':
            # Save to unprotected folder instead
            unprotected_dir = output_dir.replace('protected', 'unprotected')
            if os.path.exists(unprotected_dir):
                output_path = os.path.join(unprotected_dir, os.path.basename(output_path))
                print(f"Saving combined PDF to unprotected folder: {output_path}")
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully combined {len(unprotected_files)} PDFs into {output_path}")
        return True
        
    except Exception as e:
        print(f"Error combining PDFs: {str(e)}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Combine PDF files')
    parser.add_argument('--files', required=True, help='JSON array of PDF file paths')
    parser.add_argument('--output', required=True, help='Output PDF file path')
    
    args = parser.parse_args()
    
    try:
        # Parse the JSON array of file paths
        pdf_files = json.loads(args.files)
        
        if not pdf_files:
            print("Error: No PDF files provided", file=sys.stderr)
            sys.exit(1)
        
        success = combine_pdfs(pdf_files, args.output)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"Error parsing file list: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
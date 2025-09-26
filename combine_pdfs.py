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
    """Combine multiple PDF files into one."""
    try:
        writer = PdfFileWriter()
        
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                print(f"Adding: {pdf_file}")
                reader = PdfFileReader(pdf_file)
                
                # Add all pages from this PDF
                for page_num in range(reader.getNumPages()):
                    page = reader.getPage(page_num)
                    writer.addPage(page)
            else:
                print(f"Warning: File not found: {pdf_file}")
        
        # Write the combined PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully combined {len(pdf_files)} PDFs into {output_path}")
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
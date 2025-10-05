#!/usr/bin/env python3
"""
Quick PDF Combiner - Standalone script to combine all PDFs in a folder
Usage: python quick_combine.py folder_name output_name
"""

import sys
import os
import glob
from PyPDF2 import PdfFileReader as PdfReader, PdfFileWriter as PdfWriter

def combine_folder_pdfs(folder_name, output_name):
    """Combine all unprotected PDFs in a folder"""
    
    # Check for unprotected subfolder first
    unprotected_path = os.path.join(folder_name, 'unprotected')
    if os.path.exists(unprotected_path):
        pdf_pattern = os.path.join(unprotected_path, '*.pdf')
        output_path = os.path.join(unprotected_path, f"{output_name}.pdf")
        print(f"Using unprotected folder: {unprotected_path}")
    else:
        pdf_pattern = os.path.join(folder_name, '*.pdf')
        output_path = os.path.join(folder_name, f"{output_name}.pdf")
        print(f"Using main folder: {folder_name}")
    
    # Find all PDF files
    pdf_files = glob.glob(pdf_pattern)
    pdf_files.sort()  # Sort for consistent order
    
    if not pdf_files:
        print(f"No PDF files found in {folder_name}")
        return False
    
    print(f"Found {len(pdf_files)} PDF files to combine")
    
    try:
        writer = PdfWriter()
        
        for i, pdf_file in enumerate(pdf_files):
            print(f"Adding file {i+1}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
            reader = PdfReader(pdf_file)
            
            for page_num in range(reader.getNumPages()):
                page = reader.getPage(page_num)
                writer.addPage(page)
        
        # Write combined PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"✅ Successfully combined {len(pdf_files)} PDFs into: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error combining PDFs: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python quick_combine.py folder_name output_name")
        print("Example: python quick_combine.py output_sph_September2025 all_sph")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    output_name = sys.argv[2]
    
    if not os.path.exists(folder_name):
        print(f"Error: Folder '{folder_name}' not found")
        sys.exit(1)
    
    success = combine_folder_pdfs(folder_name, output_name)
    sys.exit(0 if success else 1)
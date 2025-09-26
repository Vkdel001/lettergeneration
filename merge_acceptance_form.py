#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Separate script to merge Renewal Acceptance Form with generated healthcare renewal letters
This keeps the main generation script safe and working
"""

import os
import glob
import subprocess
import sys

# Try to use pypdf (newer version) first, fallback to PyPDF2
try:
    from pypdf import PdfReader, PdfWriter
    USE_PYPDF = True
    print("[INFO] Using pypdf for PDF merging")
except ImportError:
    try:
        from PyPDF2 import PdfFileReader as PdfReader, PdfFileWriter as PdfWriter
        USE_PYPDF = False
        print("[INFO] Using PyPDF2 for PDF merging")
    except ImportError:
        print("[ERROR] Neither pypdf nor PyPDF2 is available. Please install one:")
        print("pip install pypdf")
        sys.exit(1)

def merge_acceptance_form():
    """Merge the acceptance form with all generated renewal letters"""
    
    # Path to the acceptance form
    form_pdf_path = "Renewal Acceptance Form - HealthSense Plan V2 0.pdf"
    
    if not os.path.exists(form_pdf_path):
        print(f"❌ Error: {form_pdf_path} not found!")
        print("Please ensure the Renewal Acceptance Form PDF is in the current directory.")
        return
    
    # Find all generated renewal PDFs
    output_folder = "output_renewals"
    if not os.path.exists(output_folder):
        print(f"❌ Error: {output_folder} folder not found!")
        print("Please run healthcare_renewal_final.py first to generate renewal letters.")
        return
    
    pdf_files = glob.glob(f"{output_folder}/*.pdf")
    
    if not pdf_files:
        print(f"❌ No PDF files found in {output_folder}")
        return
    
    print(f"📋 Found {len(pdf_files)} renewal letters to merge with acceptance form...")
    
    success_count = 0
    error_count = 0
    
    for pdf_file in pdf_files:
        try:
            # Create backup filename
            backup_file = pdf_file.replace('.pdf', '_backup.pdf')
            os.rename(pdf_file, backup_file)
            
            # Try different merging approaches
            merged_successfully = False
            
            # Method 1: Try pypdf/PyPDF2
            try:
                output_writer = PdfWriter()
                
                # Add pages from the renewal letter
                with open(backup_file, 'rb') as letter_file:
                    letter_reader = PdfReader(letter_file)
                    if USE_PYPDF:
                        # pypdf syntax
                        for page in letter_reader.pages:
                            output_writer.add_page(page)
                    else:
                        # PyPDF2 syntax
                        for page_num in range(letter_reader.getNumPages()):
                            output_writer.addPage(letter_reader.getPage(page_num))
                
                # Add pages from the acceptance form
                with open(form_pdf_path, 'rb') as form_file:
                    form_reader = PdfReader(form_file)
                    if USE_PYPDF:
                        # pypdf syntax
                        for page in form_reader.pages:
                            output_writer.add_page(page)
                    else:
                        # PyPDF2 syntax
                        for page_num in range(form_reader.getNumPages()):
                            output_writer.addPage(form_reader.getPage(page_num))
                
                # Write merged PDF
                with open(pdf_file, 'wb') as output_file:
                    output_writer.write(output_file)
                
                # Check if file was created successfully and has reasonable size
                if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 10000:  # At least 10KB
                    merged_successfully = True
                
            except Exception as pdf_error:
                print(f"⚠️ PDF library method failed for {os.path.basename(pdf_file)}: {str(pdf_error)}")
            
            # Method 2: Try using system command (if available)
            if not merged_successfully:
                try:
                    # Try using pdftk if available
                    result = subprocess.run([
                        'pdftk', backup_file, form_pdf_path, 'cat', 'output', pdf_file
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 10000:
                        merged_successfully = True
                        print(f"✅ Used pdftk for: {os.path.basename(pdf_file)}")
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                    pass  # pdftk not available or failed
            
            if merged_successfully:
                # Remove backup if successful
                os.remove(backup_file)
                filename = os.path.basename(pdf_file)
                print(f"✅ Merged: {filename}")
                success_count += 1
            else:
                # Restore backup if all methods failed
                if os.path.exists(backup_file):
                    os.rename(backup_file, pdf_file)
                filename = os.path.basename(pdf_file)
                print(f"❌ All merge methods failed for: {filename}")
                error_count += 1
            
        except Exception as e:
            # Restore backup if merging failed
            if os.path.exists(backup_file):
                os.rename(backup_file, pdf_file)
            
            filename = os.path.basename(pdf_file)
            print(f"❌ Failed to merge: {filename} - {str(e)}")
            error_count += 1
    
    print(f"\n🎉 Merging completed!")
    print(f"✅ Successfully merged: {success_count} files")
    if error_count > 0:
        print(f"❌ Failed to merge: {error_count} files")

if __name__ == "__main__":
    merge_acceptance_form()
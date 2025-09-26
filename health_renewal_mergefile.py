#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Healthcare Renewal Letters Merger
Merges all individual renewal letters from output_renewals folder into a single PDF for printing
"""

import os
import glob
import fitz  # PyMuPDF
from datetime import datetime

def merge_all_renewal_letters():
    """Merge all healthcare renewal letters into a single PDF for printing"""
    
    # Define paths
    input_folder = "output_renewals"
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"Healthcare_Renewal_Letters_Merged_{timestamp}.pdf"
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"❌ Error: {input_folder} folder not found!")
        print("Please run healthcare_renewal_final.py first to generate renewal letters.")
        return
    
    # Find all PDF files in the output folder
    pdf_files = glob.glob(f"{input_folder}/*.pdf")
    
    if not pdf_files:
        print(f"❌ No PDF files found in {input_folder}")
        print("Please run healthcare_renewal_final.py first to generate renewal letters.")
        return
    
    # Sort files alphabetically for consistent ordering
    pdf_files.sort()
    
    print(f"📋 Found {len(pdf_files)} renewal letters to merge...")
    print(f"📄 Output file: {output_filename}")
    print()
    
    try:
        # Create new merged document
        merged_doc = fitz.open()
        
        total_pages = 0
        processed_files = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                filename = os.path.basename(pdf_file)
                print(f"🔄 Processing ({i}/{len(pdf_files)}): {filename}")
                
                # Open the renewal letter PDF
                letter_doc = fitz.open(pdf_file)
                page_count = letter_doc.page_count
                
                # Add all pages from this renewal letter
                for page_num in range(page_count):
                    merged_doc.insert_pdf(letter_doc, from_page=page_num, to_page=page_num)
                
                letter_doc.close()
                
                total_pages += page_count
                processed_files += 1
                
                print(f"   ✅ Added {page_count} pages")
                
            except Exception as e:
                print(f"   ❌ Failed to process {filename}: {str(e)}")
                continue
        
        if processed_files == 0:
            print("❌ No files could be processed successfully!")
            merged_doc.close()
            return
        
        # Save the merged PDF
        print(f"\n💾 Saving merged PDF...")
        merged_doc.save(output_filename)
        merged_doc.close()
        
        # Verify the output file
        if os.path.exists(output_filename):
            file_size = os.path.getsize(output_filename)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"\n🎉 Merge completed successfully!")
            print(f"📄 Output file: {output_filename}")
            print(f"📊 Statistics:")
            print(f"   • Processed files: {processed_files}/{len(pdf_files)}")
            print(f"   • Total pages: {total_pages}")
            print(f"   • File size: {file_size_mb:.2f} MB")
            print(f"\n📋 Ready for printing!")
            
        else:
            print("❌ Failed to create merged PDF file!")
            
    except Exception as e:
        print(f"❌ Error during merging: {str(e)}")
        return

def print_usage():
    """Print usage instructions"""
    print("Healthcare Renewal Letters Merger")
    print("=" * 40)
    print()
    print("This script merges all individual healthcare renewal letters")
    print("from the 'output_renewals' folder into a single PDF for printing.")
    print()
    print("Prerequisites:")
    print("1. Run healthcare_renewal_final.py to generate renewal letters")
    print("2. Ensure PyMuPDF is installed: pip install PyMuPDF")
    print()
    print("Output:")
    print("• Single merged PDF with timestamp")
    print("• All renewal letters in alphabetical order")
    print("• Ready for batch printing")
    print()

if __name__ == "__main__":
    try:
        import fitz
        print_usage()
        merge_all_renewal_letters()
        
    except ImportError:
        print("❌ PyMuPDF not installed. Please install it:")
        print("pip install PyMuPDF")
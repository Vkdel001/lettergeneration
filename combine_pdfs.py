#!/usr/bin/env python3
"""
PDF Combiner Script
Combines multiple PDF files into a single PDF file.
"""

import sys
import os
import argparse
import json

# Try PyMuPDF first (better for image preservation), fallback to PyPDF2
PDF_LIBRARY = None
try:
    import fitz  # PyMuPDF
    PDF_LIBRARY = "pymupdf"
    print("Using PyMuPDF (better image preservation)")
except ImportError:
    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader, PdfWriter
        PYPDF2_VERSION = "new"
        PDF_LIBRARY = "pypdf2"
        print("Using PyPDF2 v3+ (PdfReader/PdfWriter) - WARNING: May affect QR codes")
    except ImportError:
        try:
            from PyPDF2 import PdfFileReader as PdfReader, PdfFileWriter as PdfWriter
            PYPDF2_VERSION = "old"
            PDF_LIBRARY = "pypdf2"
            print("Using PyPDF2 v2 (PdfFileReader/PdfFileWriter) - WARNING: May affect QR codes")
        except ImportError:
            try:
                # Very old PyPDF2 versions (1.x)
                from PyPDF2 import PdfFileReader, PdfFileWriter
                PYPDF2_VERSION = "very_old"
                PDF_LIBRARY = "pypdf2"
                print("Using PyPDF2 v1.x - WARNING: May affect QR codes")
            except ImportError:
                print("ERROR: No PDF library found. Please install: pip install PyMuPDF")
                sys.exit(1)

def combine_pdfs_pymupdf(pdf_files, output_path):
    """Combine PDFs using PyMuPDF (better image preservation)."""
    try:
        print(f"Starting PDF combination of {len(pdf_files)} files using PyMuPDF...")
        
        # Create new document
        combined_doc = fitz.open()
        
        for i, pdf_file in enumerate(pdf_files):
            if os.path.exists(pdf_file):
                print(f"Adding file {i+1}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
                try:
                    # Open source PDF
                    source_doc = fitz.open(pdf_file)
                    
                    # Insert all pages (preserves images better)
                    combined_doc.insert_pdf(source_doc)
                    
                    print(f"Successfully added {source_doc.page_count} pages")
                    source_doc.close()
                    
                except Exception as file_error:
                    print(f"ERROR: Failed to process {pdf_file}: {str(file_error)}")
                    continue
            else:
                print(f"Warning: File not found: {pdf_file}")
        
        # Save combined PDF
        print(f"Writing combined PDF to: {output_path}")
        combined_doc.save(output_path)
        
        # Verify output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            page_count = combined_doc.page_count
            combined_doc.close()
            
            if file_size > 0:
                print(f"Successfully combined {len(pdf_files)} PDFs into {output_path}")
                print(f"Total pages: {page_count}")
                print(f"Output file size: {file_size:,} bytes")
                return True
            else:
                print("ERROR: Output file is empty")
                return False
        else:
            print("ERROR: Output file was not created")
            return False
            
    except Exception as e:
        print(f"Error combining PDFs with PyMuPDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def combine_pdfs_pypdf2(pdf_files, output_path):
    """Combine PDFs using PyPDF2 (fallback method)."""
    try:
        # Initialize writer based on PyPDF2 version
        if PYPDF2_VERSION == "very_old":
            writer = PdfFileWriter()
        else:
            writer = PdfWriter()
        
        print(f"Starting PDF combination of {len(pdf_files)} files using PyPDF2...")
        
        # Process all files with PyPDF2
        for i, pdf_file in enumerate(pdf_files):
            if os.path.exists(pdf_file):
                print(f"Adding file {i+1}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
                try:
                    # Initialize reader based on PyPDF2 version
                    if PYPDF2_VERSION == "very_old":
                        reader = PdfFileReader(pdf_file)
                    else:
                        reader = PdfReader(pdf_file)
                    
                    # Add all pages
                    if PYPDF2_VERSION == "new":
                        for page in reader.pages:
                            writer.add_page(page)
                        page_count = len(reader.pages)
                    else:
                        for page_num in range(reader.getNumPages()):
                            page = reader.getPage(page_num)
                            writer.addPage(page)
                        page_count = reader.getNumPages()
                    
                    print(f"Successfully processed {page_count} pages from {os.path.basename(pdf_file)}")
                    
                except Exception as file_error:
                    print(f"ERROR: Failed to process {pdf_file}: {str(file_error)}")
                    continue
            else:
                print(f"Warning: File not found: {pdf_file}")
        
        # Write output
        print(f"Writing combined PDF to: {output_path}")
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        # Verify output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 0:
                print(f"Successfully combined {len(pdf_files)} PDFs into {output_path}")
                print(f"Output file size: {file_size:,} bytes")
                return True
            else:
                print("ERROR: Output file is empty")
                return False
        else:
            print("ERROR: Output file was not created")
            return False
            
    except Exception as e:
        print(f"Error combining PDFs with PyPDF2: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Combine PDF files')
    parser.add_argument('--files', help='JSON array of PDF file paths')
    parser.add_argument('--files-from-file', help='Path to JSON file containing PDF file paths')
    parser.add_argument('--output', required=True, help='Output PDF file path')
    
    args = parser.parse_args()
    
    print(f"Combine PDFs started...")
    print(f"Output path: {args.output}")
    
    try:
        # Parse the JSON array of file paths (from command line or file)
        if args.files_from_file:
            print(f"Reading file list from: {args.files_from_file}")
            with open(args.files_from_file, 'r') as f:
                pdf_files = json.load(f)
            print(f"Parsed {len(pdf_files)} file paths from JSON file")
        elif args.files:
            pdf_files = json.loads(args.files)
            print(f"Parsed {len(pdf_files)} file paths from command line JSON")
        else:
            print("Error: Either --files or --files-from-file must be provided", file=sys.stderr)
            sys.exit(1)
        
        if not pdf_files:
            print("Error: No PDF files provided", file=sys.stderr)
            sys.exit(1)
        
        # Validate that files exist
        existing_files = []
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                existing_files.append(pdf_file)
                print(f"✓ Found: {pdf_file}")
            else:
                print(f"✗ Missing: {pdf_file}")
        
        if not existing_files:
            print("Error: No valid PDF files found", file=sys.stderr)
            sys.exit(1)
        
        print(f"Processing {len(existing_files)} valid PDF files...")
        
        # Use PyMuPDF if available (better for QR codes), otherwise PyPDF2
        if PDF_LIBRARY == "pymupdf":
            success = combine_pdfs_pymupdf(existing_files, args.output)
        else:
            success = combine_pdfs_pypdf2(existing_files, args.output)
        
        if success:
            print("✅ PDF combination completed successfully!")
            sys.exit(0)
        else:
            print("❌ PDF combination failed!", file=sys.stderr)
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"Error parsing file list: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
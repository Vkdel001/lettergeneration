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

def get_unprotected_pdfs(folder_path):
    """Get PDF files from unprotected subfolder only."""
    unprotected_path = os.path.join(folder_path, 'unprotected')
    
    if not os.path.exists(unprotected_path):
        print(f"Warning: Unprotected folder not found at {unprotected_path}")
        # Fallback to main folder for legacy structure
        if os.path.exists(folder_path):
            pdf_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                        if f.endswith('.pdf')]
            print(f"Using legacy structure: found {len(pdf_files)} PDFs in main folder")
            return pdf_files
        return []
    
    pdf_files = [os.path.join(unprotected_path, f) for f in os.listdir(unprotected_path) 
                if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} unprotected PDFs to combine")
    print("Note: Protected PDFs are excluded (each has unique password)")
    return pdf_files

def create_combined_folder(base_folder):
    """Create combined subfolder if it doesn't exist."""
    combined_path = os.path.join(base_folder, 'combined')
    if not os.path.exists(combined_path):
        os.makedirs(combined_path)
        print(f"Created combined folder: {combined_path}")
    return combined_path

def main():
    parser = argparse.ArgumentParser(description='Combine PDF files from unprotected folder')
    parser.add_argument('--files', help='JSON array of PDF file paths (legacy)')
    parser.add_argument('--files-from-file', help='Path to JSON file containing PDF file paths (legacy)')
    parser.add_argument('--folder', help='Base folder containing unprotected/ subfolder')
    parser.add_argument('--output', required=True, help='Output PDF file path')
    parser.add_argument('--name', help='Output filename (without extension)')
    
    args = parser.parse_args()
    
    print(f"🔗 PDF Combiner Started")
    print(f"========================")
    
    try:
        pdf_files = []
        
        # New folder-based approach (preferred)
        if args.folder:
            print(f"📁 Processing folder: {args.folder}")
            pdf_files = get_unprotected_pdfs(args.folder)
            
            # Create combined folder and update output path
            combined_folder = create_combined_folder(args.folder)
            
            if args.name:
                output_filename = f"{args.name}.pdf"
            else:
                folder_name = os.path.basename(args.folder.rstrip('/'))
                timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
                output_filename = f"{folder_name}_combined_{timestamp}.pdf"
            
            args.output = os.path.join(combined_folder, output_filename)
            print(f"📄 Output file: {args.output}")
            
        # Legacy file list approach (backward compatibility)
        else:
            print("⚠️  Using legacy file list mode")
            if args.files_from_file:
                print(f"Reading file list from: {args.files_from_file}")
                with open(args.files_from_file, 'r') as f:
                    pdf_files = json.load(f)
                print(f"Parsed {len(pdf_files)} file paths from JSON file")
            elif args.files:
                pdf_files = json.loads(args.files)
                print(f"Parsed {len(pdf_files)} file paths from command line JSON")
            else:
                print("Error: Either --folder, --files, or --files-from-file must be provided", file=sys.stderr)
                sys.exit(1)
        
        if not pdf_files:
            print("❌ Error: No PDF files found to combine", file=sys.stderr)
            sys.exit(1)
        
        # Validate that files exist
        existing_files = []
        missing_count = 0
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                existing_files.append(pdf_file)
                print(f"✓ Found: {os.path.basename(pdf_file)}")
            else:
                print(f"✗ Missing: {pdf_file}")
                missing_count += 1
        
        if not existing_files:
            print("❌ Error: No valid PDF files found", file=sys.stderr)
            sys.exit(1)
        
        if missing_count > 0:
            print(f"⚠️  Warning: {missing_count} files were missing and will be skipped")
        
        print(f"📊 Processing {len(existing_files)} valid PDF files...")
        print(f"🎯 Using {PDF_LIBRARY.upper()} library for combining")
        
        # Use PyMuPDF if available (better for QR codes), otherwise PyPDF2
        if PDF_LIBRARY == "pymupdf":
            success = combine_pdfs_pymupdf(existing_files, args.output)
        else:
            success = combine_pdfs_pypdf2(existing_files, args.output)
        
        if success:
            print("✅ PDF combination completed successfully!")
            print(f"📁 Combined file saved to: {args.output}")
            
            # Show file info
            if os.path.exists(args.output):
                file_size = os.path.getsize(args.output)
                size_mb = file_size / (1024 * 1024)
                print(f"📊 File size: {size_mb:.1f} MB ({file_size:,} bytes)")
            
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
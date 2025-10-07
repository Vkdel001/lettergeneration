#!/usr/bin/env python3
"""
PDF Combiner Script
Combines multiple PDF files into a single PDF file.
"""

import sys
import os
import argparse
import json

# Handle different PyPDF2 versions
try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_VERSION = "new"
    print("Using PyPDF2 v3+ (PdfReader/PdfWriter)")
except ImportError:
    try:
        from PyPDF2 import PdfFileReader as PdfReader, PdfFileWriter as PdfWriter
        PYPDF2_VERSION = "old"
        print("Using PyPDF2 v2 (PdfFileReader/PdfFileWriter)")
    except ImportError:
        try:
            # Very old PyPDF2 versions (1.x)
            from PyPDF2 import PdfFileReader, PdfFileWriter
            PYPDF2_VERSION = "very_old"
            print("Using PyPDF2 v1.x (PdfFileReader/PdfFileWriter)")
        except ImportError:
            print("ERROR: PyPDF2 not found. Please install: pip install PyPDF2")
            sys.exit(1)

def combine_pdfs(pdf_files, output_path):
    """Combine multiple PDF files into one using unprotected PDFs."""
    try:
        # Initialize writer based on PyPDF2 version
        if PYPDF2_VERSION == "very_old":
            writer = PdfFileWriter()
        else:
            writer = PdfWriter()
        
        print(f"Starting PDF combination of {len(pdf_files)} files...")
        
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
        
        for i, pdf_file in enumerate(unprotected_files):
            if os.path.exists(pdf_file):
                print(f"Adding file {i+1}/{len(unprotected_files)}: {os.path.basename(pdf_file)}")
                try:
                    # Initialize reader based on PyPDF2 version
                    if PYPDF2_VERSION == "very_old":
                        reader = PdfFileReader(pdf_file)
                    else:
                        reader = PdfReader(pdf_file)
                    
                    # Validate PDF before processing
                    try:
                        if PYPDF2_VERSION == "new":
                            page_count = len(reader.pages)
                        else:
                            page_count = reader.getNumPages()
                        
                        if page_count == 0:
                            print(f"WARNING: {pdf_file} has no pages, skipping")
                            continue
                            
                        print(f"Processing {page_count} pages from {os.path.basename(pdf_file)}")
                        
                    except Exception as validation_error:
                        print(f"ERROR: Cannot read {pdf_file}: {str(validation_error)}")
                        continue
                    
                    # Add all pages from this PDF (should be unprotected)
                    if PYPDF2_VERSION == "new":
                        # PyPDF2 v3+ syntax - process pages individually for better error handling
                        for page_idx, page in enumerate(reader.pages):
                            try:
                                writer.add_page(page)
                            except Exception as page_error:
                                print(f"ERROR: Failed to add page {page_idx + 1} from {pdf_file}: {str(page_error)}")
                                continue
                    elif PYPDF2_VERSION == "old":
                        # PyPDF2 v2 syntax - process pages individually
                        for page_num in range(reader.getNumPages()):
                            try:
                                page = reader.getPage(page_num)
                                writer.addPage(page)
                            except Exception as page_error:
                                print(f"ERROR: Failed to add page {page_num + 1} from {pdf_file}: {str(page_error)}")
                                continue
                    else:
                        # PyPDF2 v1.x syntax (very old) - process pages individually
                        for page_num in range(reader.getNumPages()):
                            try:
                                page = reader.getPage(page_num)
                                writer.addPage(page)
                            except Exception as page_error:
                                print(f"ERROR: Failed to add page {page_num + 1} from {pdf_file}: {str(page_error)}")
                                continue
                    
                    print(f"Successfully processed {page_count} pages from {os.path.basename(pdf_file)}")
                    
                except Exception as file_error:
                    print(f"ERROR: Failed to process {pdf_file}: {str(file_error)}")
                    import traceback
                    traceback.print_exc()
                    continue
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
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and output_dir != '':
            print(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
        else:
            print("Output file is in current directory")
        
        print(f"Writing combined PDF to: {output_path}")
        
        # Validate writer has pages before saving
        try:
            if PYPDF2_VERSION == "new":
                total_pages = len(writer.pages)
            else:
                total_pages = writer.getNumPages() if hasattr(writer, 'getNumPages') else len(writer._pages)
            
            if total_pages == 0:
                print("ERROR: No pages to write - all PDFs failed to process")
                return False
                
            print(f"Writing {total_pages} total pages to combined PDF...")
            
        except Exception as validation_error:
            print(f"WARNING: Could not validate page count: {str(validation_error)}")
        
        # Write with better error handling
        try:
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            # Verify the output file was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    print(f"Successfully combined {len(unprotected_files)} PDFs into {output_path}")
                    print(f"Output file size: {file_size:,} bytes")
                    return True
                else:
                    print("ERROR: Output file is empty")
                    return False
            else:
                print("ERROR: Output file was not created")
                return False
                
        except Exception as write_error:
            print(f"ERROR: Failed to write combined PDF: {str(write_error)}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"Error combining PDFs: {str(e)}", file=sys.stderr)
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
        
        success = combine_pdfs(existing_files, args.output)
        
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
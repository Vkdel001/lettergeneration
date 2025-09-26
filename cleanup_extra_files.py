#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick script to remove unwanted AcceptanceForm files
"""

import os
import glob

def cleanup_acceptance_files():
    """Remove unwanted _AcceptanceForm.pdf files"""
    
    output_folder = "output_renewals"
    
    if not os.path.exists(output_folder):
        print(f"❌ {output_folder} folder not found")
        return
    
    # Find all AcceptanceForm files
    acceptance_files = glob.glob(f"{output_folder}/*_AcceptanceForm.pdf")
    
    if not acceptance_files:
        print("✅ No unwanted AcceptanceForm files found")
        return
    
    print(f"🧹 Found {len(acceptance_files)} AcceptanceForm files to remove...")
    
    removed_count = 0
    for file_path in acceptance_files:
        try:
            filename = os.path.basename(file_path)
            os.remove(file_path)
            print(f"🗑️ Removed: {filename}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {filename}: {str(e)}")
    
    print(f"\n✅ Cleanup completed! Removed {removed_count} files")
    print("💡 Now you only have the merged PDFs with renewal letter + acceptance form")

if __name__ == "__main__":
    cleanup_acceptance_files()
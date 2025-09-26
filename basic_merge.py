#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic PDF merger using only standard libraries + reportlab
No additional dependencies required
"""

import os
import glob
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def copy_files_method():
    """Simple approach: Just copy the acceptance form to each folder with a different name"""
    
    # Path to the acceptance form
    form_pdf_path = "Renewal Acceptance Form - HealthSense Plan V2 0.pdf"
    
    if not os.path.exists(form_pdf_path):
        print(f"❌ Error: {form_pdf_path} not found!")
        return
    
    # Find all generated renewal PDFs
    output_folder = "output_renewals"
    if not os.path.exists(output_folder):
        print(f"❌ Error: {output_folder} folder not found!")
        return
    
    pdf_files = glob.glob(f"{output_folder}/*.pdf")
    
    if not pdf_files:
        print(f"❌ No PDF files found in {output_folder}")
        return
    
    print(f"📋 Found {len(pdf_files)} renewal letters...")
    print("📋 Creating separate acceptance forms for each customer...")
    
    success_count = 0
    
    for pdf_file in pdf_files:
        try:
            # Extract the base filename (without extension)
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Create acceptance form filename for this customer
            form_copy_name = f"{output_folder}/{base_name}_AcceptanceForm.pdf"
            
            # Copy the acceptance form
            shutil.copy2(form_pdf_path, form_copy_name)
            
            print(f"✅ Created: {os.path.basename(form_copy_name)}")
            success_count += 1
            
        except Exception as e:
            filename = os.path.basename(pdf_file)
            print(f"❌ Failed to create form for: {filename} - {str(e)}")
    
    print(f"\n🎉 Process completed!")
    print(f"✅ Created {success_count} acceptance forms")
    print(f"\n📁 Each customer now has:")
    print(f"   • Renewal letter: [PolicyNo]_[Name].pdf")
    print(f"   • Acceptance form: [PolicyNo]_[Name]_AcceptanceForm.pdf")
    print(f"\n💡 You can send both files to each customer or print them together.")

def create_instruction_pdf():
    """Create a simple instruction PDF explaining the two-file approach"""
    
    instruction_file = "output_renewals/README_Instructions.pdf"
    
    try:
        c = canvas.Canvas(instruction_file, pagesize=A4)
        width, height = A4
        margin = 50
        
        y_pos = height - margin - 50
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y_pos, "Healthcare Renewal Package Instructions")
        y_pos -= 40
        
        # Instructions
        c.setFont("Helvetica", 12)
        instructions = [
            "Each customer renewal package contains two PDF files:",
            "",
            "1. [PolicyNo]_[CustomerName].pdf",
            "   → This is the renewal letter with payment QR code",
            "",
            "2. [PolicyNo]_[CustomerName]_AcceptanceForm.pdf", 
            "   → This is the form for the customer to fill and return",
            "",
            "Instructions for customers:",
            "• Review the renewal letter for premium and coverage details",
            "• Use the QR code for convenient payment via Juice/MyT Money",
            "• Fill out the acceptance form and return it to NIC",
            "",
            "This two-file approach ensures both documents remain",
            "clear and easy to handle for customers and staff."
        ]
        
        for line in instructions:
            c.drawString(margin, y_pos, line)
            y_pos -= 20
        
        c.save()
        print(f"✅ Created instruction file: {instruction_file}")
        
    except Exception as e:
        print(f"⚠️ Could not create instruction file: {str(e)}")

if __name__ == "__main__":
    print("🔄 Using basic file copying method (no PDF merging required)...")
    copy_files_method()
    create_instruction_pdf()
    print("\n💡 This approach avoids PDF compatibility issues entirely!")
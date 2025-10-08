# -*- coding: utf-8 -*-
# Import necessary libraries for data handling, HTTP requests, QR code generation, and PDF creation
import pandas as pd
import sys
import io
from datetime import datetime

# Set UTF-8 encoding for stdout to handle Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import segno
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.colors import gray

import os
import re
from datetime import datetime
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfFileReader, PdfFileWriter

# Verify font files exist
cambria_regular_path = os.path.join(os.path.dirname(__file__), 'fonts', 'cambria.ttf')
cambria_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'cambriab.ttf')

if not os.path.isfile(cambria_regular_path):
    raise FileNotFoundError(f"Font file not found: {cambria_regular_path}")
if not os.path.isfile(cambria_bold_path):
    raise FileNotFoundError(f"Font file not found: {cambria_bold_path}")

# Register Cambria fonts
try:
    pdfmetrics.registerFont(TTFont('Cambria', cambria_regular_path))
    pdfmetrics.registerFont(TTFont('Cambria-Bold', cambria_bold_path))
    print("[OK] Cambria (from cambria.ttf) and Cambria-Bold (from cambriab.ttf) fonts registered successfully")
except Exception as e:
    raise Exception(f"Failed to register fonts: {str(e)}")

# Read the Excel file containing policyholder data
try:
    df = pd.read_excel("Generic_Template.xlsx", engine='openpyxl')
    print(f"[OK] Excel file loaded successfully with {len(df)} rows")
    print(f"[INFO] Available columns: {list(df.columns)}")
    
    # Check if DataFrame is empty
    if len(df) == 0:
        print("[WARNING] Excel file is empty")
        sys.exit(1)
        
except FileNotFoundError:
    print("[ERROR] Excel file 'Generic_Template.xlsx' not found in the current directory")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error reading Excel file: {str(e)}")
    sys.exit(1)

# Create a folder to store generated PDFs - use dynamic folder name
import sys
output_folder = "output_letters"  # Default folder

# Debug: Print all command line arguments
print(f"[DEBUG] Command line arguments: {sys.argv}")

# Check if output folder is passed as command line argument
if len(sys.argv) > 1:
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_folder = sys.argv[i + 1]
            print(f"[DEBUG] Found --output argument: {output_folder}")
            break

os.makedirs(output_folder, exist_ok=True)
print(f"[INFO] Using output folder: {output_folder}")

# Define custom paragraph styles explicitly
styles = {}

# Define custom 'BodyText' style for body paragraphs
styles['BodyText'] = ParagraphStyle(
    name='BodyText',
    fontName='Cambria',
    fontSize=10.5,
    leading=12,
    spaceAfter=6,
    alignment=TA_JUSTIFY
)

styles['disclaimerText'] = ParagraphStyle(
    name='disclaimerText',
    fontName='Cambria',
    fontSize=10.5,
    leading=10,
    spaceAfter=6,
    alignment=1,
    textColor=gray

)

# Define custom 'BoldText' style for headings
styles['BoldText'] = ParagraphStyle(
    name='BoldText',
    fontName='Cambria-Bold',
    fontSize=11,
    leading=13,
    spaceAfter=6
)

# Define custom 'SalutationText' style for the "Dear..." line and address
styles['SalutationText'] = ParagraphStyle(
    name='SalutationText',
    fontName='Cambria-Bold',
    fontSize=10.5,
    leading=6,
    spaceAfter=5
)

# Define custom 'FooterText' style for the absolute footer at the bottom
styles['FooterText'] = ParagraphStyle(
    name='FooterText',
    fontName='Cambria',
    fontSize=10.5,
    leading=13,
    spaceAfter=0,
    alignment=1  # Center alignment for footer text
)

# Define custom 'BodyFooterText' style for the "Kindly disregard..." text
styles['BodyFooterText'] = ParagraphStyle(
    name='BodyFooterText',
    fontName='Cambria',
    fontSize=10.5,
    leading=13,
    spaceAfter=6,
    alignment=0  # Left alignment
)

# Define custom 'TableText' style for table data to enforce center alignment
styles['TableText'] = ParagraphStyle(
    name='TableText',
    fontName='Cambria',
    fontSize=9,
    leading=11,
    spaceAfter=6,
    alignment=1
)

# Define custom 'TableTextBold' style for table headers
styles['TableTextBold'] = ParagraphStyle(
    name='TableTextBold',
    fontName='Cambria-Bold',
    fontSize=10,
    leading=11,
    spaceAfter=6,
    alignment=1
)

# Iterate through each row in the DataFrame to process individual policyholder data
for index, row in df.iterrows():
    print(f"[PROCESSING] Row {index + 1} of {len(df)}")
    
    # Extract relevant data from the current row
    owner1_title = row.get('Owner 1 Title', '')
    owner1_first_name = row.get('Owner 1 First Name', '')
    owner1_surname = row.get('Owner 1 Surname', '')
    assignee_surname = row.get('Assignee Surname Corrected', '')
    owner1_address1 = row.get('Owner 1 Policy Address 1', '')
    owner1_address2 = row.get('Owner 1 Policy Address 2', '')
    owner1_address3 = row.get('Owner 1 Policy Address 3', '')
    owner1_address4 = row.get('Owner 1 Policy Address 4', '')
    policy_no = str(row.get('Policy No', '')) if pd.notna(row.get('Policy No', '')) else ''
    policy_no_api = policy_no.replace('/', '.') if policy_no else ''
    print(f"[DEBUG] policy_no value = '{policy_no}' (type: {type(policy_no)})")
    print(f"[DEBUG] policy_no_api value = '{policy_no_api}' (type: {type(policy_no_api)})")
    frequency = row.get('Frequency', '')
    gross_premium = row.get('Computed Gross Premium', 0)
    no_installments = row.get('No of Instalments in Arrears', 0)
    arrears_amount = row.get('Arrears Amount', 0)
    agent_no = row.get('Agent No', '')
    
    # Extract additional columns for later use
    mobile_no = row.get('MOBILE_NO', '')
    nic = row.get('NIC', '')
    arrears_processing_date_raw = row.get('Arrears Processing Date', '')
    
    # Debug output for the extracted variables
    print(f"[DEBUG] Owner 1 First Name: '{owner1_first_name}'")
    print(f"[DEBUG] Owner 1 Surname: '{owner1_surname}'")
    print(f"[DEBUG] Mobile No: '{mobile_no}'")
    print(f"[DEBUG] NIC: '{nic}'")
    
    # Process arrears processing date
    if arrears_processing_date_raw and pd.notna(arrears_processing_date_raw):
        try:
            # Handle Excel serial date number (e.g., 45900.0901388889)
            if isinstance(arrears_processing_date_raw, (int, float)):
                # Convert Excel serial number to datetime
                date_obj = pd.to_datetime(arrears_processing_date_raw, origin='1899-12-30', unit='D')
                arrears_date_formatted = date_obj.strftime('%d-%B-%Y')  # "31-August-2025"
            else:
                # Handle string format "31/08/2025  02:09:48" (fallback)
                date_part = str(arrears_processing_date_raw).split()[0]
                date_obj = datetime.strptime(date_part, '%d/%m/%Y')
                arrears_date_formatted = date_obj.strftime('%d-%B-%Y')
        except:
            arrears_date_formatted = "29 August 2025"  # fallback
    else:
        arrears_date_formatted = "29 August 2025"  # fallback
    
    print(f"[DEBUG] Arrears Processing Date: '{arrears_processing_date_raw}' -> '{arrears_date_formatted}'")
    
    # Console log NIC value for each record
    print(f"[NIC] Record {index + 1}: NIC = '{nic}' (type: {type(nic)})")
    
    # Create full_name variable (first letter of first name + surname, max 24 chars)
    first_initial = ''
    if owner1_first_name and isinstance(owner1_first_name, str) and len(owner1_first_name) > 0 and owner1_first_name.lower() != 'nan':
        first_initial = owner1_first_name[0].upper()
    # Handle surname safely (check for NaN and non-string values)
    surname_part = ''
    if owner1_surname and isinstance(owner1_surname, str) and owner1_surname.lower() != 'nan':
        surname_part = owner1_surname.strip()
    
    # Combine and ensure max 24 characters
    if first_initial and surname_part:
        full_name_temp = f"{first_initial} {surname_part}"
        full_name = full_name_temp[:24] if len(full_name_temp) > 24 else full_name_temp
    elif surname_part:
        full_name = surname_part[:24] if len(surname_part) > 24 else surname_part
    else:
        full_name = ''
    
    print(f"[DEBUG] Full Name (max 24 chars): '{full_name}' (length: {len(full_name)})")
    
    # Validate required fields
    if pd.isna(policy_no) or str(policy_no).strip() == '':
        print(f"⚠️ Skipping row {index + 1}: Missing policy number")
        continue

    # Format values for use in the PDF
    name = f"{owner1_title} {owner1_first_name} {owner1_surname}"
    amount = float(arrears_amount) if pd.notna(arrears_amount) else 0.0
    no_installments = no_installments if pd.notna(no_installments) else 0
    gross_premium = float(gross_premium) if pd.notna(gross_premium) else 0.0

    # Sanitize name and policy number for safe filename creation using consistent method
    import sys
    sys.path.append('.')
    try:
        from filename_utils import sanitize_filename
        safe_name = sanitize_filename(name)
        safe_policy = sanitize_filename(str(policy_no))
    except ImportError:
        # Fallback to original method if filename_utils not available
        safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
        safe_policy = re.sub(r'[^\w\s-]', '_', str(policy_no)).strip()

    # Generate QR Code for payment
    try:
        payload = {
            "MerchantId": 151,
            "SetTransactionAmount": True,
            "TransactionAmount": str(amount),
            "SetConvenienceIndicatorTip": False,
            "ConvenienceIndicatorTip": 0,
            "SetConvenienceFeeFixed": False,
            "ConvenienceFeeFixed": 0,
            "SetConvenienceFeePercentage": False,
            "ConvenienceFeePercentage": 0,
            "SetAdditionalBillNumber": True,
            "AdditionalRequiredBillNumber": False,
            "AdditionalBillNumber": str(policy_no_api),
            "SetAdditionalMobileNo": True,
            "AdditionalRequiredMobileNo": False,
            "AdditionalMobileNo": str(mobile_no),
            "SetAdditionalStoreLabel": False,
            "AdditionalRequiredStoreLabel": False,
            "AdditionalStoreLabel": "",
            "SetAdditionalLoyaltyNumber": False,
            "AdditionalRequiredLoyaltyNumber": False,
            "AdditionalLoyaltyNumber": "",
            "SetAdditionalReferenceLabel": False,
            "AdditionalRequiredReferenceLabel": False,
            "AdditionalReferenceLabel": "",
            "SetAdditionalCustomerLabel": True,
            "AdditionalRequiredCustomerLabel": False,
            "AdditionalCustomerLabel": str(full_name),
            "SetAdditionalTerminalLabel": False,
            "AdditionalRequiredTerminalLabel": False,
            "AdditionalTerminalLabel": "",
            "SetAdditionalPurposeTransaction": True,
            "AdditionalRequiredPurposeTransaction": False,
            "AdditionalPurposeTransaction": str(nic)
        }
        
        response = requests.post(
            "https://api.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR",
            headers={"accept": "text/plain", "Content-Type": "application/json"},
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            qr_data = str(response.text).strip()
            if not qr_data or qr_data.lower() in ('null', 'none', 'nan'):
                print(f"⚠️ No valid QR data received for {name}")
                continue
                
            qr = segno.make(qr_data, error='L')
            qr_filename = f"qr_{safe_policy}.png"
            qr.save(qr_filename, scale=8, border=2, dark='#000000')
        else:
            print(f"❌ API request failed for {name}: {response.status_code} - {response.text}")
            continue

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error while generating QR for {name}: {str(e)}")
        continue
    except Exception as e:
        print(f"⚠️ Error generating QR for {name}: {str(e)}")
        continue

    # Create a PDF for the current policyholder
    pdf_filename = f"{output_folder}/{safe_policy}_{safe_name}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4
    margin = 50
    bottom_margin = 60  # Increased for pre-printed stationery address space
    y_pos = height - margin - 80

    # Store the top position of the date
    date_top_y = y_pos

    # Add current date
    current_date = datetime.now().strftime("%d-%B-%Y")
    date_para = Paragraph(f"{current_date}", styles['SalutationText'])
    date_para.wrapOn(c, width - margin, height)
    date_para.drawOn(c, margin, y_pos - date_para.height)
    y_pos -= date_para.height + 12

    # Add recipient address
    address_lines = [name]
    if pd.notna(owner1_address1):
        address_lines.append(str(owner1_address1))
    if pd.notna(owner1_address2):
        address_lines.append(str(owner1_address2))
    if pd.notna(owner1_address3):
        address_lines.append(str(owner1_address3))
    if pd.notna(owner1_address4):
        address_lines.append(str(owner1_address4))
    
    for line in address_lines:
        addr_para = Paragraph(line.upper(), styles['SalutationText'])
        addr_para.wrapOn(c, width - 2 * margin, height)
        addr_para.drawOn(c, margin, y_pos - addr_para.height)
        y_pos -= addr_para.height + 6
    y_pos -= 2

    # Add salutation
    salutation_text = f"Dear {owner1_title} {owner1_surname},"
    salutation = Paragraph(salutation_text, styles['BodyText'])
    salutation.wrapOn(c, width - 2 * margin, height)
    salutation.drawOn(c, margin, y_pos - salutation.height)
    y_pos -= salutation.height +8

    

    # Add subject line
    subject = Paragraph("RE: ARREARS ON YOUR LIFE INSURANCE POLICY", styles['BoldText'])
    subject.wrapOn(c, width - 2 * margin, height)
    subject.drawOn(c, margin, y_pos - subject.height)
    y_pos -= subject.height + 8

    # Add introductory paragraph
    intro_text = f"We write to inform you that, as of <font name='Cambria-Bold'>{arrears_date_formatted}</font>, an amount of <font name='Cambria-Bold'>MUR {amount:,.2f}</font> remains outstanding on your life insurance policy, as detailed below:"
    intro = Paragraph(intro_text, styles['BodyText'])
    intro.wrapOn(c, width - 2 * margin, height)
    intro.drawOn(c, margin, y_pos - intro.height)
    y_pos -= intro.height + 8

    # Create and draw policy details table
    table_headers = [
        Paragraph('Policy No.', styles['TableTextBold']),
        Paragraph('Payment Frequency', styles['TableTextBold']),
        Paragraph('Premium Amount (MUR)', styles['TableTextBold']),
        Paragraph('No. of Instalments in Arrears', styles['TableTextBold']),
        Paragraph('Total Premium Amount in Arrears (MUR)', styles['TableTextBold'])
    ]
    table_data = [
        [
            Paragraph(str(policy_no), styles['TableText']),
            Paragraph(str(frequency), styles['TableText']),
            Paragraph(f"{gross_premium:,.2f}", styles['TableText']),
            Paragraph(str(no_installments), styles['TableText']),
            Paragraph(f"{amount:,.2f}", styles['TableText'])
        ]
    ]
    data = [table_headers] + table_data
    table = Table(data, colWidths=[80, 70, 70, 90, 100])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Cambria'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TEXTWRAP', (0, 0), (-1, -1), 'CJK'),
    ]))
    table_width, table_height = table.wrap(width - 2 * margin, 0)
    table.drawOn(c, margin, y_pos - table_height)
    y_pos -= table_height + 12

    # Add body text
    text1 = "We kindly urge you to settle this outstanding amount as soon as possible to ensure that your insurance cover remains active and fully effective."
    para1 = Paragraph(text1, styles['BodyText'])
    para1.wrapOn(c, width - 2 * margin, height)
    para1.drawOn(c, margin, y_pos - para1.height)
    y_pos -= para1.height + 8

    text2 = "As your insurer, we wish to remind you of the following:"
    para2 = Paragraph(text2, styles['BodyText'])
    para2.wrapOn(c, width - 2 * margin, height)
    para2.drawOn(c, margin, y_pos - para2.height)
    y_pos -= para2.height + 6

    text3 = "1.	Your life insurance policy provides essential protection and financial security for you and your loved ones against unforeseen circumstances."
    para3 = Paragraph(text3, styles['BodyText'])
    para3.wrapOn(c, width - 2 * margin - 10, height)
    para3.drawOn(c, margin + 10, y_pos - para3.height)
    y_pos -= para3.height + 6

    text4 = "2.	Regular premium payments help your policy fund grow over time."
    para4 = Paragraph(text4, styles['BodyText'])
    para4.wrapOn(c, width - 2 * margin - 10, height)
    para4.drawOn(c, margin + 10, y_pos - para4.height)
    y_pos -= para4.height + 6

    text5 = "3.	Failure to settle outstanding arrears may impact the payment of future benefits and claims."
    para5 = Paragraph(text5, styles['BodyText'])
    para5.wrapOn(c, width - 2 * margin - 10, height)
    para5.drawOn(c, margin + 10, y_pos - para5.height)
    y_pos -= para5.height + 6

    text6 = "4.	If you are facing financial difficulties or would like to arrange a payment plan, please contact us on 602 3315 or email nicarlife@nicl.mu at your earliest convenience."
    para6 = Paragraph(text6, styles['BodyText'])
    para6.wrapOn(c, width - 2 * margin - 10, height)
    para6.drawOn(c, margin + 10, y_pos - para6.height)
    y_pos -= para6.height + 8

   

    text8 = "For your convenience, you may now settle payments via the QR code below using apps such as Juice or MyT Money."
    para8 = Paragraph(text8, styles['BoldText'])
    para8.wrapOn(c, width - 2 * margin, height)
    para8.drawOn(c, margin, y_pos - para8.height)
    y_pos -= para8.height + 15

    # Add professional QR code section with payment box (matching healthcare_renewal_final.py style)
    if os.path.exists(qr_filename):
        # Calculate center position and payment box dimensions
        page_center_x = width / 2
        payment_box_width = 170  # Professional box width
        payment_box_padding = 12  # Padding around content
        
        # Calculate the total height needed for the payment box
        payment_box_top = y_pos
        temp_y = y_pos - payment_box_padding
        
        # Calculate positions for all elements to determine box height (tighter spacing)
        if os.path.exists("maucas2.jpeg"):
            img = ImageReader("maucas2.jpeg")
            img_width = 110  # Standardized size
            img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            temp_y -= img_height + 2  # Reduced from 4 to 2
        elif os.path.exists("maucas.jpeg"):
            img = ImageReader("maucas.jpeg")
            img_width = 110  # Standardized size
            img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            temp_y -= img_height + 2  # Reduced from 4 to 2
        
        temp_y -= 100 + 2  # QR code size + reduced spacing (from 4 to 2)
        temp_y -= 12 + 2   # Text height + reduced spacing (from 4 to 2)
        
        if os.path.exists("zwennPay.jpg"):
            zwenn_img = ImageReader("zwennPay.jpg")
            zwenn_width = 80
            zwenn_height = zwenn_width * (zwenn_img.getSize()[1] / zwenn_img.getSize()[0])
            temp_y -= zwenn_height
        
        payment_box_bottom = temp_y - payment_box_padding
        payment_box_height = payment_box_top - payment_box_bottom
        
        # Draw the professional payment box border
        payment_box_x = page_center_x - (payment_box_width / 2)
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(1)
        c.rect(payment_box_x, payment_box_bottom, payment_box_width, payment_box_height, stroke=1, fill=0)
        
        # Reset y_pos and add padding
        y_pos = payment_box_top - payment_box_padding
        
        # Add maucas logo (centered, standardized size) - tighter spacing
        if os.path.exists("maucas2.jpeg"):
            img = ImageReader("maucas2.jpeg")
            img_width = 110  # Standardized for consistency
            img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            logo_x = page_center_x - (img_width / 2)
            c.drawImage(img, logo_x, y_pos - img_height, width=img_width, height=img_height)
            y_pos -= img_height + 2  # Reduced from 4 to 2
        elif os.path.exists("maucas.jpeg"):
            # Fallback to original maucas.jpeg if maucas2.jpeg not found
            img = ImageReader("maucas.jpeg")
            img_width = 110  # Standardized size
            img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            logo_x = page_center_x - (img_width / 2)
            c.drawImage(img, logo_x, y_pos - img_height, width=img_width, height=img_height)
            y_pos -= img_height + 2  # Reduced from 4 to 2
        else:
            print(f"⚠️ Warning: maucas logo files not found - skipping Maucas logo")
        
        # Add QR code (centered, optimized size for scanning) - tighter spacing
        qr_size = 100  # Optimal size for scanning
        qr_x = page_center_x - (qr_size / 2)
        c.drawImage(qr_filename, qr_x, y_pos - qr_size, width=qr_size, height=qr_size)
        y_pos -= qr_size + 2  # Reduced from 4 to 2
        
        # Add "NIC Life Insurance" text below QR code (centered) - tighter spacing
        c.setFont("Cambria-Bold", 11)
        text_width = c.stringWidth("NIC Life Insurance", "Cambria-Bold", 11)
        text_x = page_center_x - (text_width / 2)
        c.drawString(text_x, y_pos - 8, "NIC Life Insurance")  # Reduced from 10 to 8
        y_pos -= 12  # Reduced from 14 to 12
        
        # Add ZwennPay logo below the text (centered)
        if os.path.exists("zwennPay.jpg"):
            zwenn_img = ImageReader("zwennPay.jpg")
            zwenn_width = 80
            zwenn_height = zwenn_width * (zwenn_img.getSize()[1] / zwenn_img.getSize()[0])
            zwenn_x = page_center_x - (zwenn_width / 2)
            c.drawImage(zwenn_img, zwenn_x, y_pos - zwenn_height, width=zwenn_width, height=zwenn_height)
            y_pos = payment_box_bottom - 15  # Position after the box
        else:
            print(f"⚠️ Warning: zwennPay.jpg not found - skipping ZwennPay logo")
            y_pos = payment_box_bottom - 15
    else:
        print(f"⚠️ Warning: QR code file not found - skipping QR section")
        y_pos -= 20

    # Add footer text with proper spacing - ensure it's below QR box
    # Calculate safe position below QR box - reduced gap
    footer_start_y = y_pos - 10  # Reduced from 20px to 10px below QR box
    
    footer1 = Paragraph(
        "If you have already cleared this amount, kindly disregard this letter.",
        styles['BodyText']
    )
    footer1.wrapOn(c, width - 2 * margin, height)
    footer1.drawOn(c, margin, footer_start_y - footer1.height)

    # Add agent number with reduced spacing
    agent_y_pos = footer_start_y - footer1.height - 5  # Further reduced spacing from 8 to 5
    if pd.notna(assignee_surname) and str(assignee_surname).strip() not in ['', 'nan', 'NaN']:
        agent_text = Paragraph(f"{assignee_surname}", styles['BodyText'])
        agent_text.wrapOn(c, width - 2 * margin, height)
        agent_text.drawOn(c, margin, agent_y_pos - agent_text.height)
        agent_y_pos -= agent_text.height + 8  # Space for disclaimer below
    else:
        agent_y_pos -= 8

    # Add disclaimer text below Cc line (proper order)
    disclaimer_y_pos = agent_y_pos - 8  # Position below Cc line
    footer2 = Paragraph(
        "This is a computer-generated letter and does not require any signature.",
        styles['disclaimerText']
    )
    footer2.wrapOn(c, width - 2 * margin, height)
    footer2.drawOn(c, margin, disclaimer_y_pos - footer2.height)

    # Save the PDF
    c.save()

    # Add password protection using customer's NIC
    try:
        if nic and str(nic).strip():
            password = str(nic).strip()
            
            # Create password-protected version
            temp_filename = pdf_filename.replace('.pdf', '_temp.pdf')
            os.rename(pdf_filename, temp_filename)
            
            # Read the unprotected PDF
            with open(temp_filename, 'rb') as input_file:
                reader = PdfFileReader(input_file)
                writer = PdfFileWriter()
                
                # Copy all pages
                for page_num in range(reader.getNumPages()):
                    writer.addPage(reader.getPage(page_num))
                
                # Encrypt with NIC as password
                writer.encrypt(password)
                
                # Write password-protected PDF
                with open(pdf_filename, 'wb') as output_file:
                    writer.write(output_file)
            
            # Remove temporary file
            os.remove(temp_filename)
            print(f"🔒 PDF password-protected with NIC: {password}")
        else:
            print(f"⚠️ No NIC found for {name}, PDF saved without password protection")
    except Exception as e:
        print(f"⚠️ Failed to add password protection: {str(e)}")
        # If password protection fails, ensure we still have the original PDF
        temp_filename = pdf_filename.replace('.pdf', '_temp.pdf')
        if os.path.exists(temp_filename):
            os.rename(temp_filename, pdf_filename)

    # Clean up QR code file
    if os.path.exists(qr_filename):
        os.remove(qr_filename)

    print(f"✅ PDF generated successfully for {name}")

print(f"🎉 Script completed. Processed {len(df)} rows total.")